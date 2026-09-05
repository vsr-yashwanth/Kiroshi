import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../application/offline_sync_state.dart';
import '../../core/services/sync_manager.dart';

class ConnectivityBanner extends StatelessWidget {
  const ConnectivityBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<OfflineSyncState>(
      builder: (context, syncState, child) {
        // Priority 1: High-contrast offline SOS pending warning (Critical Honesty Rule)
        if (syncState.hasPendingSos) {
          return Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            color: Colors.red.shade900,
            child: Row(
              children: [
                const Icon(Icons.warning_amber_rounded, color: Colors.white, size: 22),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text(
                        'EMERGENCY SAVED LOCALLY',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        syncState.honestSosMessage ??
                            'Not yet reached authorities. Retrying continuously...',
                        style: const TextStyle(color: Colors.white, fontSize: 11),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.refresh, color: Colors.white, size: 18),
                  tooltip: 'Retry transmission',
                  onPressed: () => syncState.triggerManualSync(),
                ),
              ],
            ),
          );
        }

        // Priority 2: Syncing state
        if (syncState.state == MobileSyncState.syncing) {
          return Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            color: Colors.indigo.shade800,
            child: Row(
              children: [
                const SizedBox(
                  width: 14,
                  height: 14,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Synchronizing offline events (${syncState.pendingEventCount} pending)...',
                    style: const TextStyle(color: Colors.white, fontSize: 12),
                  ),
                ),
              ],
            ),
          );
        }

        // Priority 3: Offline mode active
        if (syncState.state == MobileSyncState.offline) {
          return Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            color: Colors.amber.shade900,
            child: Row(
              children: [
                const Icon(Icons.wifi_off, color: Colors.white, size: 16),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    syncState.pendingEventCount > 0
                        ? 'Offline Mode — ${syncState.pendingEventCount} events queued'
                        : 'Offline Mode — Essential trip data available',
                    style: const TextStyle(color: Colors.white, fontSize: 12),
                  ),
                ),
                InkWell(
                  onTap: () => syncState.triggerManualSync(),
                  child: const Text(
                    'RETRY',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      decoration: TextDecoration.underline,
                    ),
                  ),
                ),
              ],
            ),
          );
        }

        // Priority 4: Sync error
        if (syncState.state == MobileSyncState.syncError) {
          return Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            color: Colors.deepOrange.shade900,
            child: Row(
              children: [
                const Icon(Icons.sync_problem, color: Colors.white, size: 16),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Sync paused (${syncState.pendingEventCount} queued) — Retrying shortly',
                    style: const TextStyle(color: Colors.white, fontSize: 12),
                  ),
                ),
                InkWell(
                  onTap: () => syncState.triggerManualSync(),
                  child: const Text(
                    'SYNC NOW',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      decoration: TextDecoration.underline,
                    ),
                  ),
                ),
              ],
            ),
          );
        }

        // Online & fully synced: no banner needed
        return const SizedBox.shrink();
      },
    );
  }
}
