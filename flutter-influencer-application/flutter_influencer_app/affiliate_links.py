from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database import get_db
from middleware.auth import verify_token
import secrets


router = APIRouter(
    prefix="/api/v1/affiliate-links",
    tags=["Affiliate Links"]
)


# ============================================================
# Request model
# ============================================================

class AffiliateLinkCreate(BaseModel):
    offer_id: int


# ============================================================
# POST /api/v1/affiliate-links
# Create an affiliate link for the authenticated creator
# ============================================================

@router.post("")
def create_affiliate_link(
    data: AffiliateLinkCreate,
    current_user: dict = Depends(verify_token)
):
    """
    Create a unique affiliate tracking link for the authenticated
    creator.

    Requirements:
    - Creator role
    - Active affiliate offer
    - Active affiliate program
    - Active creator membership for that program
    - Active affiliate account for that membership
    """

    # ---------------------------------------------------------
    # Creator-only access
    # ---------------------------------------------------------

    if current_user.get("role") != "creator":
        raise HTTPException(
            status_code=403,
            detail="Only creators can generate affiliate links"
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
        # Find active offer + active program
        # -----------------------------------------------------

        cursor.execute(
            """
            SELECT
                ao.id AS offer_id,
                ao.program_id,
                ao.title,
                ao.destination_url,
                ao.status AS offer_status,
                ap.brand_name,
                ap.program_name,
                ap.status AS program_status
            FROM affiliate_offers ao
            INNER JOIN affiliate_programs ap
                ON ap.id = ao.program_id
            WHERE ao.id = %s
              AND ao.status = 'active'
              AND ap.status = 'active'
            """,
            (data.offer_id,)
        )

        offer = cursor.fetchone()

        if not offer:
            raise HTTPException(
                status_code=404,
                detail="Affiliate offer not found or is inactive."
            )

        # -----------------------------------------------------
        # Find creator membership
        # -----------------------------------------------------

        cursor.execute(
            """
            SELECT
                apm.id AS membership_id,
                apm.status AS membership_status
            FROM affiliate_program_members apm
            WHERE apm.creator_id = %s
              AND apm.program_id = %s
            """,
            (
                creator_id,
                offer["program_id"]
            )
        )

        membership = cursor.fetchone()

        if not membership:
            raise HTTPException(
                status_code=409,
                detail=(
                    "You must join this affiliate program "
                    "before generating an affiliate link."
                )
            )

        if membership["membership_status"] != "active":
            raise HTTPException(
                status_code=409,
                detail=(
                    "Your affiliate program membership must be "
                    "active before generating an affiliate link."
                )
            )

        # -----------------------------------------------------
        # Find active affiliate account
        # -----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id AS account_id,
                network_name,
                external_account_id,
                status AS account_status
            FROM affiliate_accounts
            WHERE membership_id = %s
              AND status = 'active'
            """,
            (membership["membership_id"],)
        )

        account = cursor.fetchone()

        if not account:
            raise HTTPException(
                status_code=409,
                detail=(
                    "An active affiliate account is required "
                    "before generating an affiliate link."
                )
            )

        # -----------------------------------------------------
        # Generate unique tracking code
        # -----------------------------------------------------

        tracking_code = None

        for _ in range(10):
            candidate = "RMW-" + secrets.token_urlsafe(8)

            cursor.execute(
                """
                SELECT id
                FROM affiliate_links
                WHERE tracking_code = %s
                """,
                (candidate,)
            )

            existing = cursor.fetchone()

            if not existing:
                tracking_code = candidate
                break

        if not tracking_code:
            raise HTTPException(
                status_code=500,
                detail="Unable to generate a unique tracking code."
            )

        # -----------------------------------------------------
        # Create affiliate link
        # -----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO affiliate_links
            (
                creator_id,
                offer_id,
                tracking_code,
                destination_url,
                status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                'active'
            )
            """,
            (
                creator_id,
                offer["offer_id"],
                tracking_code,
                offer["destination_url"]
            )
        )

        conn.commit()

        link_id = cursor.lastrowid

        # -----------------------------------------------------
        # Build public redirect URL
        # -----------------------------------------------------

        affiliate_url = (
            "https://affiliate-api.flexhappyhours.com"
            f"/affiliate/r/{tracking_code}"
        )

        return {
            "success": True,
            "message": "Affiliate link created.",
            "link": {
                "id": link_id,
                "creator_id": creator_id,
                "offer_id": offer["offer_id"],
                "program_id": offer["program_id"],
                "brand_name": offer["brand_name"],
                "program_name": offer["program_name"],
                "title": offer["title"],
                "tracking_code": tracking_code,
                "affiliate_url": affiliate_url,
                "destination_url": offer["destination_url"],
                "status": "active",
                "affiliate_account_id": account["account_id"],
                "network_name": account["network_name"]
            }
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as err:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create affiliate link."
        )

    finally:
        cursor.close()
        conn.close()