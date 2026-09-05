import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:http/http.dart' as http;
import 'package:location/location.dart';
import '../../domain/models/offline_event.dart';
import '../storage/token_storage.dart';
import '../storage/offline_event_queue.dart';
import '../storage/offline_cache_service.dart';
import '../constants/endpoints.dart';
import '../../domain/models/location_tracking_state.dart';

class LocationTrackingService {
  final TokenStorage _tokenStorage;
  final OfflineEventQueue _queue;
  final OfflineCacheService _cache;
  final http.Client _httpClient;
  final Location _location = Location();

  StreamSubscription<LocationData>? _positionStreamSub;
  String? _activeTripId;

  LocationTrackingService({
    TokenStorage? tokenStorage,
    OfflineEventQueue? queue,
    OfflineCacheService? cache,
    http.Client? httpClient,
  })  : _tokenStorage = tokenStorage ?? TokenStorage(),
        _queue = queue ?? OfflineEventQueue(),
        _cache = cache ?? OfflineCacheService(),
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

    // Explicitly check for granted or limited permission
    if (permission == PermissionStatus.granted || permission == PermissionStatus.grantedLimited) {
      return TrackingStatus.trackingEnabled;
    }

    // For any other case (shouldn't normally reach here but safe fallback)
    return TrackingStatus.trackingDisabled;
  }

  Future<void> startTracking({
    required String tripId,
    required void Function(LocationPoint point) onLocationCaptured,
    required void Function(String error) onError,
  }) async {
    await stopTracking();  // Clean up existing tracking first
    _activeTripId = tripId;  // Then set the new trip ID

    await _location.changeSettings(
      accuracy: LocationAccuracy.high,
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

        // Update local single latest location cache
        await _cache.cacheLastLocation(
          latitude: point.latitude,
          longitude: point.longitude,
          accuracy: point.accuracy,
          recordedAt: point.recordedAt,
        );

        // Transmit coordinates to backend if possible; queue locally if offline
        try {
          await _transmitOrQueueLocation(point);
        } catch (e) {
          onError('Location buffered for offline sync: $e');
        }
      },
      onError: (err) {
        onError('GPS hardware error: $err');
      },
    );
  }

  Future<void> _transmitOrQueueLocation(LocationPoint point) async {
    if (_activeTripId == null) return;

    final token = await _tokenStorage.getToken();
    final localKey = 'loc-${point.recordedAt.millisecondsSinceEpoch}-${Random().nextInt(100000)}';
    final payload = point.toJson(_activeTripId!);
    payload['idempotency_key'] = localKey;

    if (token == null) {
      // Unauthenticated, buffer locally
      await _queueLocationEvent(localKey, point, payload);
      return;
    }

    try {
      final url = Uri.parse(Endpoints.location);
      final response = await _httpClient
          .post(
            url,
            headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer $token',
            },
            body: jsonEncode(payload),
          )
          .timeout(const Duration(seconds: 4));

      if (response.statusCode != 201) {
        // Server rejected or network issue -> Queue locally
        await _queueLocationEvent(localKey, point, payload);
      }
    } catch (_) {
      // Network timeout / offline -> Queue locally
      await _queueLocationEvent(localKey, point, payload);
    }
  }

  Future<void> _queueLocationEvent(
    String localKey,
    LocationPoint point,
    Map<String, dynamic> payload,
  ) async {
    final offlineEvent = OfflineEvent(
      localEventId: localKey,
      eventType: OfflineEventType.location,
      timestamp: point.recordedAt,
      payload: payload,
      status: QueueItemStatus.pending,
    );
    await _queue.enqueue(offlineEvent);
  }

  Future<void> stopTracking() async {
    await _positionStreamSub?.cancel();
    _positionStreamSub = null;
    _activeTripId = null;
  }
}
