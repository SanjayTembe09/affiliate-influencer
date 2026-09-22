from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from database import get_db
from middleware.auth import verify_token


router = APIRouter(
    prefix="/api/v1/affiliate",
    tags=["Affiliate Payouts"]
)


class PayoutRequest(BaseModel):
    amount: float = Field(gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=10)
    payment_method: str | None = Field(default=None, max_length=100)
    notes: str | None = None


@router.post("/payouts")
def request_payout(
    payout: PayoutRequest,
    user=Depends(verify_token)
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        creator_id = user["id"]
        currency = payout.currency.upper()

        # ---------------------------------------------------------
        # START TRANSACTION
        # ---------------------------------------------------------

        conn.start_transaction()

        # ---------------------------------------------------------
        # AVAILABLE AFFILIATE CREDITS
        #
        # Lock the creator's affiliate ledger rows so that
        # concurrent payout requests cannot spend the same balance.
        # ---------------------------------------------------------

        cursor.execute(
            """
            SELECT
                COALESCE(SUM(amount), 0) AS available_credits
            FROM commission_ledger
            WHERE creator_id = %s
              AND source_type = 'affiliate'
              AND entry_type = 'credit'
              AND status = 'available'
              AND currency = %s
            FOR UPDATE
            """,
            (creator_id, currency)
        )

        credit_row = cursor.fetchone()
        available_credits = float(
            credit_row["available_credits"] or 0
        )

        # ---------------------------------------------------------
        # EXISTING REQUESTED / PROCESSING PAYOUTS
        #
        # These amounts are reserved and therefore cannot be
        # requested again.
        # ---------------------------------------------------------

        cursor.execute(
            """
            SELECT
                COALESCE(SUM(amount), 0) AS reserved_amount
            FROM payouts
            WHERE creator_id = %s
              AND currency = %s
              AND status IN ('requested', 'processing')
            FOR UPDATE
            """,
            (creator_id, currency)
        )

        reserved_row = cursor.fetchone()
        reserved_amount = float(
            reserved_row["reserved_amount"] or 0
        )

        # ---------------------------------------------------------
        # ALREADY PAID PAYOUTS
        #
        # Paid payout debits have already been deducted from the
        # creator's available affiliate balance.
        # ---------------------------------------------------------

        cursor.execute(
            """
            SELECT
                COALESCE(SUM(amount), 0) AS paid_payout_amount
            FROM commission_ledger
            WHERE creator_id = %s
            AND source_type = 'payout'
            AND entry_type = 'debit'
            AND status = 'paid'
            AND currency = %s
            FOR UPDATE
            """,
            (creator_id, currency)
        )

        paid_payout_row = cursor.fetchone()
        paid_payout_amount = float(
            paid_payout_row["paid_payout_amount"] or 0
        )

        effective_available = (
            available_credits
            - reserved_amount
            - paid_payout_amount
        )

        # ---------------------------------------------------------
        # BALANCE VALIDATION
        # ---------------------------------------------------------

        if payout.amount > effective_available:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Insufficient available affiliate balance.",
                    "available_balance": round(
                        max(effective_available, 0),
                        2
                    ),
                    "requested_amount": round(
                        payout.amount,
                        2
                    ),
                    "currency": currency
                }
            )

        # ---------------------------------------------------------
        # CREATE PAYOUT REQUEST
        # ---------------------------------------------------------

        cursor.execute(
            """
            INSERT INTO payouts
                (
                    creator_id,
                    amount,
                    currency,
                    status,
                    payment_method,
                    notes
                )
            VALUES
                (
                    %s,
                    %s,
                    %s,
                    'requested',
                    %s,
                    %s
                )
            """,
            (
                creator_id,
                payout.amount,
                currency,
                payout.payment_method,
                payout.notes
            )
        )

        payout_id = cursor.lastrowid

        conn.commit()

        # ---------------------------------------------------------
        # RETURN CREATED PAYOUT
        # ---------------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                creator_id,
                amount,
                currency,
                status,
                payment_method,
                payment_reference,
                requested_at,
                processed_at,
                notes
            FROM payouts
            WHERE id = %s
            """,
            (payout_id,)
        )

        created_payout = cursor.fetchone()

        remaining_available = (
            effective_available - payout.amount
        )

        return {
            "success": True,
            "message": "Payout request created successfully.",
            "payout": created_payout,
            "remaining_available": round(
                remaining_available,
                2
            )
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as err:
        conn.rollback()

        print(
            f"DEBUG ERROR [/api/v1/affiliate/payouts]: {err}"
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to create payout request"
        )

    finally:
        cursor.close()
        conn.close()