from pathlib import Path

path = Path(r"lib\influencer_dashboard.dart")

source = path.read_text(encoding="utf-8")

marker = """  // ============================================================
  // CREATE SOCIAL PUBLISHER PRODUCT POST
  // ============================================================"""

method = """  // ============================================================
  // LOAD AFFILIATE OFFERS FOR PROGRAMS
  // ============================================================

  Future<void> _loadAffiliateOffersForPrograms() async {
    setState(() {
      _isLoadingAffiliateOffers = true;
    });

    try {
      final result = await ApiService.getAffiliateOffers(
        page: 1,
        limit: _affiliateOffersLoadLimit,
      );

      if (!mounted) return;

      final offers = result['offers'] is List
          ? List<dynamic>.from(result['offers'])
          : <dynamic>[];

      final Map<int, List<dynamic>> groupedOffers = {};

      for (final offer in offers) {
        if (offer is! Map) continue;

        final programId = int.tryParse(
          offer['program_id']?.toString() ?? '',
        );

        if (programId == null) continue;

        groupedOffers.putIfAbsent(programId, () => []);
        groupedOffers[programId]!.add(
          Map<String, dynamic>.from(offer),
        );
      }

      setState(() {
        _affiliateOffersByProgram = groupedOffers;
        _affiliateOfferTotal = offers.length;
        _isLoadingAffiliateOffers = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _isLoadingAffiliateOffers = false;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Failed to load Affiliate Offers: $e',
          ),
        ),
      );
    }
  }


"""

if marker not in source:
    raise SystemExit("ERROR: insertion marker not found - NO FILE CHANGED")

if "_loadAffiliateOffersForPrograms" in source:
    raise SystemExit("ERROR: method already exists - NO FILE CHANGED")

updated = source.replace(marker, method + marker, 1)

path.write_text(updated, encoding="utf-8")

print("SUCCESS: method inserted")
print(f"Old size: {len(source.encode('utf-8'))} bytes")
print(f"New size: {path.stat().st_size} bytes")
