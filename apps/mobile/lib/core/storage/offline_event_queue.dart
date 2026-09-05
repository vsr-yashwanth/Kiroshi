import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../../domain/models/offline_event.dart';

class OfflineEventQueue {
  static const String _storageKey = 'kiroshi_offline_event_queue';
  static const int maxQueueCapacity = 1000;

  final SharedPreferences? _prefsInstance;

  OfflineEventQueue({SharedPreferences? prefs}) : _prefsInstance = prefs;

  Future<SharedPreferences> _getPrefs() async {
    return _prefsInstance ?? await SharedPreferences.getInstance();
  }

  Future<List<OfflineEvent>> getAllEvents() async {
    final prefs = await _getPrefs();
    final rawJson = prefs.getString(_storageKey);
    if (rawJson == null || rawJson.isEmpty) {
      return [];
    }

    try {
      final List<dynamic> decoded = jsonDecode(rawJson) as List<dynamic>;
      return decoded
          .map((item) => OfflineEvent.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (_) {
      return [];
    }
  }

  Future<void> _saveEvents(List<OfflineEvent> events) async {
    final prefs = await _getPrefs();
    final encoded = jsonEncode(events.map((e) => e.toJson()).toList());
    await prefs.setString(_storageKey, encoded);
  }

  Future<void> enqueue(OfflineEvent event) async {
    final events = await getAllEvents();

    // Prevent duplicate localEventId in queue
    final existingIdx = events.indexWhere((e) => e.localEventId == event.localEventId);
    if (existingIdx != -1) {
      return;
    }

    events.add(event);
    _enforceStorageBounds(events);
    await _saveEvents(events);
  }

  void _enforceStorageBounds(List<OfflineEvent> events) {
    if (events.length <= maxQueueCapacity) return;

    // 1. Remove synced items first
    events.removeWhere((e) => e.status == QueueItemStatus.synced);
    if (events.length <= maxQueueCapacity) return;

    // 2. Prune oldest non-SOS events if still exceeding limit. NEVER drop SOS events!
    while (events.length > maxQueueCapacity) {
      final nonSosIdx = events.indexWhere((e) => e.eventType != OfflineEventType.sos);
      if (nonSosIdx != -1) {
        events.removeAt(nonSosIdx);
      } else {
        break; // Only SOS remains, preserve them
      }
    }
  }

  Future<List<OfflineEvent>> getPendingEvents({int limit = 50}) async {
    final events = await getAllEvents();

    // Prioritize SOS events first, then chronological order
    final pending = events
        .where((e) =>
            e.status == QueueItemStatus.pending ||
            (e.status == QueueItemStatus.failed && !e.isPermanentFailure))
        .toList();

    pending.sort((a, b) {
      if (a.eventType == OfflineEventType.sos && b.eventType != OfflineEventType.sos) {
        return -1;
      }
      if (b.eventType == OfflineEventType.sos && a.eventType != OfflineEventType.sos) {
        return 1;
      }
      return a.timestamp.compareTo(b.timestamp);
    });

    if (pending.length > limit) {
      return pending.sublist(0, limit);
    }
    return pending;
  }

  Future<void> markSyncing(List<String> eventIds) async {
    final events = await getAllEvents();
    final idSet = eventIds.toSet();
    for (final e in events) {
      if (idSet.contains(e.localEventId)) {
        e.status = QueueItemStatus.syncing;
      }
    }
    await _saveEvents(events);
  }

  Future<void> markSynced(List<String> eventIds) async {
    final events = await getAllEvents();
    final idSet = eventIds.toSet();
    for (final e in events) {
      if (idSet.contains(e.localEventId)) {
        e.status = QueueItemStatus.synced;
      }
    }
    await _saveEvents(events);
  }

  Future<void> markFailed(String eventId, String reason, {bool isPermanent = false}) async {
    final events = await getAllEvents();
    for (final e in events) {
      if (e.localEventId == eventId) {
        e.status = QueueItemStatus.failed;
        e.errorReason = reason;
        e.retryCount += 1;
        e.isPermanentFailure = isPermanent;
        break;
      }
    }
    await _saveEvents(events);
  }

  Future<void> pruneSynced() async {
    final events = await getAllEvents();
    events.removeWhere((e) => e.status == QueueItemStatus.synced);
    await _saveEvents(events);
  }

  Future<bool> hasPendingSos() async {
    final events = await getAllEvents();
    return events.any((e) =>
        e.eventType == OfflineEventType.sos &&
        e.status != QueueItemStatus.synced);
  }

  Future<OfflineEvent?> getPendingSos() async {
    final events = await getAllEvents();
    try {
      return events.firstWhere((e) =>
          e.eventType == OfflineEventType.sos &&
          e.status != QueueItemStatus.synced);
    } catch (_) {
      return null;
    }
  }

  Future<void> clearQueue() async {
    final prefs = await _getPrefs();
    await prefs.remove(_storageKey);
  }
}
