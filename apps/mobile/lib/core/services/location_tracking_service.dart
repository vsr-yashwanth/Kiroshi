import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:geolocator/geolocator.dart';
import '../storage/token_storage.dart';
import '../constants/endpoints.dart';
import '../../domain/models/location_tracking_state.dart';

class LocationTrackingService {
  final TokenStorage _tokenStorage;
  final http.Client _httpClient;

  StreamSubscription<Position>? _positionStreamSub;
  String? _activeTripId;

  LocationTrackingService({
    TokenStorage? tokenStorage,
    http.Client? httpClient,
  })  : _tokenStorage = tokenStorage ?? TokenStorage(),
        _httpClient = httpClient ?? http.Client();

  Future<TrackingStatus> checkAndRequestPermissions() async {
    final serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      return TrackingStatus.locationUnavailable;
    }

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        return TrackingStatus.permissionDenied;
      }
    }

    if (permission == LocationPermission.deniedForever) {
      return TrackingStatus.permissionDenied;
    }

    return TrackingStatus.trackingDisabled;
  }

  Future<void> startTracking({
    required String tripId,
    required void Function(LocationPoint point) onLocationCaptured,
    required void Function(String error) onError,
  }) async {
    _activeTripId = tripId;
    await stopTracking();

    const locationSettings = LocationSettings(
      accuracy: LocationAccuracy.high,
      distanceFilter: 10, // Ingest when moved by at least 10 meters (battery-conscious)
    );

    _positionStreamSub = Geolocator.getPositionStream(
      locationSettings: locationSettings,
    ).listen(
      (Position position) async {
        final point = LocationPoint(
          latitude: position.latitude,
          longitude: position.longitude,
          accuracy: position.accuracy,
          altitude: position.altitude,
          speed: position.speed,
          heading: position.heading,
          recordedAt: position.timestamp,
        );

        onLocationCaptured(point);

        // Transmit coordinates to backend
        try {
          await _transmitLocation(point);
        } catch (e) {
          onError('Failed to sync coordinates to server: $e');
        }
      },
      onError: (err) {
        onError('GPS hardware error: $err');
      },
    );
  }

  Future<void> _transmitLocation(LocationPoint point) async {
    if (_activeTripId == null) return;

    final token = await _tokenStorage.getToken();
    if (token == null) {
      throw Exception('Unauthenticated: No active JWT token');
    }

    final url = Uri.parse(Endpoints.location);
    final response = await _httpClient.post(
      url,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode(point.toJson(_activeTripId!)),
    );

    if (response.statusCode != 201) {
      throw Exception('Ingestion rejected with status ${response.statusCode}: ${response.body}');
    }
  }

  Future<void> stopTracking() async {
    await _positionStreamSub?.cancel();
    _positionStreamSub = null;
    _activeTripId = null;
  }
}
