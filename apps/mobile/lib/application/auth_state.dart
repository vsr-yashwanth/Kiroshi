import 'package:flutter/material.dart';
import '../core/constants/endpoints.dart';
import '../core/network/api_client.dart';
import '../core/storage/token_storage.dart';
import '../domain/models/user.dart';
import '../domain/models/tourist_profile.dart';

enum AuthStatus { initial, authenticating, authenticated, unauthenticated, error }

class AuthState extends ChangeNotifier {
  final ApiClient _apiClient = ApiClient();
  final TokenStorage _tokenStorage = TokenStorage();

  AuthStatus _status = AuthStatus.initial;
  UserModel? _user;
  TouristProfileModel? _profile;
  String? _errorMessage;

  AuthStatus get status => _status;
  UserModel? get user => _user;
  TouristProfileModel? get profile => _profile;
  String? get errorMessage => _errorMessage;
  bool get isAuthenticated => _status == AuthStatus.authenticated;

  Future<void> initAuth() async {
    final token = await _tokenStorage.getToken();
    if (token == null) {
      _status = AuthStatus.unauthenticated;
      notifyListeners();
      return;
    }

    try {
      final userJson = await _apiClient.get(Endpoints.me);
      _user = UserModel.fromJson(userJson);
      await loadProfile();
      _status = AuthStatus.authenticated;
    } catch (e) {
      await _tokenStorage.clearToken();
      _status = AuthStatus.unauthenticated;
    }
    notifyListeners();
  }

  Future<bool> login(String email, String password) async {
    _status = AuthStatus.authenticating;
    _errorMessage = null;
    notifyListeners();

    try {
      final res = await _apiClient.post(
        Endpoints.login,
        body: {'username': email, 'password': password},
        requireAuth: false,
      );

      final token = res['access_token'] as String;
      await _tokenStorage.saveToken(token);
      _user = UserModel.fromJson(res['user']);
      await loadProfile();

      _status = AuthStatus.authenticated;
      notifyListeners();
      return true;
    } catch (e) {
      _status = AuthStatus.error;
      _errorMessage = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<bool> register({
    required String email,
    required String password,
    required String fullName,
    String? phoneNumber,
  }) async {
    _status = AuthStatus.authenticating;
    _errorMessage = null;
    notifyListeners();

    try {
      await _apiClient.post(
        Endpoints.register,
        body: {
          'email': email,
          'password': password,
          'full_name': fullName,
          'phone_number': phoneNumber,
          'role': 'TOURIST',
        },
        requireAuth: false,
      );
      // Automatically login upon successful registration
      return await login(email, password);
    } catch (e) {
      _status = AuthStatus.error;
      _errorMessage = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<void> loadProfile() async {
    try {
      final res = await _apiClient.get(Endpoints.touristMe);
      _profile = TouristProfileModel.fromJson(res);
      notifyListeners();
    } catch (_) {}
  }

  Future<bool> updateProfile(TouristProfileModel updated) async {
    try {
      final res = await _apiClient.put(Endpoints.touristMe, body: updated.toJson());
      _profile = TouristProfileModel.fromJson(res);
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    try {
      await _apiClient.post(Endpoints.logout);
    } catch (_) {}
    await _tokenStorage.clearToken();
    _user = null;
    _profile = null;
    _status = AuthStatus.unauthenticated;
    notifyListeners();
  }
}
