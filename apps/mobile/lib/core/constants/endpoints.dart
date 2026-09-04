class Endpoints {
  // Configured for local development
  // In Android emulator, 10.0.2.2 maps to host localhost; for iOS simulator, localhost:8000
  static const String baseUrl = 'http://10.0.2.2:8000/api/v1';

  static const String register = '$baseUrl/auth/register';
  static const String login = '$baseUrl/auth/login';
  static const String logout = '$baseUrl/auth/logout';
  static const String me = '$baseUrl/auth/me';

  static const String touristMe = '$baseUrl/tourists/me';
  static const String trips = '$baseUrl/trips';
  static String tripById(String id) => '$baseUrl/trips/$id';
  static String startTrip(String id) => '$baseUrl/trips/$id/start';
  static String stopTrip(String id) => '$baseUrl/trips/$id/stop';

  static const String location = '$baseUrl/location';
  static const String zones = '$baseUrl/zones';
}

