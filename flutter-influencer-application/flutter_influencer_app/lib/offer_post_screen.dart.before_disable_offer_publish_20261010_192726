import 'package:flutter/material.dart';

import 'api_service.dart';

class OfferPostScreen extends StatefulWidget {
  final Map<String, dynamic> offer;
  final String affiliateUrl;

  const OfferPostScreen({
    super.key,
    required this.offer,
    required this.affiliateUrl,
  });

  @override
  State<OfferPostScreen> createState() =>
      _OfferPostScreenState();
}

class _OfferPostScreenState
    extends State<OfferPostScreen> {
  bool _creatingPost = false;
  bool _publishing = false;

  Map<String, dynamic>? _offerPost;

  bool _publishFacebook = false;
  bool _publishInstagram = false;
  bool _publishInstagramStory = false;
  bool _publishTikTok = false;

  String? _errorMessage;

  Future<void> _createOfferPost() async {
    final int? offerId = int.tryParse(
      widget.offer['offer_id']?.toString() ?? '',
    );

    if (offerId == null) {
      setState(() {
        _errorMessage = 'Invalid Affiliate Offer ID.';
      });
      return;
    }

    if (widget.affiliateUrl.trim().isEmpty) {
      setState(() {
        _errorMessage =
            'Affiliate URL is required to create the Offer Post.';
      });
      return;
    }

    setState(() {
      _creatingPost = true;
      _errorMessage = null;
    });

    try {
      final result =
          await ApiService.createSocialOfferPost(
        offerId: offerId,
        brandName:
            widget.offer['brand_name']?.toString(),
        title:
            widget.offer['title']?.toString() ??
                'Affiliate Offer',
        description:
            widget.offer['description']?.toString(),
        imageUrl:
            widget.offer['image_url']?.toString(),
        commissionType:
            widget.offer['commission_type']?.toString(),
        commissionRate: double.tryParse(
          widget.offer['commission_rate']?.toString() ??
              '',
        ),
        currency:
            widget.offer['currency']?.toString(),
        affiliateUrl: widget.affiliateUrl,
      );

      final post = result['post'];

      if (post is! Map) {
        throw Exception(
          'Offer Post was created but no post data was returned.',
        );
      }

      setState(() {
        _offerPost =
            Map<String, dynamic>.from(post);
        _creatingPost = false;
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'Affiliate Offer Post created successfully.',
            ),
          ),
        );
      }
    } catch (e) {
      setState(() {
        _creatingPost = false;
        _errorMessage = e.toString();
      });
    }
  }

  Future<void> _publishOfferPost() async {
    if (_offerPost == null) {
      setState(() {
        _errorMessage =
            'Please create the Offer Post first.';
      });
      return;
    }

    final int? postId = int.tryParse(
      _offerPost!['id']?.toString() ?? '',
    );

    if (postId == null) {
      setState(() {
        _errorMessage = 'Invalid Offer Post ID.';
      });
      return;
    }

    final List<String> platforms = [];

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
      setState(() {
        _errorMessage =
            'Please select at least one platform.';
      });
      return;
    }

    setState(() {
      _publishing = true;
      _errorMessage = null;
    });

    try {
      final result =
          await ApiService.publishOfferPost(
        postId: postId,
        platforms: platforms,
      );

      setState(() {
        _publishing = false;
      });

      if (mounted) {
        _showPublishResult(result);
      }
    } catch (e) {
      setState(() {
        _publishing = false;
        _errorMessage = e.toString();
      });
    }
  }

  void _showPublishResult(
    Map<String, dynamic> result,
  ) {
    final summary = result['summary'];

    int successful = 0;
    int failed = 0;

    if (summary is Map) {
      successful = int.tryParse(
            summary['successful']?.toString() ?? '',
          ) ??
          0;

      failed = int.tryParse(
            summary['failed']?.toString() ?? '',
          ) ??
          0;
    }

    final results = result['results'];

    showDialog<void>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text(
            'Offer Post Publication',
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment:
                  CrossAxisAlignment.start,
              children: [
                Text(
                  'Successful: $successful',
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Failed: $failed',
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                if (results is List) ...[
                  const SizedBox(height: 16),
                  ...results.map(
                    (item) {
                      if (item is! Map) {
                        return const SizedBox.shrink();
                      }

                      final platform =
                          item['platform']
                                  ?.toString() ??
                              'Platform';

                      final status =
                          item['status']
                                  ?.toString() ??
                              '';

                      final error =
                          item['error']?.toString();

                      return Padding(
                        padding:
                            const EdgeInsets.only(
                          bottom: 10,
                        ),
                        child: Column(
                          crossAxisAlignment:
                              CrossAxisAlignment.start,
                          children: [
                            Text(
                              platform,
                              style:
                                  const TextStyle(
                                fontWeight:
                                    FontWeight.bold,
                              ),
                            ),
                            Text(
                              'Status: $status',
                            ),
                            if (error != null &&
                                error.isNotEmpty)
                              Text(
                                'Error: $error',
                                style:
                                    const TextStyle(
                                  color: Colors.red,
                                  fontSize: 12,
                                ),
                              ),
                          ],
                        ),
                      );
                    },
                  ),
                ],
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(dialogContext).pop();
              },
              child: const Text('Close'),
            ),
          ],
        );
      },
    );
  }

  Widget _buildOfferPreview() {
    final String title =
        widget.offer['title']?.toString() ??
            'Affiliate Offer';

    final String description =
        widget.offer['description']?.toString() ??
            '';

    final String brandName =
        widget.offer['brand_name']?.toString() ??
            'Unknown Brand';

    final String imageUrl =
        widget.offer['image_url']?.toString() ??
            '';

    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment:
              CrossAxisAlignment.start,
          children: [
            if (imageUrl.isNotEmpty)
              ClipRRect(
                borderRadius:
                    BorderRadius.circular(12),
                child: Image.network(
                  imageUrl,
                  width: double.infinity,
                  height: 220,
                  fit: BoxFit.cover,
                  errorBuilder:
                      (
                        context,
                        error,
                        stackTrace,
                      ) {
                    return Container(
                      height: 220,
                      width: double.infinity,
                      alignment:
                          Alignment.center,
                      color:
                          Colors.grey.shade200,
                      child: const Icon(
                        Icons.image_not_supported,
                        size: 48,
                      ),
                    );
                  },
                ),
              ),
            const SizedBox(height: 14),
            Text(
              brandName,
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey.shade700,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 5),
            Text(
              title,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            if (description.isNotEmpty) ...[
              const SizedBox(height: 10),
              Text(
                description,
                style: const TextStyle(
                  fontSize: 14,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildPostPreview() {
    final post = _offerPost!;

    final String title =
        post['title']?.toString() ??
            'Affiliate Offer';

    final String caption =
        post['caption']?.toString() ??
            '';

    final String imageUrl =
        post['image_url']?.toString() ??
            '';

    final String affiliateUrl =
        post['affiliate_url']?.toString() ??
            widget.affiliateUrl;

    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment:
              CrossAxisAlignment.start,
          children: [
            const Text(
              'Generated Offer Post',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 14),
            if (imageUrl.isNotEmpty)
              ClipRRect(
                borderRadius:
                    BorderRadius.circular(12),
                child: Image.network(
                  imageUrl,
                  width: double.infinity,
                  height: 300,
                  fit: BoxFit.cover,
                  errorBuilder:
                      (
                        context,
                        error,
                        stackTrace,
                      ) {
                    return Container(
                      height: 300,
                      width: double.infinity,
                      alignment:
                          Alignment.center,
                      color:
                          Colors.grey.shade200,
                      child: const Icon(
                        Icons.image_not_supported,
                        size: 48,
                      ),
                    );
                  },
                ),
              ),
            const SizedBox(height: 14),
            Text(
              title,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            const Text(
              'Caption',
              style: TextStyle(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 6),
            SelectableText(
              caption,
              style: const TextStyle(
                fontSize: 14,
              ),
            ),
            const SizedBox(height: 14),
            const Text(
              'Affiliate Link',
              style: TextStyle(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 6),
            SelectableText(
              affiliateUrl,
              style: const TextStyle(
                fontSize: 13,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPlatformTile({
    required String title,
    required String subtitle,
    required IconData icon,
    required bool value,
    required ValueChanged<bool?> onChanged,
  }) {
    return CheckboxListTile(
      value: value,
      onChanged: _publishing
          ? null
          : onChanged,
      secondary: Icon(icon),
      title: Text(title),
      subtitle: Text(subtitle),
      contentPadding:
          const EdgeInsets.symmetric(
        horizontal: 8,
      ),
    );
  }

  Widget _buildPlatformSelection() {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment:
              CrossAxisAlignment.start,
          children: [
            const Padding(
              padding: EdgeInsets.all(8),
              child: Text(
                'Publish To',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            _buildPlatformTile(
              title: 'Facebook',
              subtitle: 'Publish the Offer Post',
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
              title: 'Instagram',
              subtitle: 'Publish to Instagram Feed',
              icon: Icons.camera_alt_outlined,
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
              subtitle:
                  'Publish Offer with affiliate link',
              icon: Icons.auto_stories_outlined,
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
              subtitle:
                  'Publish Offer image directly',
              icon: Icons.music_note,
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

  Widget _buildActionButton({
    required String label,
    required VoidCallback? onPressed,
    required bool loading,
    required IconData icon,
  }) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton.icon(
        onPressed: onPressed,
        icon: loading
            ? const SizedBox(
                width: 18,
                height: 18,
                child:
                    CircularProgressIndicator(
                  strokeWidth: 2,
                ),
              )
            : Icon(icon),
        label: Text(
          loading ? 'Please wait...' : label,
        ),
        style: ElevatedButton.styleFrom(
          padding:
              const EdgeInsets.symmetric(
            vertical: 14,
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final bool postCreated =
        _offerPost != null;

    final int selectedCount = [
      _publishFacebook,
      _publishInstagram,
      _publishInstagramStory,
      _publishTikTok,
    ].where((value) => value).length;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Offer Post'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment:
                CrossAxisAlignment.start,
            children: [
              if (!postCreated)
                _buildOfferPreview(),

              if (!postCreated) ...[
                const SizedBox(height: 20),
                _buildActionButton(
                  label: 'Create Offer Post',
                  icon: Icons.auto_awesome,
                  loading: _creatingPost,
                  onPressed: _creatingPost
                      ? null
                      : _createOfferPost,
                ),
              ],

              if (postCreated) ...[
                _buildPostPreview(),
                const SizedBox(height: 20),
                _buildPlatformSelection(),
                const SizedBox(height: 20),
                _buildActionButton(
                  label:
                      selectedCount == 0
                          ? 'Select Platforms'
                          : 'Publish Offer Post '
                              '($selectedCount)',
                  icon: Icons.publish,
                  loading: _publishing,
                  onPressed:
                      _publishing ||
                              selectedCount == 0
                          ? null
                          : _publishOfferPost,
                ),
              ],

              if (_errorMessage != null) ...[
                const SizedBox(height: 16),
                Container(
                  width: double.infinity,
                  padding:
                      const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.red
                        .withValues(alpha: 0.08),
                    borderRadius:
                        BorderRadius.circular(10),
                    border: Border.all(
                      color: Colors.red
                          .withValues(alpha: 0.25),
                    ),
                  ),
                  child: Text(
                    _errorMessage!,
                    style: const TextStyle(
                      color: Colors.red,
                      fontSize: 13,
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}