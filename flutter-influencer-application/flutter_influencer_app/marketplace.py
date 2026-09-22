from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from database import get_db
from middleware.auth import verify_token

router = APIRouter(
    prefix="/api/marketplace",
    tags=["Marketplace"]
)


class ProductCreateSchema(BaseModel):
    title: str
    description: str
    product_url: str
    image_url: str = None
    price: float
    commission_percentage: float


@router.get("/")
def get_marketplace_products(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    user=Depends(verify_token),
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        offset = (page - 1) * limit

        # --------------------------------------------------------
        # BRAND
        # --------------------------------------------------------
        # Brands continue to see their own active products.
        # No affiliate eligibility logic is applied to brands.
        # --------------------------------------------------------

        if user['role'] == 'brand':

            where_clause = """
                WHERE mp.status = 'active'
                  AND mp.brand_id = %s
            """

            filter_params = (user['id'],)

            count_sql = f"""
                SELECT COUNT(*) AS total
                FROM marketplace_products mp
                {where_clause}
            """

            products_sql = f"""
                SELECT mp.*
                FROM marketplace_products mp
                {where_clause}
                ORDER BY mp.created_at DESC
                LIMIT %s OFFSET %s
            """

        # --------------------------------------------------------
        # CREATOR
        # --------------------------------------------------------
        # A creator sees only:
        #
        # 1. Active marketplace products
        # 2. Published products
        # 3. Products whose brand has an active affiliate program
        # 4. Creator has an active membership in that program
        #
        # Additional A9.3 metadata is returned:
        #
        # - affiliate_program_id
        # - affiliate_program_name
        # - affiliate_program_brand_name
        # - creator_membership_status
        # - affiliate_offer_id
        # - can_generate_affiliate_link
        #
        # IMPORTANT:
        # We do NOT create an affiliate link here.
        # Link generation remains handled by /affiliate-links.
        # --------------------------------------------------------

        else:

            where_clause = """
                WHERE mp.status = 'active'
                  AND mp.promotion_status = 'published'
                  AND ap.status = 'active'
                  AND apm.creator_id = %s
                  AND apm.status = 'active'
            """

            filter_params = (user['id'],)

            count_sql = f"""
                SELECT COUNT(DISTINCT mp.id) AS total
                FROM marketplace_products mp

                INNER JOIN affiliate_programs ap
                    ON ap.brand_id = mp.brand_id

                INNER JOIN affiliate_program_members apm
                    ON apm.program_id = ap.id

                {where_clause}
            """

            products_sql = f"""
                SELECT DISTINCT
                    mp.*,

                    ap.id AS affiliate_program_id,

                    ap.program_name AS affiliate_program_name,

                    ap.brand_name AS affiliate_program_brand_name,

                    apm.status AS creator_membership_status,

                    (
                        SELECT ao.id
                        FROM affiliate_offers ao
                        WHERE ao.program_id = ap.id
                          AND ao.status = 'active'
                        ORDER BY ao.id ASC
                        LIMIT 1
                    ) AS affiliate_offer_id,

                    CASE
                        WHEN EXISTS (
                            SELECT 1
                            FROM affiliate_offers ao
                            WHERE ao.program_id = ap.id
                              AND ao.status = 'active'
                        )
                        THEN TRUE
                        ELSE FALSE
                    END AS can_generate_affiliate_link

                FROM marketplace_products mp

                INNER JOIN affiliate_programs ap
                    ON ap.brand_id = mp.brand_id
                   AND ap.status = 'active'

                INNER JOIN affiliate_program_members apm
                    ON apm.program_id = ap.id
                   AND apm.creator_id = %s
                   AND apm.status = 'active'

                {where_clause}

                ORDER BY mp.created_at DESC
                LIMIT %s OFFSET %s
            """

        # --------------------------------------------------------
        # TOTAL PRODUCT COUNT
        # --------------------------------------------------------

        cursor.execute(
            count_sql,
            filter_params
        )

        count_row = cursor.fetchone()

        total = int(count_row['total']) if count_row else 0

        # --------------------------------------------------------
        # TOTAL PAGES
        # --------------------------------------------------------

        total_pages = (
            (total + limit - 1) // limit
            if total > 0
            else 0
        )

        # --------------------------------------------------------
        # FETCH CURRENT PAGE
        # --------------------------------------------------------

        if user['role'] == 'brand':
            query_params = filter_params + (limit, offset)
        else:
            query_params = (
                user['id'],
                user['id'],
                limit,
                offset
            )

        cursor.execute(
            products_sql,
            query_params
        )

        rows = cursor.fetchall()

        print(
            f"DEBUG [GET /api/marketplace/]: "
            f"role={user['role']}, "
            f"user_id={user['id']}, "
            f"page={page}, "
            f"limit={limit}, "
            f"found={len(rows)}, "
            f"total={total}"
        )

        return {
            "products": rows,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
        }

    except Exception as err:
        print(
            f"ERROR [GET /api/marketplace/]: {str(err)}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(err),
        )

    finally:
        cursor.close()
        conn.close()


@router.post("/")
def add_marketplace_product(
    product: ProductCreateSchema,
    user=Depends(verify_token)
):
    if user['role'] != 'brand':
        raise HTTPException(
            status_code=403,
            detail="Access denied: Only brands can add products."
        )

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            INSERT INTO marketplace_products
            (
                brand_id,
                title,
                description,
                product_url,
                image_url,
                price,
                commission_percentage,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'active')
            """,
            (
                user['id'],
                product.title,
                product.description,
                product.product_url,
                product.image_url,
                product.price,
                product.commission_percentage
            )
        )

        conn.commit()

        return {
            "id": cursor.lastrowid,
            "success": True,
            "message": "Affiliate product added to marketplace successfully!"
        }

    except Exception as err:
        raise HTTPException(
            status_code=500,
            detail=f"Database rejection: {str(err)}"
        )

    finally:
        cursor.close()
        conn.close()


class PromotionStatusUpdateSchema(BaseModel):
    promotion_status: str


@router.patch("/{product_id}/promotion-status")
def update_product_promotion_status(
    product_id: int,
    data: PromotionStatusUpdateSchema,
    user=Depends(verify_token)
):
    if user['role'] != 'brand':
        raise HTTPException(
            status_code=403,
            detail="Access denied: Only brands can change product promotion status."
        )

    allowed_statuses = {
        'test',
        'draft',
        'published',
        'inactive'
    }

    if data.promotion_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid promotion status."
        )

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                id,
                brand_id,
                promotion_status
            FROM marketplace_products
            WHERE id = %s
            """,
            (product_id,)
        )

        product = cursor.fetchone()

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Product not found."
            )

        if product['brand_id'] != user['id']:
            raise HTTPException(
                status_code=403,
                detail="You can only change products belonging to your brand."
            )

        cursor.execute(
            """
            UPDATE marketplace_products
            SET promotion_status = %s
            WHERE id = %s
              AND brand_id = %s
            """,
            (
                data.promotion_status,
                product_id,
                user['id']
            )
        )

        conn.commit()

        return {
            "success": True,
            "id": product_id,
            "promotion_status": data.promotion_status,
            "message": "Product promotion status updated successfully."
        }

    except HTTPException:
        raise

    except Exception as err:
        conn.rollback()

        print(
            f"ERROR [PATCH /api/marketplace/{product_id}/promotion-status]: "
            f"{str(err)}"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to update product promotion status."
        )

    finally:
        cursor.close()
        conn.close()