class MobileAppException implements Exception {
  final String message;
  final int? statusCode;

  MobileAppException(this.message, [this.statusCode]);

  @override
  String toString() => message;
}

class NetworkException extends MobileAppException {
  NetworkException(String message) : super(message);
}

class AuthException extends MobileAppException {
  AuthException(String message, [int? statusCode]) : super(message, statusCode);
}
