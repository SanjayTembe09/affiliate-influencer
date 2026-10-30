from pathlib import Path
from datetime import datetime
import shutil
import sys

path = Path("lib/influencer_dashboard.dart")

if not path.exists():
    sys.exit(f"STOP: File not found: {path}")

source = path.read_text(encoding="utf-8")

replacements = [
    (
        "  int? _selectedAffiliateProgramId;\n"
        "  Map<int, List<dynamic>> _affiliateOffersByProgram = {};",
        "  int? _selectedAffiliateProgramId;\n"
        "  Map<int, List<dynamic>> _affiliateOffersByProgram = {};\n"
        "\n"
        "  // Offers belonging to this influencer's joined programs.\n"
        "  List<dynamic> _myOffers = [];\n"
        "  bool _isLoadingMyOffers = false;",
        "My Offers state",
    ),
    (
        "    _loadAffiliateOffersForPrograms();\n"
        "    _loadAffiliatePrograms();\n"
        "    _loadAffiliateEarnings();",
        "    _loadAffiliateOffersForPrograms();\n"
        "    _loadAffiliatePrograms();\n"
        "    _loadMyOffers();\n"
        "    _loadAffiliateEarnings();",
        "My Offers initial load",
    ),
    (
        "      _loadAffiliateOffersForPrograms(),\n"
        "      _loadAffiliatePrograms(),\n"
        "      _loadAffiliateEarnings(),",
        "      _loadAffiliateOffersForPrograms(),\n"
        "      _loadAffiliatePrograms(),\n"
        "      _loadMyOffers(),\n"
        "      _loadAffiliateEarnings(),",
        "My Offers refresh",
    ),
    (
        "        // ============================================================\n"
        "        // AFFILIATE OFFERS\n"
        "        // ============================================================\n"
        "\n"
        "        _buildAffiliateOffersSection(),",
        "        // MY OFFERS: only offers from joined programs\n"
        "        _buildMyOffersSection(),\n"
        "        const SizedBox(height: 24),\n"
        "\n"
        "        // ============================================================\n"
        "        // AFFILIATE OFFERS\n"
        "        // ============================================================\n"
        "\n"
        "        _buildAffiliateOffersSection(),",
        "My Offers display position",
    ),
]

loader_marker = (
    "  // ============================================================\n"
    "  // CREATE SOCIAL PUBLISHER PRODUCT POST\n"
    "  // ============================================================"
)

loader_code = '''  // ============================================================
  // LOAD MY OFFERS: offers from active/approved memberships only
  // ============================================================
  Future<void> _loadMyOffers() async {
    if (mounted) {
      setState(() => _isLoadingMyOffers = true);
    }

    try {
      final membershipsResult =
          await ApiService.getMyAffiliatePrograms();

      final rawMemberships = membershipsResult['programs'];
      final eligibleProgramIds = <int>{};

      if (rawMemberships is List) {
        for (final item in rawMemberships) {
          if (item is! Map) continue;

          final status = (item['membership_status'] ??
                  item['status'] ??
                  '')
              .toString()
              .toLowerCase();

          if (status != 'active' && status != 'approved') {
            continue;
          }

          final rawId = item['program_id'] ??
              item['affiliate_program_id'] ??
              item['id'];

          final programId = int.tryParse(rawId.toString());
          if (programId != null) {
            eligibleProgramIds.add(programId);
          }
        }
      }

      final matchedOffers = <dynamic>[];

      if (eligibleProgramIds.isNotEmpty) {
        var page = 1;
        var totalPages = 1;

        do {
          final result = await ApiService.getAffiliateOffers(
            page: page,
            limit: _affiliateOffersLoadLimit,
          );

          final rawOffers = result['offers'];
          if (rawOffers is List) {
            for (final offer in rawOffers) {
              if (offer is! Map) continue;

              final rawProgramId = offer['program_id'];
              final programId =
                  int.tryParse(rawProgramId.toString());

              if (programId != null &&
                  eligibleProgramIds.contains(programId)) {
                matchedOffers.add(
                  Map<String, dynamic>.from(offer),
                );
              }
            }
          }

          final parsedPages =
              int.tryParse('${result['total_pages']}');

          totalPages = parsedPages != null && parsedPages > 0
              ? parsedPages
              : 1;

          page++;
        } while (page <= totalPages);
      }

      if (!mounted) return;

      setState(() {
        _myOffers = matchedOffers;
      });
    } catch (e) {
      debugPrint('Failed to load My Offers: $e');

      if (mounted) {
        setState(() => _myOffers = []);
      }
    } finally {
      if (mounted) {
        setState(() => _isLoadingMyOffers = false);
      }
    }
  }

'''

section_marker = (
    "  // ============================================================\n"
    "  // AFFILIATE OFFERS SECTION\n"
    "  // ============================================================\n"
    "\n"
    "  Widget _buildAffiliateOffersSection() {"
)

section_code = '''  // ============================================================
  // MY OFFERS SECTION
  // ============================================================
  Widget _buildMyOffersSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'My Offers',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 12),
        if (_isLoadingMyOffers)
          const Center(child: CircularProgressIndicator())
        else if (_myOffers.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Text(
              "You have no offers from active or approved memberships yet.",
            ),
          )
        else
          ..._myOffers.map((offer) {
            if (offer is! Map) {
              return const SizedBox.shrink();
            }

            return _buildAffiliateOfferCard(
              Map<String, dynamic>.from(offer),
            );
          }),
      ],
    );
  }

'''

# Validate every insertion point before changing anything.
for old, new, label in replacements:
    count = source.count(old)
    if count != 1:
        sys.exit(
            f"STOP: {label} marker must occur exactly once; found {count}. "
            "No changes were written."
        )

for marker, label in [
    (loader_marker, "product-post loader marker"),
    (section_marker, "Affiliate Offers section marker"),
]:
    count = source.count(marker)
    if count != 1:
        sys.exit(
            f"STOP: {label} must occur exactly once; found {count}. "
            "No changes were written."
        )

# Apply the guarded edits in memory.
for old, new, label in replacements:
    source = source.replace(old, new, 1)

source = source.replace(
    loader_marker,
    loader_code + loader_marker,
    1,
)

source = source.replace(
    section_marker,
    section_code + section_marker,
    1,
)

# Final checks before creating a backup or writing the file.
for required in [
    "List<dynamic> _myOffers = [];",
    "Future<void> _loadMyOffers() async",
    "Widget _buildMyOffersSection()",
    "_buildMyOffersSection(),",
]:
    if required not in source:
        sys.exit(
            f"STOP: Final verification failed for {required!r}. "
            "The original file was not changed."
        )

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = path.with_name(
    f"{path.name}.before_my_offers_{stamp}"
)

shutil.copy2(path, backup)
path.write_text(source, encoding="utf-8", newline="")

print("SUCCESS: My Offers patch applied.")
print(f"Backup created: {backup}")
print("Existing Affiliate Offers discovery code was not intentionally changed.")