from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from middleware.auth import verify_token


router = APIRouter(
    prefix="/api/admin/affiliate-program-members",
    tags=["Affiliate Program Admin"]
)


def require_admin(current_user=Depends(verify_token)):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_user


# ============================================================
# Affiliate Program Membership Models
# ============================================================

class AffiliateMembershipApproval(BaseModel):
    external_publisher_id: str = None
    external_id_not_applicable: bool = False
    notes: str = None


class AffiliateMembershipNotes(BaseModel):
    notes: str = None


# ============================================================
# Affiliate Account Models
# ============================================================

class AffiliateAccountCreate(BaseModel):
    membership_id: int
    network_name: str = None
    external_account_id: str = None


class AffiliateAccountUpdate(BaseModel):
    network_name: str = None
    external_account_id: str = None
    status: str = None


# ============================================================
# Affiliate Program Membership Admin API
# ============================================================

@router.get("")
def list_affiliate_memberships(
    current_user=Depends(require_admin)
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                apm.id AS membership_id,
                apm.creator_id,
                u.name AS creator_name,
                u.email AS creator_email,
                apm.program_id,
                ap.brand_name,
                ap.program_name,
                ap.affiliate_network,
                apm.status,
                apm.external_publisher_id,
                apm.joined_at,
                apm.approved_at,
                apm.notes,
                apm.created_at,
                apm.updated_at
            FROM affiliate_program_members apm
            INNER JOIN users u
                ON u.id = apm.creator_id
            INNER JOIN affiliate_programs ap
                ON ap.id = apm.program_id
            ORDER BY
                CASE
                    WHEN apm.status = 'pending' THEN 1
                    WHEN apm.status = 'active' THEN 2
                    WHEN apm.status = 'rejected' THEN 3
                    WHEN apm.status = 'suspended' THEN 4
                    WHEN apm.status = 'withdrawn' THEN 5
                END,
                apm.created_at ASC
            """
        )

        memberships = cursor.fetchall()

        return {
            "success": True,
            "count": len(memberships),
            "memberships": memberships
        }

    finally:
        cursor.close()
        conn.close()


@router.get("/{membership_id}")
def get_affiliate_membership(
    membership_id: int,
    current_user=Depends(require_admin)
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                apm.id AS membership_id,
                apm.creator_id,
                u.name AS creator_name,
                u.email AS creator_email,
                apm.program_id,
                ap.brand_name,
                ap.program_name,
                ap.affiliate_network,
                apm.status,
                apm.external_publisher_id,
                apm.joined_at,
                apm.approved_at,
                apm.notes,
                apm.created_at,
                apm.updated_at
            FROM affiliate_program_members apm
            INNER JOIN users u
                ON u.id = apm.creator_id
            INNER JOIN affiliate_programs ap
                ON ap.id = apm.program_id
            WHERE apm.id = %s
            """,
            (membership_id,)
        )

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

    finally:
        cursor.close()
        conn.close()


@router.post("/{membership_id}/approve")
def approve_affiliate_membership(
    membership_id: int,
    data: AffiliateMembershipApproval,
    current_user=Depends(require_admin)
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                id,
                creator_id,
                program_id,
                status,
                external_publisher_id,
                notes
            FROM affiliate_program_members
            WHERE id = %s
            FOR UPDATE
            """,
            (membership_id,)
        )

        membership = cursor.fetchone()

        if not membership:
            raise HTTPException(
                status_code=404,
                detail="Affiliate program membership not found"
            )

        if membership["status"] == "active":
            raise HTTPException(
                status_code=409,
                detail="This affiliate membership is already active."
            )

        if membership["status"] == "withdrawn":
            raise HTTPException(
                status_code=409,
                detail="A withdrawn membership cannot be approved."
            )

        if membership["status"] == "suspended":
            raise HTTPException(
                status_code=409,
                detail="A suspended membership cannot be approved directly."
            )

        external_id = data.external_publisher_id

        if external_id is not None:
            external_id = external_id.strip()

        if not external_id and not data.external_id_not_applicable:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Approval requires an external_publisher_id, "
                    "or external_id_not_applicable must be set to true."
                )
            )

        if external_id and data.external_id_not_applicable:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Provide an external_publisher_id OR mark "
                    "external_id_not_applicable as true, not both."
                )
            )

        cursor.execute(
            """
            UPDATE affiliate_program_members
            SET
                status = 'active',
                external_publisher_id = %s,
                notes = %s,
                approved_at = NOW()
            WHERE id = %s
            """,
            (
                external_id if external_id else None,
                data.notes,
                membership_id
            )
        )

        conn.commit()

        cursor.execute(
            """
            SELECT
                apm.id AS membership_id,
                apm.creator_id,
                apm.program_id,
                apm.status,
                apm.external_publisher_id,
                apm.joined_at,
                apm.approved_at,
                apm.notes
            FROM affiliate_program_members apm
            WHERE apm.id = %s
            """,
            (membership_id,)
        )

        updated = cursor.fetchone()

        return {
            "success": True,
            "message": "Affiliate program membership approved.",
            "membership": updated
        }

    finally:
        cursor.close()
        conn.close()


@router.post("/{membership_id}/reject")
def reject_affiliate_membership(
    membership_id: int,
    data: AffiliateMembershipNotes,
    current_user=Depends(require_admin)
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, status
            FROM affiliate_program_members
            WHERE id = %s
            FOR UPDATE
            """,
            (membership_id,)
        )

        membership = cursor.fetchone()

        if not membership:
            raise HTTPException(
                status_code=404,
                detail="Affiliate program membership not found"
            )

        if membership["status"] == "active":
            raise HTTPException(
                status_code=409,
                detail="An active membership cannot be rejected. Suspend it instead."
            )

        if membership["status"] == "withdrawn":
            raise HTTPException(
                status_code=409,
                detail="A withdrawn membership cannot be rejected."
            )

        cursor.execute(
            """
            UPDATE affiliate_program_members
            SET
                status = 'rejected',
                notes = %s
            WHERE id = %s
            """,
            (data.notes, membership_id)
        )

        conn.commit()

        return {
            "success": True,
            "message": "Affiliate program membership rejected.",
            "membership_id": membership_id,
            "status": "rejected"
        }

    finally:
        cursor.close()
        conn.close()


@router.post("/{membership_id}/suspend")
def suspend_affiliate_membership(
    membership_id: int,
    data: AffiliateMembershipNotes,
    current_user=Depends(require_admin)
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, status
            FROM affiliate_program_members
            WHERE id = %s
            FOR UPDATE
            """,
            (membership_id,)
        )

        membership = cursor.fetchone()

        if not membership:
            raise HTTPException(
                status_code=404,
                detail="Affiliate program membership not found"
            )

        if membership["status"] != "active":
            raise HTTPException(
                status_code=409,
                detail="Only an active membership can be suspended."
            )

        cursor.execute(
            """
            UPDATE affiliate_program_members
            SET
                status = 'suspended',
                notes = %s
            WHERE id = %s
            """,
            (data.notes, membership_id)
        )

        conn.commit()

        return {
            "success": True,
            "message": "Affiliate program membership suspended.",
            "membership_id": membership_id,
            "status": "suspended"
        }

    finally:
        cursor.close()
        conn.close()


# ============================================================
# Affiliate Accounts Admin API
# ============================================================

@router.get("/accounts/list")
def list_affiliate_accounts(
    current_user=Depends(require_admin)
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                aa.id AS account_id,
                aa.membership_id,
                apm.creator_id,
                u.name AS creator_name,
                u.email AS creator_email,
                apm.program_id,
                ap.brand_name,
                ap.program_name,
                ap.affiliate_network,
                aa.network_name,
                aa.external_account_id,
                aa.status,
                aa.created_at,
                aa.updated_at
            FROM affiliate_accounts aa
            INNER JOIN affiliate_program_members apm
                ON apm.id = aa.membership_id
            INNER JOIN users u
                ON u.id = apm.creator_id
            INNER JOIN affiliate_programs ap
                ON ap.id = apm.program_id
            ORDER BY aa.created_at DESC
            """
        )

        accounts = cursor.fetchall()

        return {
            "success": True,
            "count": len(accounts),
            "accounts": accounts
        }

    finally:
        cursor.close()
        conn.close()


@router.get("/accounts/{account_id}")
def get_affiliate_account(
    account_id: int,
    current_user=Depends(require_admin)
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                aa.id AS account_id,
                aa.membership_id,
                apm.creator_id,
                u.name AS creator_name,
                u.email AS creator_email,
                apm.program_id,
                ap.brand_name,
                ap.program_name,
                ap.affiliate_network,
                apm.status AS membership_status,
                apm.external_publisher_id,
                aa.network_name,
                aa.external_account_id,
                aa.status,
                aa.created_at,
                aa.updated_at
            FROM affiliate_accounts aa
            INNER JOIN affiliate_program_members apm
                ON apm.id = aa.membership_id
            INNER JOIN users u
                ON u.id = apm.creator_id
            INNER JOIN affiliate_programs ap
                ON ap.id = apm.program_id
            WHERE aa.id = %s
            """,
            (account_id,)
        )

        account = cursor.fetchone()

        if not account:
            raise HTTPException(
                status_code=404,
                detail="Affiliate account not found"
            )

        return {
            "success": True,
            "account": account
        }

    finally:
        cursor.close()
        conn.close()


@router.post("/accounts")
def create_affiliate_account(
    data: AffiliateAccountCreate,
    current_user=Depends(require_admin)
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        # ----------------------------------------------------
        # Verify membership
        # ----------------------------------------------------
        cursor.execute(
            """
            SELECT
                apm.id,
                apm.status,
                apm.external_publisher_id,
                ap.affiliate_network
            FROM affiliate_program_members apm
            INNER JOIN affiliate_programs ap
                ON ap.id = apm.program_id
            WHERE apm.id = %s
            FOR UPDATE
            """,
            (data.membership_id,)
        )

        membership = cursor.fetchone()

        if not membership:
            raise HTTPException(
                status_code=404,
                detail="Affiliate program membership not found"
            )

        if membership["status"] != "active":
            raise HTTPException(
                status_code=409,
                detail=(
                    "An affiliate account can only be created "
                    "for an active affiliate membership."
                )
            )

        # ----------------------------------------------------
        # One account per membership
        # ----------------------------------------------------
        cursor.execute(
            """
            SELECT id
            FROM affiliate_accounts
            WHERE membership_id = %s
            """,
            (data.membership_id,)
        )

        existing_account = cursor.fetchone()

        if existing_account:
            raise HTTPException(
                status_code=409,
                detail=(
                    "An affiliate account already exists for "
                    "this membership."
                )
            )

        # ----------------------------------------------------
        # Determine network name
        # ----------------------------------------------------
        network_name = data.network_name

        if network_name is not None:
            network_name = network_name.strip()

        if not network_name:
            network_name = membership["affiliate_network"]

        # ----------------------------------------------------
        # Determine external account ID
        #
        # If the membership already has an external publisher
        # ID and the admin did not provide an account ID,
        # inherit it.
        # ----------------------------------------------------
        external_account_id = data.external_account_id

        if external_account_id is not None:
            external_account_id = external_account_id.strip()

        if not external_account_id:
            external_account_id = membership["external_publisher_id"]

        cursor.execute(
            """
            INSERT INTO affiliate_accounts
            (
                membership_id,
                network_name,
                external_account_id,
                status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                'active'
            )
            """,
            (
                data.membership_id,
                network_name,
                external_account_id
            )
        )

        conn.commit()

        account_id = cursor.lastrowid

        cursor.execute(
            """
            SELECT
                aa.id AS account_id,
                aa.membership_id,
                aa.network_name,
                aa.external_account_id,
                aa.status,
                aa.created_at,
                aa.updated_at
            FROM affiliate_accounts aa
            WHERE aa.id = %s
            """,
            (account_id,)
        )

        account = cursor.fetchone()

        return {
            "success": True,
            "message": "Affiliate account created.",
            "account": account
        }

    finally:
        cursor.close()
        conn.close()


@router.patch("/accounts/{account_id}")
def update_affiliate_account(
    account_id: int,
    data: AffiliateAccountUpdate,
    current_user=Depends(require_admin)
):
    allowed_statuses = {
        "pending",
        "active",
        "inactive",
        "suspended"
    }

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                aa.id,
                aa.membership_id,
                aa.network_name,
                aa.external_account_id,
                aa.status,
                apm.status AS membership_status
            FROM affiliate_accounts aa
            INNER JOIN affiliate_program_members apm
                ON apm.id = aa.membership_id
            WHERE aa.id = %s
            FOR UPDATE
            """,
            (account_id,)
        )

        account = cursor.fetchone()

        if not account:
            raise HTTPException(
                status_code=404,
                detail="Affiliate account not found"
            )

        if data.status is not None:
            if data.status not in allowed_statuses:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Invalid account status. Allowed values: "
                        "pending, active, inactive, suspended."
                    )
                )

            if (
                data.status == "active"
                and account["membership_status"] != "active"
            ):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "An affiliate account cannot be active "
                        "while its membership is not active."
                    )
                )

        network_name = data.network_name

        if network_name is not None:
            network_name = network_name.strip()

        external_account_id = data.external_account_id

        if external_account_id is not None:
            external_account_id = external_account_id.strip()

        # Only update fields that were supplied.
        fields = []
        values = []

        if data.network_name is not None:
            fields.append("network_name = %s")
            values.append(network_name)

        if data.external_account_id is not None:
            fields.append("external_account_id = %s")
            values.append(
                external_account_id if external_account_id else None
            )

        if data.status is not None:
            fields.append("status = %s")
            values.append(data.status)

        if not fields:
            raise HTTPException(
                status_code=400,
                detail="No account fields were provided for update."
            )

        values.append(account_id)

        cursor.execute(
            f"""
            UPDATE affiliate_accounts
            SET {", ".join(fields)}
            WHERE id = %s
            """,
            tuple(values)
        )

        conn.commit()

        cursor.execute(
            """
            SELECT
                aa.id AS account_id,
                aa.membership_id,
                aa.network_name,
                aa.external_account_id,
                aa.status,
                aa.created_at,
                aa.updated_at
            FROM affiliate_accounts aa
            WHERE aa.id = %s
            """,
            (account_id,)
        )

        updated = cursor.fetchone()

        return {
            "success": True,
            "message": "Affiliate account updated.",
            "account": updated
        }

    finally:
        cursor.close()
        conn.close()


@router.post("/accounts/{account_id}/suspend")
def suspend_affiliate_account(
    account_id: int,
    current_user=Depends(require_admin)
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, status
            FROM affiliate_accounts
            WHERE id = %s
            FOR UPDATE
            """,
            (account_id,)
        )

        account = cursor.fetchone()

        if not account:
            raise HTTPException(
                status_code=404,
                detail="Affiliate account not found"
            )

        if account["status"] != "active":
            raise HTTPException(
                status_code=409,
                detail="Only an active affiliate account can be suspended."
            )

        cursor.execute(
            """
            UPDATE affiliate_accounts
            SET status = 'suspended'
            WHERE id = %s
            """,
            (account_id,)
        )

        conn.commit()

        return {
            "success": True,
            "message": "Affiliate account suspended.",
            "account_id": account_id,
            "status": "suspended"
        }

    finally:
        cursor.close()
        conn.close()


@router.post("/accounts/{account_id}/activate")
def activate_affiliate_account(
    account_id: int,
    current_user=Depends(require_admin)
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                aa.id,
                aa.status,
                apm.status AS membership_status
            FROM affiliate_accounts aa
            INNER JOIN affiliate_program_members apm
                ON apm.id = aa.membership_id
            WHERE aa.id = %s
            FOR UPDATE
            """,
            (account_id,)
        )

        account = cursor.fetchone()

        if not account:
            raise HTTPException(
                status_code=404,
                detail="Affiliate account not found"
            )

        if account["membership_status"] != "active":
            raise HTTPException(
                status_code=409,
                detail=(
                    "An affiliate account cannot be activated "
                    "while its membership is not active."
                )
            )

        if account["status"] == "active":
            raise HTTPException(
                status_code=409,
                detail="Affiliate account is already active."
            )

        cursor.execute(
            """
            UPDATE affiliate_accounts
            SET status = 'active'
            WHERE id = %s
            """,
            (account_id,)
        )

        conn.commit()

        return {
            "success": True,
            "message": "Affiliate account activated.",
            "account_id": account_id,
            "status": "active"
        }

    finally:
        cursor.close()
        conn.close()

# ============================================================
# Affiliate Offers Admin API
# ============================================================

class AffiliateOfferCreate(BaseModel):
    program_id: int
    external_offer_id: str = None
    brand_name: str = None
    title: str
    description: str = None
    image_url: str = None
    destination_url: str
    commission_type: str = None
    commission_rate: float = None
    currency: str = "INR"


class AffiliateOfferUpdate(BaseModel):
    external_offer_id: str = None
    brand_name: str = None
    title: str = None
    description: str = None
    image_url: str = None
    destination_url: str = None
    commission_type: str = None
    commission_rate: float = None
    currency: str = None
    status: str = None


@router.get("/offers")
def list_affiliate_offers(
    current_user=Depends(require_admin)
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                ao.id AS offer_id,
                ao.program_id,
                ap.brand_name AS program_brand_name,
                ap.program_name,
                ap.affiliate_network,
                ao.external_offer_id,
                ao.brand_name,
                ao.title,
                ao.description,
                ao.image_url,
                ao.destination_url,
                ao.commission_type,
                ao.commission_rate,
                ao.currency,
                ao.status,
                ao.created_at,
                ao.updated_at
            FROM affiliate_offers ao
            INNER JOIN affiliate_programs ap
                ON ap.id = ao.program_id
            ORDER BY ao.created_at DESC
            """
        )

        offers = cursor.fetchall()

        return {
            "success": True,
            "count": len(offers),
            "offers": offers
        }

    finally:
        cursor.close()
        conn.close()


@router.get("/offers/{offer_id}")
def get_affiliate_offer(
    offer_id: int,
    current_user=Depends(require_admin)
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                ao.id AS offer_id,
                ao.program_id,
                ap.brand_name AS program_brand_name,
                ap.program_name,
                ap.affiliate_network,
                ao.external_offer_id,
                ao.brand_name,
                ao.title,
                ao.description,
                ao.image_url,
                ao.destination_url,
                ao.commission_type,
                ao.commission_rate,
                ao.currency,
                ao.status,
                ao.created_at,
                ao.updated_at
            FROM affiliate_offers ao
            INNER JOIN affiliate_programs ap
                ON ap.id = ao.program_id
            WHERE ao.id = %s
            """,
            (offer_id,)
        )

        offer = cursor.fetchone()

        if not offer:
            raise HTTPException(
                status_code=404,
                detail="Affiliate offer not found"
            )

        return {
            "success": True,
            "offer": offer
        }

    finally:
        cursor.close()
        conn.close()


@router.post("/offers")
def create_affiliate_offer(
    data: AffiliateOfferCreate,
    current_user=Depends(require_admin)
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        # ----------------------------------------------------
        # Verify affiliate program exists
        # ----------------------------------------------------
        cursor.execute(
            """
            SELECT
                id,
                brand_name,
                program_name,
                affiliate_network
            FROM affiliate_programs
            WHERE id = %s
            """,
            (data.program_id,)
        )

        program = cursor.fetchone()

        if not program:
            raise HTTPException(
                status_code=404,
                detail="Affiliate program not found"
            )

        # ----------------------------------------------------
        # Validate required strings
        # ----------------------------------------------------
        title = data.title.strip()

        if not title:
            raise HTTPException(
                status_code=400,
                detail="Offer title cannot be empty."
            )

        destination_url = data.destination_url.strip()

        if not destination_url:
            raise HTTPException(
                status_code=400,
                detail="Destination URL cannot be empty."
            )

        # ----------------------------------------------------
        # Normalize optional fields
        # ----------------------------------------------------
        external_offer_id = data.external_offer_id

        if external_offer_id is not None:
            external_offer_id = external_offer_id.strip()

        brand_name = data.brand_name

        if brand_name is not None:
            brand_name = brand_name.strip()

        if not brand_name:
            brand_name = program["brand_name"]

        commission_type = data.commission_type

        if commission_type is not None:
            commission_type = commission_type.strip()

        currency = data.currency

        if currency is not None:
            currency = currency.strip().upper()

        if not currency:
            currency = "INR"

        # ----------------------------------------------------
        # Create offer
        # ----------------------------------------------------
        cursor.execute(
            """
            INSERT INTO affiliate_offers
            (
                program_id,
                external_offer_id,
                brand_name,
                title,
                description,
                image_url,
                destination_url,
                commission_type,
                commission_rate,
                currency,
                status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                'active'
            )
            """,
            (
                data.program_id,
                external_offer_id if external_offer_id else None,
                brand_name,
                title,
                data.description,
                data.image_url,
                destination_url,
                commission_type if commission_type else None,
                data.commission_rate,
                currency
            )
        )

        conn.commit()

        offer_id = cursor.lastrowid

        cursor.execute(
            """
            SELECT
                ao.id AS offer_id,
                ao.program_id,
                ao.external_offer_id,
                ao.brand_name,
                ao.title,
                ao.description,
                ao.image_url,
                ao.destination_url,
                ao.commission_type,
                ao.commission_rate,
                ao.currency,
                ao.status,
                ao.created_at,
                ao.updated_at
            FROM affiliate_offers ao
            WHERE ao.id = %s
            """,
            (offer_id,)
        )

        offer = cursor.fetchone()

        return {
            "success": True,
            "message": "Affiliate offer created.",
            "offer": offer
        }

    finally:
        cursor.close()
        conn.close()


@router.patch("/offers/{offer_id}")
def update_affiliate_offer(
    offer_id: int,
    data: AffiliateOfferUpdate,
    current_user=Depends(require_admin)
):
    allowed_statuses = {
        "active",
        "inactive",
        "expired"
    }

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                id,
                program_id,
                external_offer_id,
                brand_name,
                title,
                description,
                image_url,
                destination_url,
                commission_type,
                commission_rate,
                currency,
                status
            FROM affiliate_offers
            WHERE id = %s
            FOR UPDATE
            """,
            (offer_id,)
        )

        offer = cursor.fetchone()

        if not offer:
            raise HTTPException(
                status_code=404,
                detail="Affiliate offer not found"
            )

        if data.status is not None:
            if data.status not in allowed_statuses:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Invalid offer status. Allowed values: "
                        "active, inactive, expired."
                    )
                )

        fields = []
        values = []

        if data.external_offer_id is not None:
            value = data.external_offer_id.strip()

            fields.append("external_offer_id = %s")
            values.append(value if value else None)

        if data.brand_name is not None:
            value = data.brand_name.strip()

            if not value:
                raise HTTPException(
                    status_code=400,
                    detail="Brand name cannot be empty."
                )

            fields.append("brand_name = %s")
            values.append(value)

        if data.title is not None:
            value = data.title.strip()

            if not value:
                raise HTTPException(
                    status_code=400,
                    detail="Offer title cannot be empty."
                )

            fields.append("title = %s")
            values.append(value)

        if data.description is not None:
            fields.append("description = %s")
            values.append(data.description)

        if data.image_url is not None:
            fields.append("image_url = %s")
            values.append(data.image_url)

        if data.destination_url is not None:
            value = data.destination_url.strip()

            if not value:
                raise HTTPException(
                    status_code=400,
                    detail="Destination URL cannot be empty."
                )

            fields.append("destination_url = %s")
            values.append(value)

        if data.commission_type is not None:
            value = data.commission_type.strip()

            fields.append("commission_type = %s")
            values.append(value if value else None)

        if data.commission_rate is not None:
            fields.append("commission_rate = %s")
            values.append(data.commission_rate)

        if data.currency is not None:
            value = data.currency.strip().upper()

            if not value:
                raise HTTPException(
                    status_code=400,
                    detail="Currency cannot be empty."
                )

            fields.append("currency = %s")
            values.append(value)

        if data.status is not None:
            fields.append("status = %s")
            values.append(data.status)

        if not fields:
            raise HTTPException(
                status_code=400,
                detail="No offer fields were provided for update."
            )

        values.append(offer_id)

        cursor.execute(
            f"""
            UPDATE affiliate_offers
            SET {", ".join(fields)}
            WHERE id = %s
            """,
            tuple(values)
        )

        conn.commit()

        cursor.execute(
            """
            SELECT
                ao.id AS offer_id,
                ao.program_id,
                ao.external_offer_id,
                ao.brand_name,
                ao.title,
                ao.description,
                ao.image_url,
                ao.destination_url,
                ao.commission_type,
                ao.commission_rate,
                ao.currency,
                ao.status,
                ao.created_at,
                ao.updated_at
            FROM affiliate_offers ao
            WHERE ao.id = %s
            """,
            (offer_id,)
        )

        updated = cursor.fetchone()

        return {
            "success": True,
            "message": "Affiliate offer updated.",
            "offer": updated
        }

    finally:
        cursor.close()
        conn.close()


@router.post("/offers/{offer_id}/deactivate")
def deactivate_affiliate_offer(
    offer_id: int,
    current_user=Depends(require_admin)
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, status
            FROM affiliate_offers
            WHERE id = %s
            FOR UPDATE
            """,
            (offer_id,)
        )

        offer = cursor.fetchone()

        if not offer:
            raise HTTPException(
                status_code=404,
                detail="Affiliate offer not found"
            )

        if offer["status"] == "expired":
            raise HTTPException(
                status_code=409,
                detail="An expired offer cannot be deactivated."
            )

        if offer["status"] == "inactive":
            raise HTTPException(
                status_code=409,
                detail="Affiliate offer is already inactive."
            )

        cursor.execute(
            """
            UPDATE affiliate_offers
            SET status = 'inactive'
            WHERE id = %s
            """,
            (offer_id,)
        )

        conn.commit()

        return {
            "success": True,
            "message": "Affiliate offer deactivated.",
            "offer_id": offer_id,
            "status": "inactive"
        }

    finally:
        cursor.close()
        conn.close()


@router.post("/offers/{offer_id}/activate")
def activate_affiliate_offer(
    offer_id: int,
    current_user=Depends(require_admin)
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, status
            FROM affiliate_offers
            WHERE id = %s
            FOR UPDATE
            """,
            (offer_id,)
        )

        offer = cursor.fetchone()

        if not offer:
            raise HTTPException(
                status_code=404,
                detail="Affiliate offer not found"
            )

        if offer["status"] == "expired":
            raise HTTPException(
                status_code=409,
                detail="An expired offer cannot be activated."
            )

        if offer["status"] == "active":
            raise HTTPException(
                status_code=409,
                detail="Affiliate offer is already active."
            )

        cursor.execute(
            """
            UPDATE affiliate_offers
            SET status = 'active'
            WHERE id = %s
            """,
            (offer_id,)
        )

        conn.commit()

        return {
            "success": True,
            "message": "Affiliate offer activated.",
            "offer_id": offer_id,
            "status": "active"
        }

    finally:
        cursor.close()
        conn.close()        