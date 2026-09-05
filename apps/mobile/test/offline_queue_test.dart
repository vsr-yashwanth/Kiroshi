import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:kiroshi_mobile/domain/models/offline_event.dart';
import 'package:kiroshi_mobile/core/storage/offline_event_queue.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('OfflineEventQueue Unit Tests', () {
    test('enqueues events and preserves FIFO chronological ordering', () async {
      final queue = OfflineEventQueue();

      final ev1 = OfflineEvent(
        localEventId: 'ev-1',
        eventType: OfflineEventType.location,
        timestamp: DateTime.parse('2026-09-05T10:00:00Z'),
        payload: {'lat': 35.0, 'lon': 139.0},
      );
      final ev2 = OfflineEvent(
        localEventId: 'ev-2',
        eventType: OfflineEventType.location,
        timestamp: DateTime.parse('2026-09-05T10:01:00Z'),
        payload: {'lat': 35.1, 'lon': 139.1},
      );

      await queue.enqueue(ev1);
      await queue.enqueue(ev2);

      final pending = await queue.getPendingEvents();
      expect(pending.length, 2);
      expect(pending[0].localEventId, 'ev-1');
      expect(pending[1].localEventId, 'ev-2');
    });

    test('prioritizes SOS distress beacon above location events', () async {
      final queue = OfflineEventQueue();

      final locEvent = OfflineEvent(
        localEventId: 'loc-1',
        eventType: OfflineEventType.location,
        timestamp: DateTime.parse('2026-09-05T09:00:00Z'),
        payload: {'lat': 35.0, 'lon': 139.0},
      );
      final sosEvent = OfflineEvent(
        localEventId: 'sos-life-critical',
        eventType: OfflineEventType.sos,
        timestamp: DateTime.parse('2026-09-05T09:30:00Z'), // Triggered later
        payload: {'notes': 'Injured'},
      );

      await queue.enqueue(locEvent);
      await queue.enqueue(sosEvent);

      final pending = await queue.getPendingEvents();
      expect(pending.length, 2);
      // SOS must be at the very front regardless of later timestamp
      expect(pending[0].localEventId, 'sos-life-critical');
      expect(pending[0].eventType, OfflineEventType.sos);
      expect(pending[1].localEventId, 'loc-1');
    });

    test('survives application restart simulation', () async {
      // 1. App running offline: enqueue SOS and location
      final queueSession1 = OfflineEventQueue();
      final sosEvent = OfflineEvent(
        localEventId: 'sos-persistent-test',
        eventType: OfflineEventType.sos,
        timestamp: DateTime.now(),
        payload: {'notes': 'App kill test'},
      );
      await queueSession1.enqueue(sosEvent);

      // 2. Simulate Application Termination / Restart:
      // Create a brand new OfflineEventQueue instance from storage
      final queueSession2 = OfflineEventQueue();
      final recoveredEvents = await queueSession2.getAllEvents();

      expect(recoveredEvents.length, 1);
      expect(recoveredEvents.first.localEventId, 'sos-persistent-test');
      expect(recoveredEvents.first.eventType, OfflineEventType.sos);
      expect(await queueSession2.hasPendingSos(), isTrue);
    });

    test('marks status transitions and prunes synced events cleanly', () async {
      final queue = OfflineEventQueue();

      final ev1 = OfflineEvent(
        localEventId: 'ev-1',
        eventType: OfflineEventType.location,
        timestamp: DateTime.now(),
        payload: {},
      );
      await queue.enqueue(ev1);

      await queue.markSyncing(['ev-1']);
      var all = await queue.getAllEvents();
      expect(all.first.status, QueueItemStatus.syncing);

      await queue.markSynced(['ev-1']);
      all = await queue.getAllEvents();
      expect(all.first.status, QueueItemStatus.synced);

      await queue.pruneSynced();
      all = await queue.getAllEvents();
      expect(all.isEmpty, isTrue);
    });

    test('enforces storage bounds without ever dropping life-critical SOS events', () async {
      final queue = OfflineEventQueue();

      // Enqueue life-critical SOS
      final sos = OfflineEvent(
        localEventId: 'sos-must-survive',
        eventType: OfflineEventType.sos,
        timestamp: DateTime.now(),
        payload: {'hazard': 'cliff'},
      );
      await queue.enqueue(sos);

      // Fill queue to exceed maxQueueCapacity
      for (int i = 0; i < OfflineEventQueue.maxQueueCapacity + 10; i++) {
        final loc = OfflineEvent(
          localEventId: 'loc-fill-$i',
          eventType: OfflineEventType.location,
          timestamp: DateTime.now(),
          payload: {'seq': i},
        );
        await queue.enqueue(loc);
      }

      final all = await queue.getAllEvents();
      expect(all.length, lessThanOrEqualTo(OfflineEventQueue.maxQueueCapacity));

      // Verify the SOS event was NEVER pruned
      final hasSos = all.any((e) => e.localEventId == 'sos-must-survive');
      expect(hasSos, isTrue);
    });
  });
}
