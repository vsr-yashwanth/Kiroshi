import 'package:shared_preferences/shared_preferences.dart';

class Endpoints {
  // Default to host PC local Wi-Fi IP for testing on physical devices
  static const String defaultBaseUrl = 'http://192.168.1.9:8000/api/v1';
  static String _baseUrl = defaultBaseUrl;

  static String get baseUrl => _baseUrl;

  static Future<void> init() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _baseUrl = prefs.getString('server_base_url') ?? defaultBaseUrl;
    } catch (_) {
      _baseUrl = defaultBaseUrl;
    }
  }

  static Future<void> setBaseUrl(String url) async {
    _baseUrl = url.trim().replaceAll(RegExp(r'/+$'), '');
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('server_base_url', _baseUrl);
    } catch (_) {}
  }

  static String get register => '$baseUrl/auth/register';
  static String get login => '$baseUrl/auth/login';
  static String get logout => '$baseUrl/auth/logout';
  static String get me => '$baseUrl/auth/me';

  static String get touristMe => '$baseUrl/tourists/me';
  static String get trips => '$baseUrl/trips';
  static String tripById(String id) => '$baseUrl/trips/$id';
  static String startTrip(String id) => '$baseUrl/trips/$id/start';
  static String stopTrip(String id) => '$baseUrl/trips/$id/stop';

  static String get location => '$baseUrl/location';
  static String get zones => '$baseUrl/zones';
  static String get sos => '$baseUrl/incidents/sos';
}
