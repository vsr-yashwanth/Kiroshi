import 'dart:async';
import 'dart:math';
import 'package:flutter/foundation.dart';
import '../constants/endpoints.dart';
import '../network/api_client.dart';
import '../storage/offline_event_queue.dart';
import 'connectivity_service.dart';

enum MobileSyncState {
  online,
  offline,
  syncing,
  synced,
  syncError,
}

class SyncManager extends ChangeNotifier {
  final OfflineEventQueue _queue;
  final ConnectivityService _connectivity;
  final ApiClient _apiClient;

  MobileSyncState _state = MobileSyncState.online;
  bool _isSyncing = false;
  int _consecutiveFailures = 0;
  Timer? _backoffTimer;
  StreamSubscription<bool>? _connSub;
  String? _lastError;

  SyncManager({
    OfflineEventQueue? queue,
    ConnectivityService? connectivity,
    ApiClient? apiClient,
  })  : _queue = queue ?? OfflineEventQueue(),
        _connectivity = connectivity ?? ConnectivityService(),
        _apiClient = apiClient ?? ApiClient() {
    _initConnectivityListener();
  }

  MobileSyncState get state => _state;
  bool get isSyncing => _isSyncing;
  String? get lastError => _lastError;
  int get consecutiveFailures => _consecutiveFailures;

  void _initConnectivityListener() {
    _connSub = _connectivity.onConnectivityChanged.listen((isOnline) {
      if (isOnline) {
        if (_state == MobileSyncState.offline || _state == MobileSyncState.syncError) {
          _consecutiveFailures = 0;
          _backoffTimer?.cancel();
          triggerSync();
        }
      } else {
        _setState(MobileSyncState.offline);
      }
    });
  }

  void _setState(MobileSyncState newState) {
    if (_state != newState) {
      _state = newState;
      notifyListeners();
    }
  }

  Duration calculateBackoff() {
    // Exponential backoff: 2s, 4s, 8s, 16s, max 30s
    final exp = min(_consecutiveFailures, 4);
    final seconds = min(30, (2 * pow(2, exp)).toInt());
    return Duration(seconds: seconds);
  }

  Future<bool> triggerSync({bool force = false}) async {
    // Single-worker mutex check (Phase 25)
    if (_isSyncing) {
      return false;
    }

    // Verify actual backend reachability
    final isOnline = await _connectivity.checkBackendReachable();
    if (!isOnline && !force) {
      _setState(MobileSyncState.offline);
      return false;
    }

    final pending = await _queue.getPendingEvents(limit: 50);
    if (pending.isEmpty) {
      _setState(MobileSyncState.synced);
      return true;
    }

    _isSyncing = true;
    _setState(MobileSyncState.syncing);

    try {
      final eventIds = pending.map((e) => e.localEventId).toList();
      await _queue.markSyncing(eventIds);

      final payload = {
        'events': pending.map((e) => e.toServerPayload()).toList(),
      };

      final response = await _apiClient.post(
        Endpoints.sync,
        body: payload,
        requireAuth: true,
      );

      final responseMap = response as Map<String, dynamic>;
      final results = (responseMap['results'] as List<dynamic>?) ?? [];

      final syncedIds = <String>[];
      for (final res in results) {
        final item = res as Map<String, dynamic>;
        final localId = item['local_event_id'] as String;
        final status = item['status'] as String;

        if (status == 'SYNCED' || status == 'DUPLICATE') {
          syncedIds.add(localId);
        } else if (status == 'CONFLICT' || status == 'REJECTED') {
          // Permanent failure, server rejected
          await _queue.markFailed(
            localId,
            item['message'] as String? ?? 'Rejected by server',
            isPermanent: true,
          );
        } else {
          // Temporary error
          await _queue.markFailed(
            localId,
            item['message'] as String? ?? 'Sync error',
            isPermanent: false,
          );
        }
      }

      if (syncedIds.isNotEmpty) {
        await _queue.markSynced(syncedIds);
        await _queue.pruneSynced();
      }

      _consecutiveFailures = 0;
      _lastError = null;
      _setState(MobileSyncState.synced);
      return true;
    } catch (e) {
      _consecutiveFailures += 1;
      _lastError = e.toString();
      _setState(MobileSyncState.syncError);

      // Schedule bounded exponential retry
      _scheduleRetry();
      return false;
    } finally {
      _isSyncing = false;
    }
  }

  void _scheduleRetry() {
    _backoffTimer?.cancel();
    final delay = calculateBackoff();
    _backoffTimer = Timer(delay, () {
      triggerSync();
    });
  }

  @override
  void dispose() {
    _connSub?.cancel();
    _backoffTimer?.cancel();
    super.dispose();
  }
}
