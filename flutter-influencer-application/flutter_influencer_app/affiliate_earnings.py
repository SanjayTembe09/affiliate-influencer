from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from middleware.auth import verify_token

router = APIRouter(
    prefix="/api/v1/affiliate",
    tags=["Affiliate Earnings"]
)


@router.get("/earnings")
def get_affiliate_earnings(user=Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        creator_id = user["id"]

        # ---------------------------------------------------------
        # EARNINGS SUMMARY BY CURRENCY
        # ---------------------------------------------------------

        cursor.execute(
            """
            SELECT
                currency,

                COALESCE(
                    SUM(
                        CASE
                            WHEN entry_type = 'credit'
                            AND status IN ('pending', 'available', 'paid')
                            THEN amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS total_earned,

                COALESCE(
                    SUM(
                        CASE
                            WHEN entry_type = 'credit'
                            AND status = 'pending'
                            THEN amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS pending,

                (
                    COALESCE(
                        SUM(
                            CASE
                                WHEN entry_type = 'credit'
                                AND status = 'available'
                                THEN amount
                                ELSE 0
                            END
                        ),
                        0
                    )
                    -
                    COALESCE(
                        (
                            SELECT SUM(p.amount)
                            FROM payouts p
                            WHERE p.creator_id = %s
                            AND p.currency = commission_ledger.currency
                            AND p.status IN ('requested', 'processing')
                        ),
                        0
                    )
                    -
                    COALESCE(
                        SUM(
                            CASE
                                WHEN entry_type = 'debit'
                                AND source_type = 'payout'
                                AND status = 'paid'
                                THEN amount
                                ELSE 0
                            END
                        ),
                        0
                    )
                ) AS available,

                COALESCE(
                    SUM(
                        CASE
                            WHEN entry_type = 'credit'
                            AND status = 'paid'
                            THEN amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS paid

            FROM commission_ledger
            WHERE creator_id = %s
            GROUP BY currency
            ORDER BY currency
            """,
            (creator_id, creator_id)
        )

        summary_rows = cursor.fetchall()

        summary = []

        for row in summary_rows:
            summary.append(
                {
                    "currency": row["currency"],
                    "total_earned": float(row["total_earned"] or 0),
                    "pending": float(row["pending"] or 0),
                    "available": float(row["available"] or 0),
                    "paid": float(row["paid"] or 0),
                }
            )

        # ---------------------------------------------------------
        # LEDGER ENTRIES
        # ---------------------------------------------------------

        cursor.execute(
            """
            SELECT
                cl.id,
                cl.source_type,
                cl.source_id,
                cl.entry_type,
                cl.amount,
                cl.currency,
                cl.status,
                cl.description,
                cl.created_at
            FROM commission_ledger cl
            WHERE cl.creator_id = %s
            ORDER BY cl.created_at DESC, cl.id DESC
            """,
            (creator_id,)
        )

        entries = cursor.fetchall()

        return {
            "success": True,
            "creator_id": creator_id,
            "summary": summary,
            "entries": entries
        }

    except Exception as err:
        print(
            f"DEBUG ERROR [/api/v1/affiliate/earnings]: {err}"
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve affiliate earnings"
        )

    finally:
        cursor.close()
        conn.close()