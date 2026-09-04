import 'dart:math';
import 'package:location/location.dart';
import '../network/api_client.dart';
import '../constants/endpoints.dart';

class SosService {
  final ApiClient _apiClient;
  final Location _location = Location();

  SosService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  /// Generates a unique idempotency key for this SOS interaction.
  String generateIdempotencyKey() {
    final rand = Random().nextInt(1000000);
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    return 'sos-$timestamp-$rand';
  }

  /// Triggers an emergency SOS incident.
  /// Decoupled from AI, Risk Engine, and external dependencies.
  /// If GPS coordinates cannot be captured, SOS STILL PROCEEDS.
  Future<Map<String, dynamic>> triggerSos({
    String? tripId,
    String? notes,
    String? idempotencyKey,
  }) async {
    final key = idempotencyKey ?? generateIdempotencyKey();

    double? latitude;
    double? longitude;
    double? accuracy;

    try {
      // Attempt location capture with quick 4-second timeout to avoid delaying SOS
      final locData = await _location.getLocation().timeout(
        const Duration(seconds: 4),
      );
      latitude = locData.latitude;
      longitude = locData.longitude;
      accuracy = locData.accuracy;
    } catch (_) {
      // GPS failure MUST NEVER prevent SOS creation (Phase 8 & 10)
      latitude = null;
      longitude = null;
      accuracy = null;
    }

    final payload = {
      if (tripId != null) 'trip_id': tripId,
      'latitude': latitude,
      'longitude': longitude,
      'accuracy': accuracy,
      if (notes != null && notes.isNotEmpty) 'notes': notes,
      'idempotency_key': key,
    };

    final response = await _apiClient.post(
      Endpoints.sos,
      body: payload,
      requireAuth: true,
    );

    return response as Map<String, dynamic>;
  }
}
