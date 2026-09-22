import 'package:flutter/material.dart';

import 'api_service.dart';

class MarketplaceScreen extends StatefulWidget {
  const MarketplaceScreen({super.key});

  @override
  State<MarketplaceScreen> createState() =>
      _MarketplaceScreenState();
}

class _MarketplaceScreenState
    extends State<MarketplaceScreen> {
  bool _isLoading = true;
  String? _errorMessage;

  List<dynamic> _products = [];

  @override
  void initState() {
    super.initState();
    _loadProducts();
  }

  // ============================================================
  // LOAD MARKETPLACE PRODUCTS
  // ============================================================

    Future<void> _loadProducts() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final result =
          await ApiService.getMarketplaceProducts();

      if (!mounted) return;

      setState(() {
        _products =
            List<dynamic>.from(result['products'] ?? []);
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _errorMessage =
            'Failed to load marketplace products: $e';
        _isLoading = false;
      });
    }
  }

  // ============================================================
  // FORMAT CURRENCY
  // ============================================================

  String _formatCurrency(double value) {
    return '₹${value.toStringAsFixed(2)}';
  }

  // ============================================================
  // CALCULATE PAYOUT
  // ============================================================

  double _calculatePayout(dynamic product) {
    if (product is! Map) {
      return 0;
    }

    final price =
        double.tryParse(
              product['price']?.toString() ?? '0',
            ) ??
            0;

    final commissionPercentage =
        double.tryParse(
              product['commission_percentage']
                      ?.toString() ??
                  '0',
            ) ??
            0;

    return price *
        commissionPercentage /
        100;
  }

  // ============================================================
  // SELECT PRODUCT
  // ============================================================

  void _selectProduct(dynamic product) {
    if (product is! Map) {
      return;
    }

    Navigator.pop(
      context,
      Map<String, dynamic>.from(product),
    );
  }

  // ============================================================
  // MAIN BUILD
  // ============================================================

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Marketplace',
          style: TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
      body: RefreshIndicator(
        onRefresh: _loadProducts,
        child: _buildBody(),
      ),
    );
  }

  // ============================================================
  // BODY
  // ============================================================

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    if (_errorMessage != null) {
      return ListView(
        physics:
            const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(24),
        children: [
          const SizedBox(height: 100),

          const Icon(
            Icons.error_outline,
            size: 64,
            color: Colors.redAccent,
          ),

          const SizedBox(height: 16),

          Text(
            _errorMessage!,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: Colors.redAccent,
              fontSize: 16,
            ),
          ),

          const SizedBox(height: 20),

          Center(
            child: ElevatedButton.icon(
              onPressed: _loadProducts,
              icon: const Icon(Icons.refresh),
              label: const Text('Try Again'),
            ),
          ),
        ],
      );
    }

    if (_products.isEmpty) {
      return ListView(
        physics:
            const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(24),
        children: [
          const SizedBox(height: 100),

          const Icon(
            Icons.storefront_outlined,
            size: 64,
            color: Colors.white38,
          ),

          const SizedBox(height: 16),

          const Text(
            'No marketplace products are currently available.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white60,
              fontSize: 16,
            ),
          ),
        ],
      );
    }

    return ListView.builder(
      physics:
          const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(16),
      itemCount: _products.length,
      itemBuilder: (context, index) {
        return Padding(
          padding:
              const EdgeInsets.only(bottom: 16),
          child: _buildProductCard(
            _products[index],
          ),
        );
      },
    );
  }

  // ============================================================
  // PRODUCT CARD
  // ============================================================

  Widget _buildProductCard(dynamic product) {
    if (product is! Map) {
      return const SizedBox.shrink();
    }

    final title =
        product['title']?.toString() ??
            'Untitled Product';

    final description =
        product['description']?.toString() ?? '';

    final imageUrl =
        product['image_url']?.toString() ?? '';

    final price =
        double.tryParse(
              product['price']?.toString() ?? '0',
            ) ??
            0;

    final commissionPercentage =
        double.tryParse(
              product['commission_percentage']
                      ?.toString() ??
                  '0',
            ) ??
            0;

    final payout =
        _calculatePayout(product);

    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: Colors.white10,
        ),
      ),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          // ------------------------------------------------------
          // PRODUCT IMAGE
          // ------------------------------------------------------

          if (imageUrl.isNotEmpty)
            ClipRRect(
              borderRadius:
                  const BorderRadius.vertical(
                top: Radius.circular(18),
              ),
              child: AspectRatio(
                aspectRatio: 16 / 9,
                child: Image.network(
                  imageUrl,
                  fit: BoxFit.contain,
                  errorBuilder:
                      (
                        context,
                        error,
                        stackTrace,
                      ) {
                    return Container(
                      color: const Color(
                        0xFF1E293B,
                      ),
                      child: const Center(
                        child: Icon(
                          Icons
                              .image_not_supported_outlined,
                          size: 50,
                          color: Colors.white38,
                        ),
                      ),
                    );
                  },
                  loadingBuilder:
                      (
                        context,
                        child,
                        loadingProgress,
                      ) {
                    if (loadingProgress ==
                        null) {
                      return child;
                    }

                    return const Center(
                      child:
                          CircularProgressIndicator(),
                    );
                  },
                ),
              ),
            )
          else
            Container(
              height: 200,
              decoration: const BoxDecoration(
                color: Color(0xFF1E293B),
                borderRadius:
                    BorderRadius.vertical(
                  top: Radius.circular(18),
                ),
              ),
              child: const Center(
                child: Icon(
                  Icons.image_outlined,
                  size: 50,
                  color: Colors.white38,
                ),
              ),
            ),

          // ------------------------------------------------------
          // PRODUCT INFORMATION
          // ------------------------------------------------------

          Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),

                if (description.isNotEmpty) ...[
                  const SizedBox(height: 10),
                  Text(
                    description,
                    maxLines: 4,
                    overflow:
                        TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Colors.white70,
                      height: 1.4,
                    ),
                  ),
                ],

                const SizedBox(height: 16),

                // ------------------------------------------------
                // PRICE / COMMISSION
                // ------------------------------------------------

                Row(
                  children: [
                    Expanded(
                      child: _buildInfoItem(
                        title: 'Price',
                        value:
                            _formatCurrency(price),
                      ),
                    ),
                    Expanded(
                      child: _buildInfoItem(
                        title: 'Commission',
                        value:
                            '${commissionPercentage.toStringAsFixed(2)}%',
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 14),

                Container(
                  padding:
                      const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: Colors.greenAccent
                        .withValues(alpha: 0.08),
                    borderRadius:
                        BorderRadius.circular(12),
                    border: Border.all(
                      color: Colors.greenAccent
                          .withValues(alpha: 0.2),
                    ),
                  ),
                  child: Row(
                    children: [
                      const Icon(
                        Icons
                            .account_balance_wallet_outlined,
                        color:
                            Colors.greenAccent,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment:
                              CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Your Estimated Payout',
                              style: TextStyle(
                                color:
                                    Colors.white60,
                                fontSize: 12,
                              ),
                            ),
                            const SizedBox(height: 3),
                            Text(
                              _formatCurrency(
                                payout,
                              ),
                              style:
                                  const TextStyle(
                                color:
                                    Colors.greenAccent,
                                fontSize: 18,
                                fontWeight:
                                    FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 18),

                // ------------------------------------------------
                // SELECT PRODUCT
                // ------------------------------------------------

                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: () =>
                        _selectProduct(product),
                    icon: const Icon(
                      Icons
                          .check_circle_outline,
                    ),
                    label: const Text(
                      'Select Product',
                    ),
                    style:
                        ElevatedButton.styleFrom(
                      padding:
                          const EdgeInsets
                              .symmetric(
                        vertical: 14,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ============================================================
  // INFO ITEM
  // ============================================================

  Widget _buildInfoItem({
    required String title,
    required String value,
  }) {
    return Column(
      crossAxisAlignment:
          CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            color: Colors.white54,
            fontSize: 12,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ),
        ),
      ],
    );
  }
}