from pathlib import Path
import re

path = Path(r"lib\influencer_dashboard.dart")
text = path.read_text(encoding="utf-8")

start_marker = "  Widget _buildAffiliateOffersSection() {"
end_marker = "  Widget _buildAffiliateOfferCard("

start = text.find(start_marker)
if start == -1:
    raise SystemExit("ERROR: _buildAffiliateOffersSection() was not found.")

end = text.find(end_marker, start)
if end == -1:
    raise SystemExit(
        "ERROR: _buildAffiliateOfferCard() was not found after "
        "_buildAffiliateOffersSection()."
    )

old_section = text[start:end]

new_section = r'''  Widget _buildAffiliateOffersSection() {
    if (_selectedAffiliateProgramId == null) {
      return Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          _buildSectionTitle(
            'Affiliate Offers',
            '$_affiliateProgramTotal',
          ),

          const SizedBox(height: 12),

          if (_isLoadingAffiliatePrograms)
            const Padding(
              padding: EdgeInsets.symmetric(
                vertical: 30,
              ),
              child: Center(
                child: CircularProgressIndicator(),
              ),
            )
          else if (_affiliatePrograms.isEmpty)
            _buildEmptyCard(
              icon: Icons.business_outlined,
              message: 'No Affiliate Programs available.',
            )
          else
            ..._affiliatePrograms.map(
              (program) {
                return Padding(
                  padding: const EdgeInsets.only(
                    bottom: 12,
                  ),
                  child: _buildAffiliateProgramCard(
                    program,
                  ),
                );
              },
            ),

          if (_affiliateProgramTotalPages > 1)
            _buildPaginationControls(
              currentPage: _affiliateProgramPage,
              totalPages: _affiliateProgramTotalPages,
              isLoading: _isChangingAffiliateProgramPage,
              onPrevious: () {
                _changeAffiliateProgramPage(
                  _affiliateProgramPage - 1,
                );
              },
              onNext: () {
                _changeAffiliateProgramPage(
                  _affiliateProgramPage + 1,
                );
              },
            ),
        ],
      );
    }

    final selectedProgramId =
        _selectedAffiliateProgramId!;

    final selectedProgram = _affiliatePrograms
        .where(
          (program) =>
              program is Map &&
              int.tryParse(
                    program['id']?.toString() ?? '',
                  ) ==
                  selectedProgramId,
        )
        .cast<dynamic>()
        .toList();

    final offers =
        _affiliateOffersByProgram[selectedProgramId] ??
            <dynamic>[];

    String programName =
        'Affiliate Program';

    String brandName = '';

    if (selectedProgram.isNotEmpty &&
        selectedProgram.first is Map) {
      final program =
          Map<String, dynamic>.from(
        selectedProgram.first as Map,
      );

      programName =
          program['program_name']?.toString().trim().isNotEmpty ==
                  true
              ? program['program_name'].toString()
              : 'Affiliate Program';

      brandName =
          program['brand_name']?.toString() ?? '';
    } else if (offers.isNotEmpty &&
        offers.first is Map) {
      final firstOffer =
          Map<String, dynamic>.from(
        offers.first as Map,
      );

      programName =
          firstOffer['program_name']?.toString().trim().isNotEmpty ==
                  true
              ? firstOffer['program_name'].toString()
              : 'Affiliate Program';

      brandName =
          firstOffer['program_brand_name']?.toString() ??
              firstOffer['brand_name']?.toString() ??
              '';
    }

    return Column(
      crossAxisAlignment:
          CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: _buildSectionTitle(
                'Affiliate Offers',
                '${offers.length}',
              ),
            ),
          ],
        ),

        const SizedBox(height: 8),

        OutlinedButton.icon(
          onPressed: () {
            setState(() {
              _selectedAffiliateProgramId = null;
            });
          },
          icon: const Icon(
            Icons.arrow_back,
          ),
          label: const Text(
            'Back to Affiliate Programs',
          ),
        ),

        const SizedBox(height: 12),

        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,
              children: [
                if (brandName.isNotEmpty)
                  Text(
                    brandName,
                    style:
                        Theme.of(context)
                            .textTheme
                            .labelLarge
                            ?.copyWith(
                              fontWeight:
                                  FontWeight.w600,
                            ),
                  ),

                const SizedBox(height: 4),

                Text(
                  programName,
                  style:
                      Theme.of(context)
                          .textTheme
                          .titleMedium
                          ?.copyWith(
                            fontWeight:
                                FontWeight.bold,
                          ),
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 12),

        if (_isLoadingAffiliateOffers)
          const Padding(
            padding: EdgeInsets.symmetric(
              vertical: 30,
            ),
            child: Center(
              child: CircularProgressIndicator(),
            ),
          )
        else if (offers.isEmpty)
          _buildEmptyCard(
            icon: Icons.local_offer_outlined,
            message:
                'No offers available for this program.',
          )
        else
          ...offers.map(
            (offer) {
              if (offer is! Map) {
                return const SizedBox.shrink();
              }

              return Padding(
                padding: const EdgeInsets.only(
                  bottom: 12,
                ),
                child: _buildAffiliateOfferCard(
                  Map<String, dynamic>.from(offer),
                ),
              );
            },
          ),
      ],
    );
  }

'''

text = text[:start] + new_section + text[end:]

path.write_text(text, encoding="utf-8")

print("SUCCESS: Affiliate Offers section replaced.")
print("Old section length:", len(old_section))
print("New section length:", len(new_section))
