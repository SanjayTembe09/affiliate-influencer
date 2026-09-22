import 'package:flutter/material.dart';
import 'api_service.dart';
import 'product_post_screen.dart';

class MarketplaceProductDetailsScreen extends StatefulWidget {
  final Map<String, dynamic> product;

  const MarketplaceProductDetailsScreen({
    super.key,
    required this.product,
  });

  @override
  State<MarketplaceProductDetailsScreen> createState() =>
      _MarketplaceProductDetailsScreenState();
}

class _MarketplaceProductDetailsScreenState
    extends State<MarketplaceProductDetailsScreen> {
  bool _isGeneratingAffiliateLink = false;
  String? _affiliateUrl;

  Map<String, dynamic> get product => widget.product;

  String _stringValue(String key, [String fallback = '']) {
    final value = product[key];
    if (value == null) return fallback;
    return value.toString();
  }

  double _doubleValue(String key) {
    return double.tryParse(
          product[key]?.toString() ?? '0',
        ) ??
        0;
  }

  bool _boolValue(String key) {
    final value = product[key];

    return value == true ||
        value == 1 ||
        value?.toString().toLowerCase() == 'true' ||
        value?.toString() == '1';
  }

  int? _intValue(String key) {
    final value = product[key];

    if (value == null) {
      return null;
    }

    if (value is int) {
      return value;
    }

    return int.tryParse(value.toString());
  }

  Future<void> _generateAffiliateLink() async {
    final offerId = _intValue('affiliate_offer_id');

    if (offerId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Affiliate offer is not available for this product.',
          ),
        ),
      );
      return;
    }

    setState(() {
      _isGeneratingAffiliateLink = true;
    });

    try {
      final response = await ApiService.createAffiliateLink(
        offerId: offerId,
      );

      final link = response['link'];

      if (link is Map<String, dynamic>) {
        final affiliateUrl =
            link['affiliate_url']?.toString();

        if (affiliateUrl != null &&
            affiliateUrl.isNotEmpty) {
          setState(() {
            _affiliateUrl = affiliateUrl;
          });

          if (!mounted) return;

          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text(
                'Affiliate link generated successfully.',
              ),
            ),
          );

          return;
        }
      }

      throw Exception(
        'Affiliate link was not returned by the server.',
      );
    } catch (e) {
      if (!mounted) return;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            e.toString().replaceFirst(
              'Exception: ',
              '',
            ),
          ),
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isGeneratingAffiliateLink = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final title = _stringValue(
      'title',
      'Untitled Product',
    );

    final description = _stringValue(
      'description',
      'No description available.',
    );

    final imageUrl = _stringValue('image_url');

    final price = _doubleValue('price');

    final commission = _doubleValue(
      'commission_percentage',
    );

    final affiliateProgramName = _stringValue(
      'affiliate_program_name',
      'Not assigned',
    );

    final membershipStatus = _stringValue(
      'creator_membership_status',
      'Not available',
    );

    final canGenerateAffiliateLink = _boolValue(
      'can_generate_affiliate_link',
    );

    return Scaffold(
      appBar: AppBar(
        title: const Text('Product Details'),
      ),
      backgroundColor: const Color(0xFF020617),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ==================================================
              // PRODUCT IMAGE
              // ==================================================
              Container(
                width: double.infinity,
                height: 240,
                decoration: BoxDecoration(
                  color: const Color(0xFF0F172A),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: Colors.white10,
                  ),
                ),
                child: imageUrl.isNotEmpty
                    ? ClipRRect(
                        borderRadius:
                            BorderRadius.circular(16),
                        child: Image.network(
                          imageUrl,
                          fit: BoxFit.contain,
                          errorBuilder:
                              (
                            context,
                            error,
                            stackTrace,
                          ) {
                            return const Center(
                              child: Icon(
                                Icons
                                    .image_not_supported_outlined,
                                size: 56,
                                color: Colors.white38,
                              ),
                            );
                          },
                        ),
                      )
                    : const Center(
                        child: Icon(
                          Icons.image_outlined,
                          size: 56,
                          color: Colors.white38,
                        ),
                      ),
              ),

              const SizedBox(height: 20),

              // ==================================================
              // PRODUCT NAME
              // ==================================================
              Text(
                title,
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),

              const SizedBox(height: 12),

              // ==================================================
              // DESCRIPTION
              // ==================================================
              Text(
                description,
                style: const TextStyle(
                  fontSize: 15,
                  height: 1.5,
                  color: Colors.white70,
                ),
              ),

              const SizedBox(height: 24),

              // ==================================================
              // PRICE / COMMISSION
              // ==================================================
              Row(
                children: [
                  Expanded(
                    child: _InfoCard(
                      label: 'Price',
                      value:
                          '₹${price.toStringAsFixed(2)}',
                      icon: Icons.currency_rupee,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _InfoCard(
                      label: 'Commission',
                      value:
                          '${commission.toStringAsFixed(2)}%',
                      icon: Icons.payments_outlined,
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 20),

              // ==================================================
              // AFFILIATE PROGRAM
              // ==================================================
              _DetailRow(
                icon: Icons.business_outlined,
                label: 'Affiliate Program',
                value: affiliateProgramName,
              ),

              const SizedBox(height: 12),

              // ==================================================
              // MEMBERSHIP STATUS
              // ==================================================
              _DetailRow(
                icon: Icons.card_membership_outlined,
                label: 'Membership Status',
                value: membershipStatus,
              ),

              const SizedBox(height: 12),

              // ==================================================
              // AFFILIATE LINK AVAILABILITY
              // ==================================================
              _DetailRow(
                icon: canGenerateAffiliateLink
                    ? Icons.link
                    : Icons.link_off,
                label: 'Affiliate Link',
                value: _affiliateUrl != null
                    ? 'Generated'
                    : canGenerateAffiliateLink
                        ? 'Available'
                        : 'Not available',
                valueColor: _affiliateUrl != null
                    ? Colors.greenAccent
                    : canGenerateAffiliateLink
                        ? Colors.greenAccent
                        : Colors.white54,
              ),

              // ==================================================
              // GENERATED AFFILIATE URL
              // ==================================================
              if (_affiliateUrl != null) ...[
                const SizedBox(height: 12),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0F172A),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: Colors.greenAccent
                          .withValues(alpha: 0.35),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment:
                        CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Your Affiliate Link',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: Colors.white70,
                        ),
                      ),
                      const SizedBox(height: 8),
                      SelectableText(
                        _affiliateUrl!,
                        style: const TextStyle(
                          fontSize: 14,
                          color: Colors.greenAccent,
                          height: 1.4,
                        ),
                      ),
                    ],
                  ),
                ),
              ],

              const SizedBox(height: 28),

              // ==================================================
              // GENERATE AFFILIATE LINK
              // ==================================================
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed:
                      canGenerateAffiliateLink &&
                              !_isGeneratingAffiliateLink
                          ? _generateAffiliateLink
                          : null,
                  icon: _isGeneratingAffiliateLink
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child:
                              CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.link),
                  label: Text(
                    _isGeneratingAffiliateLink
                        ? 'Generating...'
                        : _affiliateUrl != null
                            ? 'Generate Another Link'
                            : 'Generate Affiliate Link',
                  ),
                  style: ElevatedButton.styleFrom(
                    padding:
                        const EdgeInsets.symmetric(
                      vertical: 15,
                    ),
                  ),
                ),
              ),

              const SizedBox(height: 12),

              // ==================================================
              // PROMOTE PRODUCT
              // ==================================================
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: _affiliateUrl == null
                    ? null
                  : () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => ProductPostScreen(
                          product: product,
                          affiliateUrl: _affiliateUrl,
                        ),
                      ),
                    );
                  },
                  icon: const Icon(
                    Icons.campaign_outlined,
                  ),
                  label: const Text(
                    'Promote Product',
                  ),
                  style: OutlinedButton.styleFrom(
                    padding:
                        const EdgeInsets.symmetric(
                      vertical: 15,
                    ),
                    foregroundColor: Colors.white,
                    side: const BorderSide(
                      color: Colors.white24,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ============================================================
// INFO CARD
// ============================================================

class _InfoCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;

  const _InfoCard({
    required this.label,
    required this.value,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: Colors.white10,
        ),
      ),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Icon(
            icon,
            size: 20,
            color: Colors.white54,
          ),
          const SizedBox(height: 8),
          Text(
            label,
            style: const TextStyle(
              fontSize: 13,
              color: Colors.white54,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
        ],
      ),
    );
  }
}

// ============================================================
// DETAIL ROW
// ============================================================

class _DetailRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color? valueColor;

  const _DetailRow({
    required this.label,
    required this.value,
    required this.icon,
    this.valueColor,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: Colors.white10,
        ),
      ),
      child: Row(
        children: [
          Icon(
            icon,
            color: Colors.white54,
            size: 22,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              label,
              style: const TextStyle(
                fontSize: 14,
                color: Colors.white60,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.right,
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: valueColor ?? Colors.white,
              ),
            ),
          ),
        ],
      ),
    );
  }
}