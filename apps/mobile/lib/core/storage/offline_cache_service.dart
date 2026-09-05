import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../../domain/models/trip.dart';

class OfflineCacheService {
  static const String _keyActiveTrip = 'kiroshi_cache_active_trip';
  static const String _keyLastLocation = 'kiroshi_cache_last_location';
  static const String _keyEmergencyContacts = 'kiroshi_cache_emergency_contacts';

  final SharedPreferences? _prefsInstance;

  OfflineCacheService({SharedPreferences? prefs}) : _prefsInstance = prefs;

  Future<SharedPreferences> _getPrefs() async {
    return _prefsInstance ?? await SharedPreferences.getInstance();
  }

  // Active Trip Cache (REQUIRED OFFLINE)
  Future<void> cacheActiveTrip(TripModel trip) async {
    final prefs = await _getPrefs();
    final jsonStr = jsonEncode(trip.toJson());
    await prefs.setString(_keyActiveTrip, jsonStr);
  }

  Future<TripModel?> getCachedActiveTrip() async {
    final prefs = await _getPrefs();
    final raw = prefs.getString(_keyActiveTrip);
    if (raw == null || raw.isEmpty) return null;
    try {
      final map = jsonDecode(raw) as Map<String, dynamic>;
      return TripModel.fromJson(map);
    } catch (_) {
      return null;
    }
  }

  Future<void> clearActiveTrip() async {
    final prefs = await _getPrefs();
    await prefs.remove(_keyActiveTrip);
  }

  // Last Known Location Cache (REQUIRED OFFLINE - single latest fix only)
  Future<void> cacheLastLocation({
    required double latitude,
    required double longitude,
    required double accuracy,
    DateTime? recordedAt,
  }) async {
    final prefs = await _getPrefs();
    final data = {
      'latitude': latitude,
      'longitude': longitude,
      'accuracy': accuracy,
      'recorded_at': (recordedAt ?? DateTime.now()).toIso8601String(),
    };
    await prefs.setString(_keyLastLocation, jsonEncode(data));
  }

  Future<Map<String, dynamic>?> getLastLocation() async {
    final prefs = await _getPrefs();
    final raw = prefs.getString(_keyLastLocation);
    if (raw == null || raw.isEmpty) return null;
    try {
      return jsonDecode(raw) as Map<String, dynamic>;
    } catch (_) {
      return null;
    }
  }

  // Emergency Contacts Cache (REQUIRED OFFLINE)
  Future<void> cacheEmergencyContacts(List<Map<String, String>> contacts) async {
    final prefs = await _getPrefs();
    await prefs.setString(_keyEmergencyContacts, jsonEncode(contacts));
  }

  Future<List<Map<String, String>>> getEmergencyContacts() async {
    final prefs = await _getPrefs();
    final raw = prefs.getString(_keyEmergencyContacts);
    if (raw == null || raw.isEmpty) {
      // Default safety fallback contacts if none saved
      return [
        {'name': 'National Emergency Dispatch', 'number': '112 / 911'},
        {'name': 'Tourist Police Hotline', 'number': '+1-800-KIROSHI'},
      ];
    }
    try {
      final List<dynamic> list = jsonDecode(raw) as List<dynamic>;
      return list.map((item) => Map<String, String>.from(item as Map)).toList();
    } catch (_) {
      return [];
    }
  }

  Future<void> clearAllCache() async {
    final prefs = await _getPrefs();
    await prefs.remove(_keyActiveTrip);
    await prefs.remove(_keyLastLocation);
    await prefs.remove(_keyEmergencyContacts);
  }
}
