import 'package:flutter/foundation.dart';
import '../core/services/sync_manager.dart';
import '../core/storage/offline_event_queue.dart';

class OfflineSyncState extends ChangeNotifier {
  final SyncManager _syncManager;
  final OfflineEventQueue _queue;

  int _pendingEventCount = 0;
  bool _hasPendingSos = false;

  OfflineSyncState({
    SyncManager? syncManager,
    OfflineEventQueue? queue,
  })  : _syncManager = syncManager ?? SyncManager(),
        _queue = queue ?? OfflineEventQueue() {
    _syncManager.addListener(_onSyncManagerChanged);
    refreshQueueStatus();
  }

  SyncManager get syncManager => _syncManager;
  MobileSyncState get state => _syncManager.state;
  bool get isSyncing => _syncManager.isSyncing;
  String? get lastError => _syncManager.lastError;
  int get pendingEventCount => _pendingEventCount;
  bool get hasPendingSos => _hasPendingSos;

  String? get honestSosMessage {
    if (_hasPendingSos) {
      return 'Emergency saved on this device. It has NOT reached authorities yet. We will retry when connectivity returns.';
    }
    return null;
  }

  void _onSyncManagerChanged() {
    refreshQueueStatus();
    notifyListeners();
  }

  Future<void> refreshQueueStatus() async {
    final pending = await _queue.getPendingEvents(limit: 500);
    _pendingEventCount = pending.length;
    _hasPendingSos = await _queue.hasPendingSos();
    notifyListeners();
  }

  Future<bool> triggerManualSync() async {
    final success = await _syncManager.triggerSync(force: true);
    await refreshQueueStatus();
    return success;
  }

  @override
  void dispose() {
    _syncManager.removeListener(_onSyncManagerChanged);
    super.dispose();
  }
}
