from pathlib import Path

path = Path(r"lib\influencer_dashboard.dart")
text = path.read_text(encoding="utf-8")

old = """        // ============================================================
        // AFFILIATE OFFERS
        // ============================================================



        const SizedBox(height: 24),"""

new = """        // ============================================================
        // AFFILIATE OFFERS
        // ============================================================

        _buildAffiliateOffersSection(),

        const SizedBox(height: 24),"""

if old not in text:
    raise SystemExit("ERROR: Expected Affiliate Offers placeholder was not found.")

if text.count(old) != 1:
    raise SystemExit(
        f"ERROR: Expected exactly 1 placeholder, found {text.count(old)}."
    )

path.write_text(text.replace(old, new, 1), encoding="utf-8")

print("SUCCESS: Affiliate Offers section activated.")
