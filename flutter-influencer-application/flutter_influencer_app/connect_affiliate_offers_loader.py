from pathlib import Path

path = Path(r"lib\influencer_dashboard.dart")
source = path.read_text(encoding="utf-8")

old_init = """    _loadAffiliateOffers();
    _loadAffiliatePrograms();"""

new_init = """    _loadAffiliateOffers();
    _loadAffiliateOffersForPrograms();
    _loadAffiliatePrograms();"""

old_refresh = """       _loadAffiliateOffers(),
      _loadAffiliatePrograms(),"""

new_refresh = """       _loadAffiliateOffers(),
      _loadAffiliateOffersForPrograms(),
      _loadAffiliatePrograms(),"""

if source.count(old_init) != 1:
    raise SystemExit(
        f"ERROR: expected exactly 1 initState match, found {source.count(old_init)} - NO FILE CHANGED"
    )

if source.count(old_refresh) != 1:
    raise SystemExit(
        f"ERROR: expected exactly 1 refresh match, found {source.count(old_refresh)} - NO FILE CHANGED"
    )

updated = source.replace(old_init, new_init, 1)
updated = updated.replace(old_refresh, new_refresh, 1)

path.write_text(updated, encoding="utf-8")

print("SUCCESS: grouped affiliate-offer loader connected to initState and refresh")
print(f"New size: {path.stat().st_size} bytes")
