import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:location/location.dart';
import '../storage/token_storage.dart';
import '../constants/endpoints.dart';
import '../../domain/models/location_tracking_state.dart';

class LocationTrackingService {
  final TokenStorage _tokenStorage;
  final http.Client _httpClient;
  final Location _location = Location();

  StreamSubscription<LocationData>? _positionStreamSub;
  String? _activeTripId;

  LocationTrackingService({
    TokenStorage? tokenStorage,
    http.Client? httpClient,
  })  : _tokenStorage = tokenStorage ?? TokenStorage(),
        _httpClient = httpClient ?? http.Client();

  Future<TrackingStatus> checkAndRequestPermissions() async {
    bool serviceEnabled = await _location.serviceEnabled();
    if (!serviceEnabled) {
      serviceEnabled = await _location.requestService();
      if (!serviceEnabled) {
        return TrackingStatus.locationUnavailable;
      }
    }

    PermissionStatus permission = await _location.hasPermission();
    if (permission == PermissionStatus.denied) {
      permission = await _location.requestPermission();
      if (permission == PermissionStatus.denied) {
        return TrackingStatus.permissionDenied;
      }
    }

    if (permission == PermissionStatus.deniedForever) {
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

    await _location.changeSettings(
      accuracy: LocationAccuracy.HIGH,
      distanceFilter: 10, // Ingest when moved by at least 10 meters (battery-conscious)
    );

    _positionStreamSub = _location.onLocationChanged.listen(
      (LocationData position) async {
        final point = LocationPoint(
          latitude: position.latitude ?? 0.0,
          longitude: position.longitude ?? 0.0,
          accuracy: position.accuracy ?? 0.0,
          altitude: position.altitude ?? 0.0,
          speed: position.speed ?? 0.0,
          heading: position.heading ?? 0.0,
          recordedAt: position.time != null
              ? DateTime.fromMillisecondsSinceEpoch(position.time!.toInt())
              : DateTime.now(),
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
