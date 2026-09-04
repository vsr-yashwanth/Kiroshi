import 'dart:convert';
import 'package:http/http.dart' as http;
import '../errors/app_exception.dart';
import '../storage/token_storage.dart';

class ApiClient {
  final TokenStorage _tokenStorage = TokenStorage();

  Future<Map<String, String>> _getHeaders({bool requireAuth = true}) async {
    final headers = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (requireAuth) {
      final token = await _tokenStorage.getToken();
      if (token != null) {
        headers['Authorization'] = 'Bearer $token';
      }
    }
    return headers;
  }

  dynamic _processResponse(http.Response response) {
    final dynamic body = response.body.isNotEmpty ? jsonDecode(response.body) : {};
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return body;
    }

    final String errorMessage = (body is Map && body.containsKey('detail'))
        ? body['detail'].toString()
        : 'Request failed with status code ${response.statusCode}';

    if (response.statusCode == 401) {
      throw AuthException(errorMessage, 401);
    }
    throw MobileAppException(errorMessage, response.statusCode);
  }

  static const Duration _timeout = Duration(seconds: 12);

  Future<dynamic> get(String url, {bool requireAuth = true}) async {
    try {
      final headers = await _getHeaders(requireAuth: requireAuth);
      final response = await http
          .get(Uri.parse(url), headers: headers)
          .timeout(_timeout);
      return _processResponse(response);
    } catch (e) {
      if (e is MobileAppException) rethrow;
      throw NetworkException(
        'Could not connect to server ($url). Please verify that the backend is running and reachable on your Wi-Fi network.',
      );
    }
  }

  Future<dynamic> post(String url, {dynamic body, bool requireAuth = true}) async {
    try {
      final headers = await _getHeaders(requireAuth: requireAuth);
      final response = await http
          .post(
            Uri.parse(url),
            headers: headers,
            body: body != null ? jsonEncode(body) : null,
          )
          .timeout(_timeout);
      return _processResponse(response);
    } catch (e) {
      if (e is MobileAppException) rethrow;
      throw NetworkException(
        'Could not connect to server ($url). Please verify that the backend is running and reachable on your Wi-Fi network.',
      );
    }
  }

  Future<dynamic> put(String url, {dynamic body, bool requireAuth = true}) async {
    try {
      final headers = await _getHeaders(requireAuth: requireAuth);
      final response = await http
          .put(
            Uri.parse(url),
            headers: headers,
            body: body != null ? jsonEncode(body) : null,
          )
          .timeout(_timeout);
      return _processResponse(response);
    } catch (e) {
      if (e is MobileAppException) rethrow;
      throw NetworkException(
        'Could not connect to server ($url). Please verify that the backend is running and reachable on your Wi-Fi network.',
      );
    }
  }
}
