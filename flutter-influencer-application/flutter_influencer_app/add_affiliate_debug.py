from pathlib import Path

path = Path("lib/influencer_dashboard.dart")
text = path.read_text(encoding="utf-8")

old = """      final offers = result['offers'] is List
          ? List<dynamic>.from(result['offers'])
          : <dynamic>[];

      final Map<int, List<dynamic>> groupedOffers = {};
"""

new = """      final offers = result['offers'] is List
          ? List<dynamic>.from(result['offers'])
          : <dynamic>[];

      final debugProgramIds = offers
          .whereType<Map>()
          .map((offer) => offer['program_id'])
          .toSet()
          .toList();

      debugPrint(
        'AFFILIATE OFFERS DEBUG: '
        'success=${result['success']}, '
        'count=${result['count']}, '
        'total=${result['total']}, '
        'offers.length=${offers.length}, '
        'programIds=$debugProgramIds',
      );

      final Map<int, List<dynamic>> groupedOffers = {};
"""

if old not in text:
    raise SystemExit("Target code was not found. No changes made.")

path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("Temporary diagnostic added successfully.")