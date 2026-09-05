import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:kiroshi_mobile/core/services/sos_service.dart';
import 'package:kiroshi_mobile/core/storage/offline_event_queue.dart';
import 'package:kiroshi_mobile/core/services/connectivity_service.dart';
import 'package:kiroshi_mobile/core/network/api_client.dart';
import 'package:kiroshi_mobile/domain/models/offline_event.dart';

class MockOfflineConnectivityService extends ConnectivityService {
  @override
  Future<bool> checkBackendReachable() async => false;
}

class MockOnlineConnectivityService extends ConnectivityService {
  @override
  Future<bool> checkBackendReachable() async => true;
}

class MockSuccessApiClient extends ApiClient {
  @override
  Future<dynamic> post(
    String url, {
    dynamic body,
    bool requireAuth = true,
  }) async {
    return {
      'id': 'incident-auth-ack-1234',
      'status': 'DETECTED',
      'severity': 'CRITICAL',
    };
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('Offline SOS Critical Honesty Rule Tests', () {
    test('Offline SOS explicitly states NOT reached authorities yet and queues event', () async {
      final queue = OfflineEventQueue();
      final sosService = SosService(
        queue: queue,
        connectivity: MockOfflineConnectivityService(),
        apiClient: MockSuccessApiClient(),
      );

      final result = await sosService.triggerSos(
        tripId: 'trip-offline-test',
        notes: 'Cold night in ravine',
        idempotencyKey: 'sos-honest-offline-1',
      );

      // 1. MUST NOT claim emergency is sent
      expect(result.status, SosDeliveryStatus.savedLocally);
      expect(result.isConfirmedByAuthorities, isFalse);
      expect(result.incidentId, isNull);

      // 2. Unmistakable honest messaging required by specification
      expect(result.honestMessage, contains('saved on this device'));
      expect(result.honestMessage, contains('NOT reached authorities yet'));

      // 3. Must be safely queued in local persistent queue
      final pending = await queue.getPendingEvents();
      expect(pending.length, 1);
      expect(pending.first.localEventId, 'sos-honest-offline-1');
      expect(pending.first.eventType, OfflineEventType.sos);
    });

    test('Online SOS only marks CONFIRMED after server acknowledgement', () async {
      final queue = OfflineEventQueue();
      final sosService = SosService(
        queue: queue,
        connectivity: MockOnlineConnectivityService(),
        apiClient: MockSuccessApiClient(),
      );

      final result = await sosService.triggerSos(
        tripId: 'trip-online-test',
        notes: 'Immediate hazard',
        idempotencyKey: 'sos-online-ack-1',
      );

      // Server confirmed receipt
      expect(result.status, SosDeliveryStatus.sent);
      expect(result.isConfirmedByAuthorities, isTrue);
      expect(result.incidentId, 'incident-auth-ack-1234');
      expect(result.honestMessage, contains('received and confirmed by authorities'));
    });
  });
}
