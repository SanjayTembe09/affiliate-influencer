import 'package:flutter/material.dart';

import 'api_service.dart';

class ProductPostScreen extends StatefulWidget {
  final Map<String, dynamic> product;
  final String? affiliateUrl;

  const ProductPostScreen({
    super.key,
    required this.product,
    this.affiliateUrl,
  });

  @override
  State<ProductPostScreen> createState() =>
      _ProductPostScreenState();
}

class _ProductPostScreenState
    extends State<ProductPostScreen> {
  bool _creatingPost = false;
  bool _publishing = false;

  Map<String, dynamic>? _productPost;

  bool _publishFacebook = false;
  bool _publishInstagram = false;
  bool _publishInstagramStory = false;
  bool _publishTikTok = false;

  String? _errorMessage;

  // =========================================================
  // CREATE PRODUCT POST
  // =========================================================

  Future<void> _createProductPost() async {
    final productId = widget.product['id'];

    if (productId == null) {
      _showMessage(
        'Selected product has no product ID.',
      );
      return;
    }

    setState(() {
      _creatingPost = true;
      _errorMessage = null;
    });

    try {
      final result =
          await ApiService.createSocialProductPost(
        productId: int.parse(
          productId.toString(),
        ),
        affiliateUrl: widget.affiliateUrl,
      );

      setState(() {
        _errorMessage =
            'DEBUG affiliateUrl: ${widget.affiliateUrl}';
      });

      if (!mounted) return;

      if (result['success'] == true) {
        final post = result['post'];

        if (post is Map) {
          setState(() {
            _productPost =
                Map<String, dynamic>.from(post);
            _creatingPost = false;
          });

          _showMessage(
            'Product Post created successfully. '
            'Post ID: ${post['id'] ?? 'unknown'}',
          );
        } else {
          throw Exception(
            'Product Post data is missing.',
          );
        }
      } else {
        throw Exception(
          result['error']?.toString() ??
              result['message']?.toString() ??
              'Unable to create Product Post.',
        );
      }
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _creatingPost = false;
        _errorMessage = e.toString();
      });

      _showMessage(
        'Could not create Product Post.',
      );
    }
  }

  // =========================================================
  // PUBLISH PRODUCT POST
  // =========================================================

  Future<void> _publishProductPost() async {
    final post = _productPost;

    if (post == null) {
      _showMessage(
        'Please create the Product Post first.',
      );
      return;
    }

    final platforms = <String>[];

    if (_publishFacebook) {
      platforms.add('facebook');
    }

    if (_publishInstagram) {
      platforms.add('instagram');
    }

    if (_publishInstagramStory) {
      platforms.add('instagram_story');
    }

    if (_publishTikTok) {
      platforms.add('tiktok');
    }

    if (platforms.isEmpty) {
      _showMessage(
        'Please select at least one platform.',
      );
      return;
    }

    setState(() {
      _publishing = true;
      _errorMessage = null;
    });

    try {
      final postId = post['id'];

      if (postId == null) {
        throw Exception(
          'Product Post ID is missing.',
        );
      }

      final results = <Map<String, dynamic>>[];

      // =====================================================
      // Facebook / Instagram / Instagram Story
      // =====================================================

      final regularPlatforms = <String>[];

      if (_publishFacebook) {
        regularPlatforms.add('facebook');
      }

      if (_publishInstagram) {
        regularPlatforms.add('instagram');
      }

      if (_publishInstagramStory) {
        regularPlatforms.add('instagram_story');
      }

      if (regularPlatforms.isNotEmpty) {
        try {
          final result =
              await ApiService.publishProductPost(
            postId: int.parse(
              postId.toString(),
            ),
            platforms: regularPlatforms,
          );

          final regularResults =
              result['results'];

          if (regularResults is List) {
            for (final item in regularResults) {
              if (item is Map) {
                results.add(
                  Map<String, dynamic>.from(item),
                );
              }
            }
          }
        } catch (e) {
          for (final platform
              in regularPlatforms) {
            results.add({
              'platform': platform,
              'success': false,
              'status': 'FAILED',
              'error_message': e.toString(),
            });
          }
        }
      }

      // =====================================================
      // TikTok
      // =====================================================

      if (_publishTikTok) {
        try {
          final imageUrl =
              post['tiktok_jpg_url']
                  ?.toString();

          if (imageUrl == null ||
              imageUrl.isEmpty) {
            throw Exception(
              'TikTok JPG image is not available.',
            );
          }

          final title =
              post['title']?.toString() ?? '';

          final caption =
              post['caption']?.toString() ?? '';

          final tiktokResult =
              await ApiService.publishTikTokPhoto(
            imageUrl: imageUrl,
            title: title,
            description: caption,
            privacyLevel: 'SELF_ONLY',
            disableComment: false,
          );

          final tiktokData =
              tiktokResult['tiktok'];

          String status = 'UNKNOWN';
          bool success = false;

          if (tiktokData is Map) {
            status =
                tiktokData['status']
                        ?.toString() ??
                    'UNKNOWN';

            success =
                tiktokData['completed'] == true ||
                    status == 'PUBLISH_COMPLETE';
          }

          results.add({
            'platform': 'tiktok',
            'success': success,
            'status': status,
            'publish_id':
                tiktokData is Map
                    ? tiktokData['publish_id']
                    : null,
            'error_message': success
                ? null
                : tiktokData is Map
                    ? tiktokData['message']
                    : 'TikTok publishing failed.',
          });
        } catch (e) {
          results.add({
            'platform': 'tiktok',
            'success': false,
            'status': 'FAILED',
            'error_message': e.toString(),
          });
        }
      }

      if (!mounted) return;

      setState(() {
        _publishing = false;
      });

      int successful = 0;
      int failed = 0;

      for (final item in results) {
        if (item['success'] == true) {
          successful++;
        } else {
          failed++;
        }
      }

      _showPublishResult({
        'success': failed == 0,
        'summary': {
          'successful': successful,
          'failed': failed,
        },
        'results': results,
      });
    } catch (e) {
      if (!mounted) return;

      setState(() {
        _publishing = false;
        _errorMessage = e.toString();
      });

      _showMessage(
        'Publishing failed.',
      );
    }
  }

  // =========================================================
  // PUBLISH RESULT
  // =========================================================

  void _showPublishResult(
    Map<String, dynamic> result,
  ) {
    final summary = result['summary'];

    final successful = summary is Map
        ? summary['successful'] ?? 0
        : 0;

    final failed = summary is Map
        ? summary['failed'] ?? 0
        : 0;

    final results = result['results'];

    showDialog(
      context: context,
      builder: (_) {
        return AlertDialog(
          title: const Text(
            'Publication Result',
          ),
          content: SingleChildScrollView(
            child: Column(
              crossAxisAlignment:
                  CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'Successful: $successful',
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  'Failed: $failed',
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                  ),
                ),

                const SizedBox(height: 16),

                if (results is List)
                  ...results.map((item) {
                    if (item is! Map) {
                      return const SizedBox();
                    }

                    final platform =
                        item['platform']
                                ?.toString() ??
                            '';

                    final success =
                        item['success'] == true;

                    final status =
                        item['status']
                                ?.toString() ??
                            '';

                    final error =
                        item['error_message']
                            ?.toString();

                    return Padding(
                      padding:
                          const EdgeInsets.only(
                        bottom: 12,
                      ),
                      child: Row(
                        crossAxisAlignment:
                            CrossAxisAlignment.start,
                        children: [
                          Icon(
                            success
                                ? Icons.check_circle
                                : Icons.error,
                            color: success
                                ? Colors.green
                                : Colors.red,
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment:
                                  CrossAxisAlignment
                                      .start,
                              children: [
                                Text(
                                  platform,
                                  style:
                                      const TextStyle(
                                    fontWeight:
                                        FontWeight.bold,
                                  ),
                                ),
                                if (status.isNotEmpty)
                                  Text(status),
                                if (error != null &&
                                    error.isNotEmpty)
                                  Text(
                                    error,
                                    style:
                                        const TextStyle(
                                      color: Colors.red,
                                    ),
                                  ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    );
                  }),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(context);
              },
              child: const Text('OK'),
            ),
          ],
        );
      },
    );
  }

  // =========================================================
  // MESSAGE
  // =========================================================

  void _showMessage(String message) {
    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        behavior:
            SnackBarBehavior.floating,
      ),
    );
  }

  // =========================================================
  // BUILD
  // =========================================================

  @override
  Widget build(BuildContext context) {
    final product = widget.product;

    final title =
        product['title']?.toString() ??
            'Untitled Product';

    final description =
        product['description']?.toString() ??
            '';

    final imageUrl =
        product['image_url']?.toString() ??
            product['imageUrl']?.toString() ??
            '';

    final price =
        product['price']?.toString() ?? '0';

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Product Post',
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(
            16,
            16,
            16,
            32,
          ),
          child: Column(
            crossAxisAlignment:
                CrossAxisAlignment.start,
            children: [
              _buildProductPreview(
                title: title,
                description: description,
                imageUrl: imageUrl,
                price: price,
              ),

              const SizedBox(height: 20),

              if (_productPost == null)
                _buildCreatePostButton(),

              if (_productPost != null) ...[
                _buildPostPreview(),

                const SizedBox(height: 24),

                _buildPlatformSelection(),

                const SizedBox(height: 20),

                _buildPublishButton(),
              ],

              if (_errorMessage != null) ...[
                const SizedBox(height: 20),
                _buildError(),
              ],
            ],
          ),
        ),
      ),
    );
  }

  // =========================================================
  // PRODUCT PREVIEW
  // =========================================================

  Widget _buildProductPreview({
    required String title,
    required String description,
    required String imageUrl,
    required String price,
  }) {
    return Card(
      elevation: 3,
      child: Padding(
        padding:
            const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment:
              CrossAxisAlignment.start,
          children: [
            const Text(
              'Selected Product',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 16),

            Center(
              child: _buildLargeImage(
                imageUrl,
                height: 260,
              ),
            ),

            const SizedBox(height: 16),

            Text(
              title,
              style: const TextStyle(
                fontSize: 19,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 8),

            Text(
              'Price: ₹$price',
              style: const TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.bold,
              ),
            ),

            if (description.isNotEmpty) ...[
              const SizedBox(height: 10),
              Text(
                description,
                maxLines: 6,
                overflow:
                    TextOverflow.ellipsis,
              ),
            ],
          ],
        ),
      ),
    );
  }

  // =========================================================
  // CREATE POST BUTTON
  // =========================================================

  Widget _buildCreatePostButton() {
    return Container(
      width: double.infinity,
      padding:
          const EdgeInsets.all(16),
      decoration: BoxDecoration(
        borderRadius:
            BorderRadius.circular(14),
        border: Border.all(
          color: Theme.of(context)
              .colorScheme
              .primary,
          width: 1.5,
        ),
      ),
      child: Column(
        children: [
          const Text(
            'Ready to create your Product Post?',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),

          const SizedBox(height: 12),

          _buildActionButton(
            label: _creatingPost
                ? 'Creating Product Post...'
                : 'Create Product Post',
            icon: Icons.auto_awesome,
            onPressed: _creatingPost
                ? null
                : _createProductPost,
          ),
        ],
      ),
    );
  }

  // =========================================================
  // PRODUCT POST PREVIEW
  // =========================================================

  Widget _buildPostPreview() {
    final post = _productPost!;

    final title =
        post['title']?.toString() ?? '';

    final caption =
        post['caption']?.toString() ?? '';

    final imageUrl =
        post['image_url']?.toString() ?? '';

    final productUrl =
        post['product_url']?.toString() ?? '';

    return Card(
      elevation: 3,
      child: Padding(
        padding:
            const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment:
              CrossAxisAlignment.start,
          children: [
            const Text(
              'Product Post Preview',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 16),

            Center(
              child: _buildLargeImage(
                imageUrl,
                height: 300,
              ),
            ),

            const SizedBox(height: 16),

            Text(
              title,
              style: const TextStyle(
                fontSize: 19,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 10),

            Text(caption),

            const SizedBox(height: 14),

            const Text(
              'Product URL',
              style: TextStyle(
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 4),

            if (productUrl.isNotEmpty)
              SelectableText(
                productUrl,
                style: const TextStyle(
                  color: Colors.blue,
                ),
              )
            else
              const Text(
                'No product URL available.',
                style: TextStyle(
                  color: Colors.grey,
                ),
              ),
          ],
        ),
      ),
    );
  }

  // =========================================================
  // PLATFORM SELECTION
  // =========================================================

  Widget _buildPlatformSelection() {
    return Card(
      elevation: 3,
      child: Padding(
        padding:
            const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment:
              CrossAxisAlignment.start,
          children: [
            const Text(
              'Publish To',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 4),

            const Text(
              'Select the platforms where you want to publish this product.',
              style: TextStyle(
                color: Colors.grey,
              ),
            ),

            const SizedBox(height: 12),

            _buildPlatformTile(
              title: 'Facebook',
              icon: Icons.facebook,
              value: _publishFacebook,
              onChanged: (value) {
                setState(() {
                  _publishFacebook =
                      value ?? false;
                });
              },
            ),

            _buildPlatformTile(
              title: 'Instagram Feed',
              icon: Icons.camera_alt,
              value: _publishInstagram,
              onChanged: (value) {
                setState(() {
                  _publishInstagram =
                      value ?? false;
                });
              },
            ),

            _buildPlatformTile(
              title: 'Instagram Story',
              icon: Icons.auto_stories,
              subtitle:
                  'Product link will be retained for Story publishing.',
              value: _publishInstagramStory,
              onChanged: (value) {
                setState(() {
                  _publishInstagramStory =
                      value ?? false;
                });
              },
            ),

            _buildPlatformTile(
              title: 'TikTok',
              icon: Icons.music_note,
              subtitle:
                  'Publish the Product Post image directly to TikTok.',
              value: _publishTikTok,
              onChanged: (value) {
                setState(() {
                  _publishTikTok =
                      value ?? false;
                });
              },
            ),
          ],
        ),
      ),
    );
  }

  // =========================================================
  // PLATFORM TILE
  // =========================================================

  Widget _buildPlatformTile({
    required String title,
    required IconData icon,
    required bool value,
    required ValueChanged<bool?>
        onChanged,
    String? subtitle,
  }) {
    return Container(
      margin:
          const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        border: Border.all(
          color: value
              ? Theme.of(context)
                  .colorScheme
                  .primary
              : Colors.grey.shade300,
        ),
        borderRadius:
            BorderRadius.circular(10),
        color: value
            ? Theme.of(context)
                .colorScheme
                .primary
                .withValues(alpha: 0.06)
            : null,
      ),
      child: CheckboxListTile(
        contentPadding:
            const EdgeInsets.symmetric(
          horizontal: 12,
          vertical: 4,
        ),
        secondary: Icon(icon),
        title: Text(
          title,
          style: const TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
        subtitle: subtitle != null
            ? Text(subtitle)
            : null,
        value: value,
        onChanged: onChanged,
      ),
    );
  }

  // =========================================================
  // PUBLISH BUTTON
  // =========================================================

  Widget _buildPublishButton() {
    final selectedCount =
        (_publishFacebook ? 1 : 0) +
            (_publishInstagram ? 1 : 0) +
            (_publishInstagramStory
                ? 1
                : 0) +
            (_publishTikTok ? 1 : 0);

    return Container(
      width: double.infinity,
      padding:
          const EdgeInsets.all(16),
      decoration: BoxDecoration(
        borderRadius:
            BorderRadius.circular(14),
        border: Border.all(
          color: Theme.of(context)
              .colorScheme
              .primary,
          width: 1.5,
        ),
      ),
      child: Column(
        children: [
          Text(
            selectedCount == 0
                ? 'No platform selected'
                : '$selectedCount platform${selectedCount == 1 ? '' : 's'} selected',
            style: TextStyle(
              fontWeight:
                  FontWeight.bold,
              color: selectedCount == 0
                  ? Colors.red
                  : Colors.green,
            ),
          ),

          const SizedBox(height: 12),

          _buildActionButton(
            label: _publishing
                ? 'Publishing...'
                : 'Publish Product Post',
            icon: Icons.publish,
            onPressed: _publishing
                ? null
                : _publishProductPost,
          ),
        ],
      ),
    );
  }

  // =========================================================
  // ACTION BUTTON
  // =========================================================

  Widget _buildActionButton({
    required String label,
    required IconData icon,
    required VoidCallback?
        onPressed,
  }) {
    return SizedBox(
      width: double.infinity,
      height: 56,
      child: ElevatedButton.icon(
        onPressed: onPressed,
        icon: icon == Icons.auto_awesome &&
                _creatingPost
            ? const SizedBox(
                width: 20,
                height: 20,
                child:
                    CircularProgressIndicator(
                  strokeWidth: 2,
                ),
              )
            : icon == Icons.publish &&
                    _publishing
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child:
                        CircularProgressIndicator(
                      strokeWidth: 2,
                    ),
                  )
                : Icon(icon),
        label: Text(label),
        style:
            ElevatedButton.styleFrom(
          minimumSize:
              const Size(double.infinity, 56),
          padding:
              const EdgeInsets.symmetric(
            horizontal: 20,
            vertical: 14,
          ),
          textStyle:
              const TextStyle(
            fontSize: 16,
            fontWeight:
                FontWeight.bold,
          ),
          shape:
              RoundedRectangleBorder(
            borderRadius:
                BorderRadius.circular(10),
          ),
        ),
      ),
    );
  }

  // =========================================================
  // ERROR
  // =========================================================

  Widget _buildError() {
    final message =
        _errorMessage ?? '';

    if (message.isEmpty) {
      return const SizedBox();
    }

    return Card(
      color: Colors.red.shade50,
      child: Padding(
        padding:
            const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment:
              CrossAxisAlignment.start,
          children: [
            const Icon(
              Icons.error,
              color: Colors.red,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                message,
                style:
                    const TextStyle(
                  color: Colors.red,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // =========================================================
  // LARGE IMAGE
  // =========================================================

  Widget _buildLargeImage(
    String? url, {
    double height = 240,
  }) {
    if (url == null ||
        url.isEmpty) {
      return SizedBox(
        height: height,
        child: const Center(
          child: Icon(
            Icons.image_not_supported,
            size: 60,
          ),
        ),
      );
    }

    return ClipRRect(
      borderRadius:
          BorderRadius.circular(12),
      child: Container(
        width: double.infinity,
        height: height,
        color: Colors.grey.shade100,
        child: Image.network(
          url,
          width: double.infinity,
          height: height,
          fit: BoxFit.contain,
          errorBuilder:
              (_, __, ___) {
            return const Center(
              child: Icon(
                Icons.broken_image,
                size: 60,
              ),
            );
          },
        ),
      ),
    );
  }
}