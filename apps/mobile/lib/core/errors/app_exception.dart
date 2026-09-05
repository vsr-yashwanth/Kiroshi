class MobileAppException implements Exception {
  final String message;
  final int? statusCode;

  MobileAppException(this.message, [this.statusCode]);

  @override
  String toString() => message;
}

class NetworkException extends MobileAppException {
  NetworkException(super.message);
}

class AuthException extends MobileAppException {
  AuthException(super.message, [super.statusCode]);
}
