import 'dart:math';
import 'package:location/location.dart';
import '../../domain/models/offline_event.dart';
import '../network/api_client.dart';
import '../constants/endpoints.dart';
import '../storage/offline_event_queue.dart';
import 'connectivity_service.dart';

enum SosDeliveryStatus {
  savedLocally,
  waitingForConnection,
  sending,
  sent,
  syncFailed,
}

class SosTriggerResult {
  final SosDeliveryStatus status;
  final String localEventId;
  final String? incidentId;
  final String honestMessage;
  final Map<String, dynamic>? rawResponse;

  SosTriggerResult({
    required this.status,
    required this.localEventId,
    this.incidentId,
    required this.honestMessage,
    this.rawResponse,
  });

  bool get isConfirmedByAuthorities => status == SosDeliveryStatus.sent && incidentId != null;
}

class SosService {
  final ApiClient _apiClient;
  final OfflineEventQueue _queue;
  final ConnectivityService _connectivity;
  final Location _location = Location();

  SosService({
    ApiClient? apiClient,
    OfflineEventQueue? queue,
    ConnectivityService? connectivity,
  })  : _apiClient = apiClient ?? ApiClient(),
        _queue = queue ?? OfflineEventQueue(),
        _connectivity = connectivity ?? ConnectivityService();

  String generateIdempotencyKey() {
    final rand = Random().nextInt(1000000);
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    return 'sos-$timestamp-$rand';
  }

  /// Triggers an emergency SOS distress beacon.
  /// Enforces the Critical Honesty Rule: Never claims emergency was sent unless
  /// server acknowledges receipt.
  Future<SosTriggerResult> triggerSos({
    String? tripId,
    String? notes,
    String? idempotencyKey,
  }) async {
    final localId = idempotencyKey ?? generateIdempotencyKey();

    double? latitude;
    double? longitude;
    double? accuracy;

    try {
      final locData = await _location.getLocation().timeout(
        const Duration(seconds: 4),
      );
      latitude = locData.latitude;
      longitude = locData.longitude;
      accuracy = locData.accuracy;
    } catch (_) {
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
      'idempotency_key': localId,
    };

    // Check backend reachability
    final isOnline = await _connectivity.checkBackendReachable();

    if (isOnline) {
      try {
        final response = await _apiClient.post(
          Endpoints.sos,
          body: payload,
          requireAuth: true,
        );

        final map = response as Map<String, dynamic>;
        final incidentId = map['id']?.toString();

        return SosTriggerResult(
          status: SosDeliveryStatus.sent,
          localEventId: localId,
          incidentId: incidentId,
          honestMessage: 'Emergency received and confirmed by authorities. Dispatch underway.',
          rawResponse: map,
        );
      } catch (_) {
        // Network failed during transmission -> Queue locally
      }
    }

    // Persist SOS locally into persistent queue
    final offlineEvent = OfflineEvent(
      localEventId: localId,
      eventType: OfflineEventType.sos,
      timestamp: DateTime.now(),
      payload: payload,
      status: QueueItemStatus.pending,
    );

    await _queue.enqueue(offlineEvent);

    return SosTriggerResult(
      status: SosDeliveryStatus.savedLocally,
      localEventId: localId,
      incidentId: null,
      honestMessage:
          'Emergency saved on this device. It has NOT reached authorities yet. We will retry when connectivity returns.',
    );
  }
}
