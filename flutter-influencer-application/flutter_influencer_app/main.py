from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from database import get_db
from middleware.auth import verify_token

from routers import auth, campaigns, submissions, marketplace, blogs, redirect, creator_registration, founding_admin, affiliate_programs, affiliate_admin, affiliate_offers, affiliate_links, affiliate_redirect, affiliate_earnings, affiliate_payouts

app = FastAPI(title="Nano Influencer Python Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://rmworkz.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all modular routers
app.include_router(auth.router)
app.include_router(campaigns.router)
app.include_router(submissions.router)
app.include_router(marketplace.router)
app.include_router(blogs.router)
app.include_router(redirect.router)
app.include_router(creator_registration.router)
app.include_router(founding_admin.router)
app.include_router(affiliate_admin.router)
app.include_router(affiliate_programs.router)
app.include_router(affiliate_offers.router)
app.include_router(affiliate_links.router)
app.include_router(affiliate_redirect.router)
app.include_router(affiliate_earnings.router)
app.include_router(affiliate_payouts.router)

@app.get("/api/products/{product_id}")
def get_single_product(product_id: int):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT c.id, c.title, p.price AS retail_price, c.payout_per_post AS payout_amount 
               FROM campaigns c
               LEFT JOIN marketplace_products p ON c.title = p.title
               WHERE c.id = %s""", 
            (product_id,)
        )
        rows = cursor.fetchall()
        if rows:
            return rows[0]
        raise HTTPException(status_code=404, detail="Campaign/Product not found")
    except Exception as err:
        raise HTTPException(status_code=500, detail="Server error")
    finally:
        cursor.close()
        conn.close()

@app.get("/api/stats/overview")
def get_stats_overview(user = Depends(verify_token)):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        creator_id = user['id']
        cursor.execute("""
          SELECT 
            IFNULL((SELECT SUM(payout_amount) FROM submissions WHERE creator_id = %s), 0) +
            IFNULL((SELECT SUM(payout_amount) FROM marketplace_submissions WHERE creator_id = %s), 0) 
            AS total_earned,
            
            IFNULL((SELECT COUNT(*) FROM affiliate_clicks WHERE creator_id = %s), 0) AS total_clicks,
            
            IFNULL(ROUND((
              (SELECT COUNT(*) FROM (SELECT id FROM submissions WHERE creator_id = %s UNION ALL SELECT id FROM marketplace_submissions WHERE creator_id = %s) AS sub) 
              / NULLIF((SELECT COUNT(*) FROM affiliate_clicks WHERE creator_id = %s), 0)
            ) * 100, 1), 0) AS conversion_rate
        """, (creator_id, creator_id, creator_id, creator_id, creator_id, creator_id))
        
        rows = cursor.fetchall()
        return rows[0] if rows else {"total_earned": 0, "total_clicks": 0, "conversion_rate": 0}
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        cursor.close()
        conn.close()

# Dynamic endpoint that filters blog content and active campaigns based on category from the database
@app.get("/api/blogs/{category}", response_class=HTMLResponse)
def get_category_blog_view(category: str, creator_id: int = 1):
    normalized_category = category.capitalize()
    valid_categories = ["Travel", "Beauty", "Tech"]
    
    if normalized_category not in valid_categories:
        raise HTTPException(status_code=404, detail="Blog network category not found")
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT id, title, description, payout_per_post, required_hashtag, product_url 
               FROM campaigns 
               WHERE LOWER(category) = LOWER(%s)""",
            (normalized_category,)
        )
        filtered_campaigns = cursor.fetchall()
    except Exception as err:
        filtered_campaigns = []
    finally:
        cursor.close()
        conn.close()
        
    campaigns_html = "".join(
        f"""
        <div style="background: #1e293b; padding: 18px; margin-bottom: 14px; border-radius: 12px; border-left: 4px solid #38bdf8; display: flex; flex-direction: column; gap: 8px;">
            <h3 style="margin: 0; color: #ffffff; font-size: 16px;">{c['title']}</h3>
            <p style="margin: 0; color: #94a3b8; font-size: 13px;">{c.get('description', '')}</p>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
                <span style="color: #4ade80; font-weight: bold; font-size: 14px;">Payout: ₹{c.get('payout_per_post', 0)}</span>
                <a href="/checkout/campaign/{c['id']}?creator_id={creator_id}" target="_blank" style="background: #38bdf8; color: #020617; padding: 8px 14px; border-radius: 8px; font-weight: bold; font-size: 12px; text-decoration: none; box-shadow: 0 4px 12px rgba(56,189,248,0.2);">💳 Complete Purchase</a>
            </div>
        </div>
        """ for c in filtered_campaigns
    ) or "<p style='color: #94a3b8;'>No active campaigns currently injected for this network.</p>"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{normalized_category} Native Blog Network - NanoConnect</title>
        <style>
            body {{ background-color: #020617; color: #f8fafc; font-family: 'Inter', sans-serif; padding: 30px; margin: 0; }}
            .container {{ max-width: 700px; margin: 0 auto; background: #0f172a; padding: 30px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
            h1 {{ color: #38bdf8; font-size: 24px; margin-top: 0; }}
            .badge {{ display: inline-block; background: rgba(56, 189, 248, 0.2); color: #38bdf8; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; margin-bottom: 15px; }}
            p {{ color: #cbd5e1; line-height: 1.5; }}
            .section-title {{ color: #a855f7; font-size: 14px; font-weight: bold; text-transform: uppercase; margin-top: 25px; margin-bottom: 12px; letter-spacing: 0.5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <span class="badge">{normalized_category} NETWORK</span>
            <h1>🌐 {normalized_category} Native Blog Stream</h1>
            <p>Welcome to the publisher network portal for <strong>{normalized_category}</strong> content. Below are your live injected campaign streams and monetization updates:</p>
            
            <div class="section-title">Active Injected Campaigns ({len(filtered_campaigns)})</div>
            {campaigns_html}
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/ref/{creator_id}/{campaign_id}")
def track_affiliate_click(creator_id: int, campaign_id: int):
    print(f"DEBUG [/ref/]: Received request for creator_id={creator_id}, item_id={campaign_id}")
    
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Check if it's a marketplace product
        cursor.execute("SELECT id FROM marketplace_products WHERE id = %s", (campaign_id,))
        product = cursor.fetchone()
        print(f"DEBUG [/ref/]: marketplace_products lookup result: {product}")
        
        if product:
            print(f"DEBUG [/ref/]: Target ID {campaign_id} identified as Marketplace Product. Redirecting to product checkout.")
            target_url = f"http://87.106.214.100:8080/checkout/product/{campaign_id}?creator_id={creator_id}"
        else:
            # Fallback check for standard campaign table
            cursor.execute("SELECT id FROM campaigns WHERE id = %s", (campaign_id,))
            campaign = cursor.fetchone()
            print(f"DEBUG [/ref/]: campaigns lookup result: {campaign}")
            
            if not campaign:
                print(f"DEBUG ERROR [/ref/]: ID {campaign_id} not found in either marketplace_products or campaigns!")
                raise HTTPException(status_code=404, detail=f"ID {campaign_id} Not Found in Database")
            
            print(f"DEBUG [/ref/]: Target ID {campaign_id} identified as Standard Campaign. Redirecting to campaign checkout.")
            target_url = f"http://87.106.214.100:8080/checkout/campaign/{campaign_id}?creator_id={creator_id}"

        # Log click using product_id instead of campaign_id
        cursor.execute(
            """INSERT INTO affiliate_clicks (creator_id, product_id, clicked_at) 
                VALUES (%s, %s, NOW())""",
            (creator_id, campaign_id)
        )
        conn.commit()
        print(f"DEBUG [/ref/]: Click successfully logged for creator {creator_id}, item {campaign_id}")
        
    except HTTPException:
        raise
    except Exception as err:
        conn.rollback()
        print(f"DEBUG ERROR [/ref/]: {err}")
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        cursor.close()
        conn.close()
    
    return RedirectResponse(url=target_url, status_code=303)

@app.get("/checkout/campaign/{campaign_id}", response_class=HTMLResponse)
def checkout_campaign(campaign_id: int, creator_id: int = 1):
    print(f"DEBUG [/checkout/campaign/]: Entering with campaign_id={campaign_id}, creator_id={creator_id}")
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT id, title, payout_per_post as payout_amount, description 
               FROM campaigns WHERE id = %s""",
            (campaign_id,)
        )
        item = cursor.fetchone()
        print(f"DEBUG [/checkout/campaign/]: Query result -> {item}")
            
        if not item:
            print(f"DEBUG ERROR [/checkout/campaign/]: Campaign ID {campaign_id} not found.")
            raise HTTPException(status_code=404, detail="Campaign not found")
            
        title = item['title']
        payout = float(item.get('payout_amount', 0.0) or 0.0)
        print(f"DEBUG [/checkout/campaign/]: Inserting submission for title='{title}', payout={payout}")

        cursor.execute(
            """INSERT INTO submissions (creator_id, campaign_id, payout_amount, status, proof_url, submitted_at) 
               VALUES (%s, %s, %s, %s, %s, NOW())""",
            (creator_id, campaign_id, payout, "approved", f"http://87.106.214.100:8080/checkout/campaign/{campaign_id}?creator_id={creator_id}")
        )
        conn.commit()
        print(f"DEBUG [/checkout/campaign/]: Submission committed successfully.")

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Campaign Checkout Successful - NanoConnect</title>
            <style>
                body {{ background-color: #020617; color: #f8fafc; font-family: 'Inter', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                .card {{ background-color: #0f172a; padding: 36px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.08); text-align: center; max-width: 420px; width: 100%; box-shadow: 0 15px 35px rgba(0,0,0,0.6); }}
                h2 {{ color: #4ade80; margin-top: 0; font-size: 22px; }}
                p {{ color: #94a3b8; font-size: 14px; line-height: 1.5; }}
                .product-title {{ color: #ffffff; font-weight: bold; font-size: 16px; margin: 12px 0; }}
                .price {{ color: #38bdf8; font-size: 28px; font-weight: bold; margin: 16px 0; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>🎉 Campaign Verification Complete!</h2>
                <p>Recorded successfully for campaign:</p>
                <div class="product-title">{title}</div>
                <div class="price">₹{payout:.2f}</div>
                <p>Payout has been logged to your dashboard for Creator #{creator_id}.</p>
            </div>
        </body>
        </html>
        """
    except HTTPException:
        raise
    except Exception as err:
        conn.rollback()
        print(f"DEBUG ERROR [/checkout/campaign/]: {err}")
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        cursor.close()
        conn.close()

@app.get("/checkout/product/{product_id}", response_class=HTMLResponse)
def checkout_marketplace_product(product_id: int, creator_id: int = 1):
    print(f"DEBUG [/checkout/product/]: Entering with product_id={product_id}, creator_id={creator_id}")
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """SELECT id, title, (price * commission_percentage / 100) as payout_amount, description 
               FROM marketplace_products WHERE id = %s""",
            (product_id,)
        )
        item = cursor.fetchone()
        print(f"DEBUG [/checkout/product/]: Query result -> {item}")
            
        if not item:
            print(f"DEBUG ERROR [/checkout/product/]: Marketplace product ID {product_id} not found.")
            raise HTTPException(status_code=404, detail="Marketplace product not found")
            
        title = item['title']
        payout = float(item.get('payout_amount', 0.0) or 0.0)
        print(f"DEBUG [/checkout/product/]: Inserting submission into marketplace_submissions for item title='{title}', payout={payout}")

        # FIXED: Insert into marketplace_submissions to match what /api/submissions/my-logs expects
        cursor.execute(
            """INSERT INTO marketplace_submissions (product_id, creator_id, status, payout_amount, submitted_at) 
               VALUES (%s, %s, %s, %s, NOW())""",
            (product_id, creator_id, "approved", payout)
        )
        conn.commit()
        print(f"DEBUG [/checkout/product/]: Marketplace submission committed successfully.")

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Marketplace Checkout Successful - NanoConnect</title>
            <style>
                body {{ background-color: #020617; color: #f8fafc; font-family: 'Inter', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                .card {{ background-color: #0f172a; padding: 36px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.08); text-align: center; max-width: 420px; width: 100%; box-shadow: 0 15px 35px rgba(0,0,0,0.6); }}
                h2 {{ color: #4ade80; margin-top: 0; font-size: 22px; }}
                p {{ color: #94a3b8; font-size: 14px; line-height: 1.5; }}
                .product-title {{ color: #ffffff; font-weight: bold; font-size: 16px; margin: 12px 0; }}
                .price {{ color: #38bdf8; font-size: 28px; font-weight: bold; margin: 16px 0; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>🎉 Purchase Successful!</h2>
                <p>Mock transaction completed for marketplace product:</p>
                <div class="product-title">{title}</div>
                <div class="price">₹{payout:.2f}</div>
                <p>Commission has been successfully recorded for Creator #{creator_id}.</p>
            </div>
        </body>
        </html>
        """
    except HTTPException:
        raise
    except Exception as err:
        conn.rollback()
        print(f"DEBUG ERROR [/checkout/product/]: {err}")
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        cursor.close()
        conn.close()
        
@app.get("/")
def root():
    return {"message": "Nano Influencer Python FastAPI is running!"} 