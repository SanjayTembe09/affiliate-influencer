from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database import get_db
from middleware.auth import verify_token


router = APIRouter(
    prefix="/api/v1/affiliate-programs",
    tags=["Affiliate Programs"]
)


# ============================================================
# Request schema
# ============================================================

class AffiliateMembershipUpdate(BaseModel):
    external_publisher_id: str = None
    notes: str = None


# ============================================================
# GET /api/v1/affiliate-programs
# Existing public affiliate-program directory
# ============================================================

@router.get("")
def get_affiliate_programs(
    search: str = None,
    category: str = None,
    country: str = None,
    creator_eligible: str = None,
    page: int = 1,
    limit: int = 20
):
    """
    Return active affiliate programs with search,
    filtering and pagination.
    """

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
        conditions = ["status = 'active'"]
        params = []

        if search:
            conditions.append("""
                (
                    brand_name LIKE %s
                    OR program_name LIKE %s
                    OR category LIKE %s
                )
            """)

            search_value = f"%{search}%"

            params.extend([
                search_value,
                search_value,
                search_value
            ])

        if category:
            conditions.append("category = %s")
            params.append(category)

        if country:
            conditions.append("country_market LIKE %s")
            params.append(f"%{country}%")

        if creator_eligible:
            conditions.append("creator_eligible = %s")
            params.append(creator_eligible)

        where_clause = " AND ".join(conditions)

        count_query = f"""
            SELECT COUNT(*) AS total
            FROM affiliate_programs
            WHERE {where_clause}
        """

        cursor.execute(count_query, tuple(params))
        total = cursor.fetchone()["total"]

        query = f"""
            SELECT
                id,
                brand_name,
                category,
                country_market,
                program_name,
                commission_type,
                commission_rate,
                cookie_duration,
                affiliate_network,
                creator_eligible,
                official_program_url,
                application_url,
                verification_notes,
                last_verified_at,
                status
            FROM affiliate_programs
            WHERE {where_clause}
            ORDER BY brand_name ASC
            LIMIT %s OFFSET %s
        """

        query_params = params + [limit, offset]

        cursor.execute(query, tuple(query_params))
        programs = cursor.fetchall()

        return {
            "success": True,
            "count": len(programs),
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
            "programs": programs
        }

    except Exception as err:
        print(f"ERROR [/api/v1/affiliate-programs]: {err}")

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve affiliate programs"
        )

    finally:
        cursor.close()
        conn.close()


# ============================================================
# POST /api/v1/affiliate-programs/{program_id}/join
# Creator joins an affiliate program
# ============================================================

@router.post("/{program_id}/join")
def join_affiliate_program(
    program_id: int,
    current_user: dict = Depends(verify_token)
):
    """
    Create an affiliate-program membership for the
    authenticated creator.

    New memberships always start as 'pending'.
    """

    if current_user.get("role") != "creator":
        raise HTTPException(
            status_code=403,
            detail="Only creators can join affiliate programs"
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
        # Verify that the affiliate program exists and is active
        # -----------------------------------------------------

        cursor.execute("""
            SELECT
                id,
                brand_name,
                program_name,
                status
            FROM affiliate_programs
            WHERE id = %s
              AND status = 'active'
        """, (program_id,))

        program = cursor.fetchone()

        if not program:
            raise HTTPException(
                status_code=404,
                detail="Affiliate program not found or inactive"
            )

        # -----------------------------------------------------
        # Check whether creator already joined this program
        # -----------------------------------------------------

        cursor.execute("""
            SELECT
                id,
                status,
                external_publisher_id,
                joined_at,
                approved_at
            FROM affiliate_program_members
            WHERE creator_id = %s
              AND program_id = %s
        """, (creator_id, program_id))

        existing_membership = cursor.fetchone()

        if existing_membership:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "You have already joined this affiliate program",
                    "membership": existing_membership
                }
            )

        # -----------------------------------------------------
        # Create membership
        # -----------------------------------------------------

        cursor.execute("""
            INSERT INTO affiliate_program_members (
                creator_id,
                program_id,
                status,
                joined_at
            )
            VALUES (
                %s,
                %s,
                'pending',
                NOW()
            )
        """, (
            creator_id,
            program_id
        ))

        membership_id = cursor.lastrowid

        conn.commit()

        return {
            "success": True,
            "message": "Affiliate program application submitted",
            "membership": {
                "id": membership_id,
                "creator_id": creator_id,
                "program_id": program_id,
                "brand_name": program["brand_name"],
                "program_name": program["program_name"],
                "status": "pending",
                "joined_at": None
            }
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as err:
        conn.rollback()

        print(
            f"ERROR [POST /api/v1/affiliate-programs/"
            f"{program_id}/join]: {err}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to join affiliate program"
        )

    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/v1/affiliate-programs/my
# Creator's affiliate-program memberships
# ============================================================

@router.get("/my")
def get_my_affiliate_programs(
    current_user: dict = Depends(verify_token)
):
    """
    Return affiliate programs joined by the authenticated creator.
    """

    if current_user.get("role") != "creator":
        raise HTTPException(
            status_code=403,
            detail="Only creators can access affiliate memberships"
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
        cursor.execute("""
            SELECT
                apm.id AS membership_id,
                apm.program_id,
                apm.status AS membership_status,
                apm.external_publisher_id,
                apm.joined_at,
                apm.approved_at,
                apm.notes,

                ap.brand_name,
                ap.category,
                ap.country_market,
                ap.program_name,
                ap.commission_type,
                ap.commission_rate,
                ap.cookie_duration,
                ap.affiliate_network,
                ap.creator_eligible,
                ap.official_program_url,
                ap.application_url

            FROM affiliate_program_members apm

            INNER JOIN affiliate_programs ap
                ON ap.id = apm.program_id

            WHERE apm.creator_id = %s

            ORDER BY apm.created_at DESC
        """, (creator_id,))

        memberships = cursor.fetchall()

        return {
            "success": True,
            "count": len(memberships),
            "programs": memberships
        }

    except Exception as err:
        print(
            f"ERROR [GET /api/v1/affiliate-programs/my]: {err}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve your affiliate programs"
        )

    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/v1/affiliate-programs/my/{membership_id}
# Creator views one membership
# ============================================================

@router.get("/my/{membership_id}")
def get_my_affiliate_program(
    membership_id: int,
    current_user: dict = Depends(verify_token)
):
    """
    Return one affiliate-program membership belonging
    to the authenticated creator.
    """

    if current_user.get("role") != "creator":
        raise HTTPException(
            status_code=403,
            detail="Only creators can access affiliate memberships"
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
        cursor.execute("""
            SELECT
                apm.id AS membership_id,
                apm.program_id,
                apm.status AS membership_status,
                apm.external_publisher_id,
                apm.joined_at,
                apm.approved_at,
                apm.notes,

                ap.brand_name,
                ap.category,
                ap.country_market,
                ap.program_name,
                ap.commission_type,
                ap.commission_rate,
                ap.cookie_duration,
                ap.affiliate_network,
                ap.creator_eligible,
                ap.official_program_url,
                ap.application_url

            FROM affiliate_program_members apm

            INNER JOIN affiliate_programs ap
                ON ap.id = apm.program_id

            WHERE apm.id = %s
              AND apm.creator_id = %s
        """, (
            membership_id,
            creator_id
        ))

        membership = cursor.fetchone()

        if not membership:
            raise HTTPException(
                status_code=404,
                detail="Affiliate program membership not found"
            )

        return {
            "success": True,
            "membership": membership
        }

    except HTTPException:
        raise

    except Exception as err:
        print(
            f"ERROR [GET /api/v1/affiliate-programs/"
            f"my/{membership_id}]: {err}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve affiliate membership"
        )

    finally:
        cursor.close()
        conn.close()


# ============================================================
# PATCH /api/v1/affiliate-programs/my/{membership_id}
# Creator updates their membership information
# ============================================================

@router.patch("/my/{membership_id}")
def update_my_affiliate_program(
    membership_id: int,
    data: AffiliateMembershipUpdate,
    current_user: dict = Depends(verify_token)
):
    """
    Allow the authenticated creator to update information
    associated with their affiliate-program membership.

    Creator cannot change membership status.
    """

    if current_user.get("role") != "creator":
        raise HTTPException(
            status_code=403,
            detail="Only creators can update affiliate memberships"
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
        # Verify ownership
        # -----------------------------------------------------

        cursor.execute("""
            SELECT
                id,
                status
            FROM affiliate_program_members
            WHERE id = %s
              AND creator_id = %s
        """, (
            membership_id,
            creator_id
        ))

        membership = cursor.fetchone()

        if not membership:
            raise HTTPException(
                status_code=404,
                detail="Affiliate program membership not found"
            )

        # -----------------------------------------------------
        # Build update dynamically
        # -----------------------------------------------------

        updates = []
        params = []

        if data.external_publisher_id is not None:
            updates.append("external_publisher_id = %s")
            params.append(data.external_publisher_id.strip() or None)

        if data.notes is not None:
            updates.append("notes = %s")
            params.append(data.notes.strip() or None)

        if not updates:
            raise HTTPException(
                status_code=400,
                detail="No fields provided for update"
            )

        params.extend([
            membership_id,
            creator_id
        ])

        query = f"""
            UPDATE affiliate_program_members
            SET {", ".join(updates)}
            WHERE id = %s
              AND creator_id = %s
        """

        cursor.execute(query, tuple(params))

        conn.commit()

        # -----------------------------------------------------
        # Return updated membership
        # -----------------------------------------------------

        cursor.execute("""
            SELECT
                apm.id AS membership_id,
                apm.program_id,
                apm.status AS membership_status,
                apm.external_publisher_id,
                apm.joined_at,
                apm.approved_at,
                apm.notes,

                ap.brand_name,
                ap.program_name,
                ap.affiliate_network

            FROM affiliate_program_members apm

            INNER JOIN affiliate_programs ap
                ON ap.id = apm.program_id

            WHERE apm.id = %s
              AND apm.creator_id = %s
        """, (
            membership_id,
            creator_id
        ))

        updated_membership = cursor.fetchone()

        return {
            "success": True,
            "message": "Affiliate membership updated",
            "membership": updated_membership
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as err:
        conn.rollback()

        print(
            f"ERROR [PATCH /api/v1/affiliate-programs/"
            f"my/{membership_id}]: {err}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to update affiliate membership"
        )

    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/v1/affiliate-programs/{program_id}
# Existing public program detail endpoint
#
# IMPORTANT:
# Keep this route AFTER the /my routes above.
# ============================================================

@router.get("/{program_id}")
def get_affiliate_program(program_id: int):
    """
    Return a single affiliate program by ID.
    """

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                id,
                brand_name,
                category,
                country_market,
                program_name,
                commission_type,
                commission_rate,
                cookie_duration,
                affiliate_network,
                creator_eligible,
                official_program_url,
                application_url,
                verification_notes,
                last_verified_at,
                status
            FROM affiliate_programs
            WHERE id = %s
              AND status = 'active'
        """, (program_id,))

        program = cursor.fetchone()

        if not program:
            raise HTTPException(
                status_code=404,
                detail="Affiliate program not found"
            )

        return {
            "success": True,
            "program": program
        }

    except HTTPException:
        raise

    except Exception as err:
        print(
            f"ERROR [/api/v1/affiliate-programs/"
            f"{program_id}]: {err}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve affiliate program"
        )

    finally:
        cursor.close()
        conn.close()