from fastapi import APIRouter, HTTPException, Depends
from database import get_db
from middleware.auth import verify_token


router = APIRouter(
    prefix="/api/v1/affiliate-offers",
    tags=["Affiliate Offers"]
)


# ============================================================
# GET /api/v1/affiliate-offers
# Creator-facing active affiliate offers
# ============================================================

@router.get("")
def get_affiliate_offers(
    search: str = None,
    category: str = None,
    country: str = None,
    page: int = 1,
    limit: int = 20,
    current_user: dict = Depends(verify_token)
):
    """
    Return active affiliate offers available to the
    authenticated creator.

    Offers are joined with their affiliate program so the
    creator receives the program and commission information
    needed to evaluate the offer.
    """

    # ---------------------------------------------------------
    # Creator-only access
    # ---------------------------------------------------------

    if current_user.get("role") != "creator":
        raise HTTPException(
            status_code=403,
            detail="Only creators can access affiliate offers"
        )

    creator_id = current_user.get("id")

    if not creator_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid authenticated user"
        )

    # ---------------------------------------------------------
    # Pagination validation
    # ---------------------------------------------------------

    if page < 1:
        page = 1

    if limit < 1:
        limit = 20

    if limit > 100:
        limit = 100

    offset = (page - 1) * limit

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        # -----------------------------------------------------
        # Build filters
        # -----------------------------------------------------

        conditions = [
            "ao.status = 'active'",
            "ap.status = 'active'"
        ]

        params = []

        if search:
            conditions.append("""
                (
                    ao.brand_name LIKE %s
                    OR ao.title LIKE %s
                    OR ao.description LIKE %s
                    OR ap.brand_name LIKE %s
                    OR ap.program_name LIKE %s
                )
            """)

            search_value = f"%{search}%"

            params.extend([
                search_value,
                search_value,
                search_value,
                search_value,
                search_value
            ])

        if category:
            conditions.append("ap.category = %s")
            params.append(category)

        if country:
            conditions.append("ap.country_market LIKE %s")
            params.append(f"%{country}%")

        where_clause = " AND ".join(conditions)

        # -----------------------------------------------------
        # Count total offers
        # -----------------------------------------------------

        count_query = f"""
            SELECT COUNT(*) AS total
            FROM affiliate_offers ao

            INNER JOIN affiliate_programs ap
                ON ap.id = ao.program_id

            WHERE {where_clause}
        """

        cursor.execute(
            count_query,
            tuple(params)
        )

        total = cursor.fetchone()["total"]

        # -----------------------------------------------------
        # Retrieve offers
        # -----------------------------------------------------

        query = f"""
            SELECT
                ao.id AS offer_id,
                ao.program_id,

                ao.brand_name,
                ao.title,
                ao.description,
                ao.image_url,
                ao.destination_url,

                ao.commission_type,
                ao.commission_rate,
                ao.currency,

                ao.external_offer_id,
                ao.status,

                ap.brand_name AS program_brand_name,
                ap.category,
                ap.country_market,
                ap.program_name,
                ap.cookie_duration,
                ap.affiliate_network,
                ap.creator_eligible,
                ap.official_program_url,
                ap.application_url,

                apm.id AS membership_id,
                apm.status AS membership_status,

                aa.id AS affiliate_account_id,
                aa.status AS affiliate_account_status,
                aa.network_name,
                aa.external_account_id

            FROM affiliate_offers ao

            INNER JOIN affiliate_programs ap
                ON ap.id = ao.program_id

            LEFT JOIN affiliate_program_members apm
                ON apm.program_id = ao.program_id
               AND apm.creator_id = %s

            LEFT JOIN affiliate_accounts aa
                ON aa.membership_id = apm.id

            WHERE {where_clause}

            ORDER BY ao.created_at DESC

            LIMIT %s OFFSET %s
        """

        query_params = [creator_id] + params + [
            limit,
            offset
        ]

        cursor.execute(
            query,
            tuple(query_params)
        )

        offers = cursor.fetchall()

        # -----------------------------------------------------
        # Add creator-specific availability information
        # -----------------------------------------------------

        for offer in offers:

            membership_status = offer.get("membership_status")
            account_status = offer.get("affiliate_account_status")

            offer["creator_membership_status"] = membership_status
            offer["creator_account_status"] = account_status

            if membership_status == "active" and account_status == "active":
                offer["can_generate_link"] = True
            else:
                offer["can_generate_link"] = False

        return {
            "success": True,
            "count": len(offers),
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
            "offers": offers
        }

    except HTTPException:
        raise

    except Exception as err:
        print(
            f"ERROR [GET /api/v1/affiliate-offers]: {err}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve affiliate offers"
        )

    finally:
        cursor.close()
        conn.close()

# ============================================================
# GET /api/v1/affiliate-offers/{offer_id}
# Creator-facing affiliate offer detail
# ============================================================

@router.get("/{offer_id}")
def get_affiliate_offer_detail(
    offer_id: int,
    current_user: dict = Depends(verify_token)
):
    """
    Return one active affiliate offer with its affiliate
    program information and creator-specific membership
    and account status.
    """

    # ---------------------------------------------------------
    # Creator-only access
    # ---------------------------------------------------------

    if current_user.get("role") != "creator":
        raise HTTPException(
            status_code=403,
            detail="Only creators can access affiliate offers"
        )

    creator_id = current_user.get("id")

    if not creator_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid authenticated user"
        )

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        # -----------------------------------------------------
        # Retrieve offer
        # -----------------------------------------------------

        query = """
            SELECT
                ao.id AS offer_id,
                ao.program_id,

                ao.brand_name,
                ao.title,
                ao.description,
                ao.image_url,
                ao.destination_url,

                ao.commission_type,
                ao.commission_rate,
                ao.currency,

                ao.external_offer_id,
                ao.status,

                ap.brand_name AS program_brand_name,
                ap.category,
                ap.country_market,
                ap.program_name,
                ap.cookie_duration,
                ap.affiliate_network,
                ap.creator_eligible,
                ap.official_program_url,
                ap.application_url,

                apm.id AS membership_id,
                apm.status AS membership_status,

                aa.id AS affiliate_account_id,
                aa.status AS affiliate_account_status,
                aa.network_name,
                aa.external_account_id

            FROM affiliate_offers ao

            INNER JOIN affiliate_programs ap
                ON ap.id = ao.program_id

            LEFT JOIN affiliate_program_members apm
                ON apm.program_id = ao.program_id
               AND apm.creator_id = %s

            LEFT JOIN affiliate_accounts aa
                ON aa.membership_id = apm.id

            WHERE ao.id = %s
              AND ao.status = 'active'
              AND ap.status = 'active'

            LIMIT 1
        """

        cursor.execute(
            query,
            (creator_id, offer_id)
        )

        offer = cursor.fetchone()

        # -----------------------------------------------------
        # Offer not found
        # -----------------------------------------------------

        if not offer:
            raise HTTPException(
                status_code=404,
                detail="Affiliate offer not found"
            )

        # -----------------------------------------------------
        # Add creator-specific availability information
        # -----------------------------------------------------

        membership_status = offer.get("membership_status")
        account_status = offer.get("affiliate_account_status")

        offer["creator_membership_status"] = membership_status
        offer["creator_account_status"] = account_status

        if (
            membership_status == "active"
            and account_status == "active"
        ):
            offer["can_generate_link"] = True
        else:
            offer["can_generate_link"] = False

        return {
            "success": True,
            "offer": offer
        }

    except HTTPException:
        raise

    except Exception as err:
        print(
            f"ERROR [GET /api/v1/affiliate-offers/{{offer_id}}]: {err}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve affiliate offer"
        )

    finally:
        cursor.close()
        conn.close()        
