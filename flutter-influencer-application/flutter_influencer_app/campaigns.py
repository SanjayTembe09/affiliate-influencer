from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from database import get_db
from middleware.auth import verify_token

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"])


class CampaignCreateSchema(BaseModel):
    title: str
    description: str
    product_url: str
    payout_per_post: float
    required_hashtag: str
    category: str


@router.get("/")
def get_campaigns(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    user=Depends(verify_token),
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        offset = (page - 1) * limit

        # ---------------------------------------------------------
        # BRAND
        # ---------------------------------------------------------
        if user['role'] == 'brand':
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM campaigns
                WHERE brand_id = %s
                """,
                (user['id'],)
            )

            total = cursor.fetchone()['total']

            cursor.execute(
                """
                SELECT *
                FROM campaigns
                WHERE brand_id = %s
                ORDER BY id DESC
                LIMIT %s OFFSET %s
                """,
                (user['id'], limit, offset)
            )

        # ---------------------------------------------------------
        # CREATOR / OTHER ROLES
        # ---------------------------------------------------------
        else:
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM campaigns c
                INNER JOIN affiliate_programs ap
                    ON ap.brand_id = c.brand_id
                INNER JOIN affiliate_program_members apm
                    ON apm.program_id = ap.id
                WHERE c.status = 'active'
                  AND c.promotion_status = 'published'
                  AND ap.status = 'active'
                  AND apm.creator_id = %s
                  AND apm.status = 'active'
                """,
                (user['id'],)
            )

            total = cursor.fetchone()['total']

            cursor.execute(
                """
                SELECT DISTINCT c.*
                FROM campaigns c
                INNER JOIN affiliate_programs ap
                    ON ap.brand_id = c.brand_id
                INNER JOIN affiliate_program_members apm
                    ON apm.program_id = ap.id
                WHERE c.status = 'active'
                  AND c.promotion_status = 'published'
                  AND ap.status = 'active'
                  AND apm.creator_id = %s
                  AND apm.status = 'active'
                ORDER BY c.id DESC
                LIMIT %s OFFSET %s
                """,
                (user['id'], limit, offset)
            )

        rows = cursor.fetchall()

        return {
            "items": rows,
            "page": page,
            "limit": limit,
            "total": total,
            "has_more": offset + len(rows) < total,
        }

    except Exception as err:
        print(f"ERROR [GET /api/campaigns/]: {str(err)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch campaigns"
        )

    finally:
        cursor.close()
        conn.close()

@router.post("/")
def create_campaign(
    campaign: CampaignCreateSchema,
    user=Depends(verify_token)
):
    if user['role'] != 'brand':
        raise HTTPException(
            status_code=403,
            detail="Unauthorized: Only brands can create campaigns"
        )

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
          INSERT INTO campaigns
          (
            brand_id,
            title,
            description,
            product_url,
            payout_per_post,
            required_hashtag,
            category,
            status
          )
          VALUES (%s, %s, %s, %s, %s, %s, %s, 'active')
        """

        values = (
            user['id'],
            campaign.title,
            campaign.description,
            campaign.product_url,
            campaign.payout_per_post,
            campaign.required_hashtag,
            campaign.category
        )

        cursor.execute(query, values)
        conn.commit()

        return {
            "id": cursor.lastrowid,
            "message": "Campaign created successfully"
        }

    except Exception as err:
        raise HTTPException(
            status_code=500,
            detail="Failed to create campaign"
        )

    finally:
        cursor.close()
        conn.close()

class PromotionStatusUpdateSchema(BaseModel):
    promotion_status: str


@router.patch("/{campaign_id}/promotion-status")
def update_campaign_promotion_status(
    campaign_id: int,
    data: PromotionStatusUpdateSchema,
    user=Depends(verify_token)
):
    if user['role'] != 'brand':
        raise HTTPException(
            status_code=403,
            detail="Unauthorized: Only brands can change campaign promotion status"
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
            SELECT id, brand_id, promotion_status
            FROM campaigns
            WHERE id = %s
            """,
            (campaign_id,)
        )

        campaign = cursor.fetchone()

        if not campaign:
            raise HTTPException(
                status_code=404,
                detail="Campaign not found."
            )

        if campaign['brand_id'] != user['id']:
            raise HTTPException(
                status_code=403,
                detail="You can only change campaigns belonging to your brand."
            )

        cursor.execute(
            """
            UPDATE campaigns
            SET promotion_status = %s
            WHERE id = %s
              AND brand_id = %s
            """,
            (
                data.promotion_status,
                campaign_id,
                user['id']
            )
        )

        conn.commit()

        return {
            "success": True,
            "id": campaign_id,
            "promotion_status": data.promotion_status,
            "message": "Campaign promotion status updated successfully."
        }

    except HTTPException:
        raise

    except Exception as err:
        conn.rollback()
        print(
            f"ERROR [PATCH /api/campaigns/{campaign_id}/promotion-status]: "
            f"{str(err)}"
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to update campaign promotion status."
        )

    finally:
        cursor.close()
        conn.close()        
