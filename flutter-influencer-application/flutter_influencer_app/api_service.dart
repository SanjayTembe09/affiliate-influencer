import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String baseUrl = 'http://87.106.214.100:8080';
  static const String socialPublisherBaseUrl =
    'https://affiliate-social.flexhappyhours.com/api/v1';

  // ---------------------------------------------------------
  // TOKEN
  // ---------------------------------------------------------

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('token');
  }

  // ---------------------------------------------------------
  // AUTH HEADERS
  // ---------------------------------------------------------

  static Future<Map<String, String>> _authHeaders() async {
    final token = await getToken();

    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  // ---------------------------------------------------------
  // REGISTER
  // ---------------------------------------------------------

  static Future<Map<String, dynamic>> register({
    required String name,
    required String email,
    required String password,
    required String role,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/register'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'name': name,
        'email': email,
        'password': password,
        'role': role,
      }),
    );

    final data = jsonDecode(response.body);

    if (response.statusCode == 200) {
      return {
        'success': true,
        'data': data,
      };
    }

    return {
      'success': false,
      'error': data['detail'] ??
          data['error'] ??
          data['message'] ??
          'Registration failed',
    };
  }

  // ---------------------------------------------------------
  // LOGIN
  // ---------------------------------------------------------

  static Future<Map<String, dynamic>> authenticate({
    required String email,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/login'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'email': email,
        'password': password,
      }),
    );

    final data = jsonDecode(response.body);

    if (response.statusCode == 200) {
      final prefs = await SharedPreferences.getInstance();

      if (data['token'] != null) {
        await prefs.setString('token', data['token']);
      }

      if (data['user'] != null) {
        await prefs.setString(
          'user',
          jsonEncode(data['user']),
        );
      }

      return {
        'success': true,
        'data': data,
      };
    }

    return {
      'success': false,
      'error': data['detail'] ??
          data['error'] ??
          data['message'] ??
          'Login failed',
    };
  }

  // ---------------------------------------------------------
  // GET CAMPAIGNS - PAGINATED
  // ---------------------------------------------------------

  static Future<Map<String, dynamic>> getCampaigns({
    int page = 1,
    int limit = 10,
  }) async {
    final headers = await _authHeaders();

    final response = await http.get(
      Uri.parse(
        '$baseUrl/api/campaigns/?page=$page&limit=$limit',
      ),
      headers: headers,
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);

      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception('Invalid campaigns response');
    }

    throw Exception(
      'Failed to load campaigns (${response.statusCode})',
    );
  }

  // ---------------------------------------------------------
  // GET MARKETPLACE PRODUCTS - PAGINATED
  // ---------------------------------------------------------

  static Future<Map<String, dynamic>> getMarketplaceProducts({
    int page = 1,
    int limit = 10,
  }) async {
    final headers = await _authHeaders();

    final response = await http.get(
      Uri.parse(
        '$baseUrl/api/marketplace/?page=$page&limit=$limit',
      ),
      headers: headers,
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);

      if (data is Map<String, dynamic>) {
        final products = data['products'];

        if (products is List) {
          return {
            'products': List<dynamic>.from(products),
            'page': data['page'] ?? page,
            'limit': data['limit'] ?? limit,
            'total': data['total'] ?? 0,
            'total_pages': data['total_pages'] ?? 0,
          };
        }
      }

      throw Exception('Invalid marketplace response');
    }

    throw Exception(
      'Failed to load marketplace products '
      '(${response.statusCode})',
    );
  }

  // ---------------------------------------------------------
  // GET MY SUBMISSION LOGS - PAGINATED
  // ---------------------------------------------------------

  static Future<Map<String, dynamic>> getMySubmissionLogs({
    int page = 1,
    int limit = 10,
  }) async {
    final headers = await _authHeaders();

    final response = await http.get(
      Uri.parse(
        '$baseUrl/api/submissions/my-logs?page=$page&limit=$limit',
      ),
      headers: headers,
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);

      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception('Invalid submissions response');
    }

    throw Exception(
      'Failed to load submission history (${response.statusCode})',
    );
  }

  // ---------------------------------------------------------
  // CREATE SOCIAL PUBLISHER PRODUCT POST
  // ---------------------------------------------------------

  static Future<Map<String, dynamic>> createSocialProductPost({
    required int productId,
    String? affiliateUrl,
  }) async {
    final token = await getToken();

    if (token == null || token.isEmpty) {
      throw Exception(
        'Authentication token is missing. Please login again.',
      );
    }

    final body = <String, dynamic>{
      'product_id': productId,
    };

    // Send affiliate URL only when one has been generated.
    // If null/empty, Social Publisher keeps using the
    // normal product URL.
    if (affiliateUrl != null &&
        affiliateUrl.trim().isNotEmpty) {
      body['affiliate_url'] = affiliateUrl.trim();
    }

    final response = await http.post(
      Uri.parse(
        '$socialPublisherBaseUrl/product-post/create',
      ),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode(body),
    );

    final data = jsonDecode(response.body);

    if (response.statusCode == 200) {
      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception(
        'Invalid Social Publisher response.',
      );
    }

    throw Exception(
      data is Map<String, dynamic>
          ? data['detail']?.toString() ??
              data['error']?.toString() ??
              'Social Publisher request failed '
                  '(${response.statusCode})'
          : 'Social Publisher request failed '
              '(${response.statusCode})',
    );
  }

    // ---------------------------------------------------------
  // PUBLISH PRODUCT POST
  // ---------------------------------------------------------

  static Future<Map<String, dynamic>> publishProductPost({
    required int postId,
    required List<String> platforms,
  }) async {
    if (platforms.isEmpty) {
      throw Exception(
        'Please select at least one platform.',
      );
    }

    final token = await getToken();

    if (token == null || token.isEmpty) {
      throw Exception(
        'Authentication token is missing. Please login again.',
      );
    }

    final response = await http.post(
      Uri.parse(
        '$socialPublisherBaseUrl/product-post/$postId/publish',
      ),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode({
        'platforms': platforms,
      }),
    );

    final data = jsonDecode(response.body);

    if (response.statusCode == 200) {
      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception(
        'Invalid Product Post Publish response.',
      );
    }

    throw Exception(
      data is Map<String, dynamic>
          ? data['detail']?.toString() ??
              data['error']?.toString() ??
              data['message']?.toString() ??
              'Unable to publish Product Post '
                  '(${response.statusCode})'
          : 'Unable to publish Product Post '
              '(${response.statusCode})',
    );
  }

  // ---------------------------------------------------------
  // PUBLISH TIKTOK PHOTO
  // ---------------------------------------------------------

  static Future<Map<String, dynamic>> publishTikTokPhoto({
    required String imageUrl,
    required String title,
    String description = '',
    String privacyLevel = 'SELF_ONLY',
    bool disableComment = false,
  }) async {
    if (imageUrl.trim().isEmpty) {
      throw Exception(
        'TikTok publishing requires an image URL.',
      );
    }

    final token = await getToken();

    if (token == null || token.isEmpty) {
      throw Exception(
        'Authentication token is missing. Please login again.',
      );
    }

    final uri = Uri.parse(
      '$socialPublisherBaseUrl/tiktok/direct-post-photo',
    ).replace(
      queryParameters: {
        'image_url': imageUrl,
        'title': title,
        'description': description,
        'privacy_level': privacyLevel,
        'disable_comment':
            disableComment.toString(),
      },
    );

    final response = await http.post(
      uri,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    final data = jsonDecode(response.body);

    if (response.statusCode == 200) {
      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception(
        'Invalid TikTok Photo Publish response.',
      );
    }

    throw Exception(
      data is Map<String, dynamic>
          ? data['detail']?.toString() ??
              data['error']?.toString() ??
              data['message']?.toString() ??
              'Unable to publish Product Post to TikTok '
                  '(${response.statusCode})'
          : 'Unable to publish Product Post to TikTok '
              '(${response.statusCode})',
    );
  }

  // ============================================================
  // AFFILIATE PROGRAMS
  // ============================================================

  // ------------------------------------------------------------
  // GET AFFILIATE PROGRAMS
  // ------------------------------------------------------------

  static Future<Map<String, dynamic>> getAffiliatePrograms({
    String? search,
    String? category,
    String? country,
    String? creatorEligible,
    int page = 1,
    int limit = 20,
  }) async {
    final headers = await _authHeaders();

    final queryParameters = <String, String>{
      'page': page.toString(),
      'limit': limit.toString(),
    };

    if (search != null && search.trim().isNotEmpty) {
      queryParameters['search'] = search.trim();
    }

    if (category != null && category.trim().isNotEmpty) {
      queryParameters['category'] = category.trim();
    }

    if (country != null && country.trim().isNotEmpty) {
      queryParameters['country'] = country.trim();
    }

    if (creatorEligible != null &&
        creatorEligible.trim().isNotEmpty) {
      queryParameters['creator_eligible'] =
          creatorEligible.trim();
    }

    final uri = Uri.parse(
      '$baseUrl/api/v1/affiliate-programs',
    ).replace(
      queryParameters: queryParameters,
    );

    final response = await http.get(
      uri,
      headers: headers,
    );

    final data = jsonDecode(response.body);

    if (response.statusCode == 200) {
      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception(
        'Invalid Affiliate Programs response.',
      );
    }

    throw Exception(
      data is Map<String, dynamic>
          ? data['detail']?.toString() ??
              data['error']?.toString() ??
              data['message']?.toString() ??
              'Unable to load Affiliate Programs '
                  '(${response.statusCode})'
          : 'Unable to load Affiliate Programs '
              '(${response.statusCode})',
    );
  }

  // ------------------------------------------------------------
  // GET SINGLE AFFILIATE PROGRAM
  // ------------------------------------------------------------

  static Future<Map<String, dynamic>> getAffiliateProgram({
    required int programId,
  }) async {
    final headers = await _authHeaders();

    final response = await http.get(
      Uri.parse(
        '$baseUrl/api/v1/affiliate-programs/$programId',
      ),
      headers: headers,
    );

    final data = jsonDecode(response.body);

    if (response.statusCode == 200) {
      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception(
        'Invalid Affiliate Program response.',
      );
    }

    throw Exception(
      data is Map<String, dynamic>
          ? data['detail']?.toString() ??
              data['error']?.toString() ??
              data['message']?.toString() ??
              'Unable to load Affiliate Program '
                  '(${response.statusCode})'
          : 'Unable to load Affiliate Program '
              '(${response.statusCode})',
    );
  }

  // ------------------------------------------------------------
  // JOIN AFFILIATE PROGRAM
  // ------------------------------------------------------------

  static Future<Map<String, dynamic>> joinAffiliateProgram({
    required int programId,
  }) async {
    final headers = await _authHeaders();

    final response = await http.post(
      Uri.parse(
        '$baseUrl/api/v1/affiliate-programs/$programId/join',
      ),
      headers: headers,
    );

    final data = jsonDecode(response.body);

    if (response.statusCode == 200) {
      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception(
        'Invalid Join Affiliate Program response.',
      );
    }

    throw Exception(
      data is Map<String, dynamic>
          ? data['detail']?.toString() ??
              data['error']?.toString() ??
              data['message']?.toString() ??
              'Unable to join Affiliate Program '
                  '(${response.statusCode})'
          : 'Unable to join Affiliate Program '
              '(${response.statusCode})',
    );
  }

  // ------------------------------------------------------------
  // GET MY AFFILIATE PROGRAMS
  // ------------------------------------------------------------

  static Future<Map<String, dynamic>>
      getMyAffiliatePrograms() async {
    final headers = await _authHeaders();

    final response = await http.get(
      Uri.parse(
        '$baseUrl/api/v1/affiliate-programs/my',
      ),
      headers: headers,
    );

    final data = jsonDecode(response.body);

    if (response.statusCode == 200) {
      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception(
        'Invalid My Affiliate Programs response.',
      );
    }

    throw Exception(
      data is Map<String, dynamic>
          ? data['detail']?.toString() ??
              data['error']?.toString() ??
              data['message']?.toString() ??
              'Unable to load My Affiliate Programs '
                  '(${response.statusCode})'
          : 'Unable to load My Affiliate Programs '
              '(${response.statusCode})',
    );
  }

  // ------------------------------------------------------------
  // GET MY SINGLE AFFILIATE PROGRAM MEMBERSHIP
  // ------------------------------------------------------------

  static Future<Map<String, dynamic>>
      getMyAffiliateProgram({
    required int membershipId,
  }) async {
    final headers = await _authHeaders();

    final response = await http.get(
      Uri.parse(
        '$baseUrl/api/v1/affiliate-programs/my/$membershipId',
      ),
      headers: headers,
    );

    final data = jsonDecode(response.body);

    if (response.statusCode == 200) {
      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception(
        'Invalid Affiliate Membership response.',
      );
    }

    throw Exception(
      data is Map<String, dynamic>
          ? data['detail']?.toString() ??
              data['error']?.toString() ??
              data['message']?.toString() ??
              'Unable to load Affiliate Membership '
                  '(${response.statusCode})'
          : 'Unable to load Affiliate Membership '
              '(${response.statusCode})',
    );
  }

  // ------------------------------------------------------------
  // UPDATE MY AFFILIATE PROGRAM MEMBERSHIP
  // ------------------------------------------------------------

  static Future<Map<String, dynamic>>
      updateMyAffiliateProgram({
    required int membershipId,
    String? externalPublisherId,
    String? notes,
  }) async {
    final headers = await _authHeaders();

    final body = <String, dynamic>{};

    if (externalPublisherId != null) {
      body['external_publisher_id'] =
          externalPublisherId;
    }

    if (notes != null) {
      body['notes'] = notes;
    }

    if (body.isEmpty) {
      throw Exception(
        'Please provide at least one field to update.',
      );
    }

    final response = await http.patch(
      Uri.parse(
        '$baseUrl/api/v1/affiliate-programs/my/$membershipId',
      ),
      headers: headers,
      body: jsonEncode(body),
    );

    final data = jsonDecode(response.body);

    if (response.statusCode == 200) {
      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception(
        'Invalid Affiliate Membership update response.',
      );
    }

    throw Exception(
      data is Map<String, dynamic>
          ? data['detail']?.toString() ??
              data['error']?.toString() ??
              data['message']?.toString() ??
              'Unable to update Affiliate Membership '
                  '(${response.statusCode})'
          : 'Unable to update Affiliate Membership '
              '(${response.statusCode})',
    );
  }

  // ------------------------------------------------------------
  // CREATE AFFILIATE LINK
  // ------------------------------------------------------------

  static Future<Map<String, dynamic>> createAffiliateLink({
    required int offerId,
  }) async {
    final headers = await _authHeaders();

    final response = await http.post(
      Uri.parse(
        '$baseUrl/api/v1/affiliate-links',
      ),
      headers: headers,
      body: jsonEncode({
        'offer_id': offerId,
      }),
    );

    final data = jsonDecode(response.body);

    if (response.statusCode == 200) {
      if (data is Map<String, dynamic>) {
        return data;
      }

      throw Exception(
        'Invalid Affiliate Link response.',
      );
    }

    throw Exception(
      data is Map<String, dynamic>
          ? data['detail']?.toString() ??
              data['error']?.toString() ??
              data['message']?.toString() ??
              'Unable to create Affiliate Link '
                  '(${response.statusCode})'
          : 'Unable to create Affiliate Link '
              '(${response.statusCode})',
    );
  }


  // ---------------------------------------------------------
  // LOGOUT
  // ---------------------------------------------------------

  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();

    await prefs.remove('token');
    await prefs.remove('user');
  }
}