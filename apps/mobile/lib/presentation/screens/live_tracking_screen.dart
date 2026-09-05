import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../application/location_state.dart';
import '../../domain/models/location_tracking_state.dart';
import '../../domain/models/trip.dart';
import '../../core/constants/app_colors.dart';
import '../widgets/sos_confirmation_sheet.dart';

class LiveTrackingScreen extends StatelessWidget {
  final TripModel trip;

  const LiveTrackingScreen({super.key, required this.trip});

  @override
  Widget build(BuildContext context) {
    return Consumer<LocationState>(
      builder: (context, locationState, child) {
        return Scaffold(
          backgroundColor: AppColors.background,
          appBar: AppBar(
            backgroundColor: AppColors.surface,
            elevation: 0,
            title: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Live GPS Safety Tracking', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                Text(trip.title, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
              ],
            ),
            actions: [
              IconButton(
                icon: const Icon(Icons.sos_rounded, color: Color(0xFFEF4444), size: 30),
                tooltip: 'Emergency SOS Beacon',
                onPressed: () => SosConfirmationSheet.show(context, activeTripId: trip.id),
              ),
            ],
          ),
          body: Column(
            children: [
              // Tracking Status Banner
              _buildStatusBanner(context, locationState),

              // Error notification if present
              if (locationState.lastError != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  color: AppColors.danger.withValues(alpha: 0.15),
                  child: Row(
                    children: [
                      const Icon(Icons.warning_amber_rounded, color: AppColors.danger, size: 18),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          locationState.lastError!,
                          style: const TextStyle(color: AppColors.danger, fontSize: 12),
                        ),
                      ),
                    ],
                  ),
                ),

              // Real-time Telemetry Cards & Authority Proximity Radar
              Expanded(
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    // Authority Proximity & Response Network Card
                    _buildAuthorityProximityCard(context, locationState),
                    const SizedBox(height: 14),

                    _buildTelemetryCard(
                      title: 'CURRENT COORDINATES',
                      value: locationState.currentLocation != null
                          ? '${locationState.currentLocation!.latitude.toStringAsFixed(5)}, ${locationState.currentLocation!.longitude.toStringAsFixed(5)}'
                          : 'Awaiting first satellite fix...',
                      icon: Icons.my_location,
                      color: AppColors.primary,
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: _buildTelemetryCard(
                            title: 'ACCURACY',
                            value: locationState.currentLocation != null
                              ? '±${locationState.currentLocation!.accuracy.toStringAsFixed(1)} m'
                              : '--',
                            icon: Icons.gps_fixed,
                            color: AppColors.success,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _buildTelemetryCard(
                            title: 'SPEED',
                            value: locationState.currentLocation?.speed != null
                              ? '${locationState.currentLocation!.speed!.toStringAsFixed(1)} m/s'
                              : '0.0 m/s',
                            icon: Icons.speed,
                            color: AppColors.warning,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: _buildTelemetryCard(
                            title: 'ALTITUDE',
                            value: locationState.currentLocation?.altitude != null
                              ? '${locationState.currentLocation!.altitude!.toStringAsFixed(0)} m'
                              : '--',
                            icon: Icons.landscape,
                            color: AppColors.primaryLight,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _buildTelemetryCard(
                            title: 'POINTS RECORDED',
                            value: '${locationState.routeTrail.length}',
                            icon: Icons.timeline,
                            color: AppColors.primary,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // Privacy & Safety Network Protection Notice
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: AppColors.surface,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: const Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(Icons.shield_outlined, color: AppColors.success, size: 20),
                          SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              'Battery-conscious adaptive distance filtering (10m) is active. Coordinates are encrypted and processed exclusively for safety geofencing and rescue coordination.',
                              style: TextStyle(color: AppColors.textSecondary, fontSize: 12, height: 1.4),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              // Bottom Tracking Control Button
              Container(
                padding: const EdgeInsets.all(16),
                decoration: const BoxDecoration(
                  color: AppColors.surface,
                  border: Border(top: BorderSide(color: AppColors.border)),
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    SizedBox(
                      width: double.infinity,
                      height: 46,
                      child: ElevatedButton.icon(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFFDC2626),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        icon: const Icon(Icons.warning_rounded, color: Colors.white, size: 20),
                        label: const Text(
                          'EMERGENCY SOS DISTRESS',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.white, letterSpacing: 0.8),
                        ),
                        onPressed: () => SosConfirmationSheet.show(context, activeTripId: trip.id),
                      ),
                    ),
                    const SizedBox(height: 10),
                    SizedBox(
                      width: double.infinity,
                      height: 48,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: locationState.status == TrackingStatus.trackingEnabled
                              ? AppColors.danger
                              : AppColors.success,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        onPressed: () {
                          if (locationState.status == TrackingStatus.trackingEnabled) {
                            locationState.stopTracking();
                          } else {
                            locationState.startTracking(trip.id);
                          }
                        },
                        child: Text(
                          locationState.status == TrackingStatus.trackingEnabled
                              ? 'STOP GPS TRACKING'
                              : 'ENABLE REAL-TIME TRACKING',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Colors.white),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildAuthorityProximityCard(BuildContext context, LocationState locationState) {
    final bool isTracking = locationState.status == TrackingStatus.trackingEnabled;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF1E293B)),
        boxShadow: const [
          BoxShadow(
            color: Colors.black26,
            blurRadius: 10,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: const Color(0xFF06B6D4).withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(Icons.security_rounded, color: Color(0xFF06B6D4), size: 20),
                  ),
                  const SizedBox(width: 10),
                  const Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'AUTHORITY SAFETY RADAR',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF06B6D4),
                          letterSpacing: 0.5,
                        ),
                      ),
                      Text(
                        'Nearest Dispatch Base: 1.2 km away',
                        style: TextStyle(fontSize: 11, color: AppColors.textSecondary),
                      ),
                    ],
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: isTracking ? const Color(0xFF10B981).withValues(alpha: 0.15) : const Color(0xFF64748B).withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: isTracking ? const Color(0xFF10B981).withValues(alpha: 0.4) : const Color(0xFF64748B).withValues(alpha: 0.4),
                  ),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 6,
                      height: 6,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: isTracking ? const Color(0xFF10B981) : const Color(0xFF64748B),
                      ),
                    ),
                    const SizedBox(width: 5),
                    Text(
                      isTracking ? 'CONNECTED' : 'STANDBY',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        color: isTracking ? const Color(0xFF10B981) : const Color(0xFF94A3B8),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          const Divider(color: Color(0xFF1E293B), height: 1),
          const SizedBox(height: 10),
          Row(
            children: [
              const Icon(Icons.shield_rounded, size: 14, color: Color(0xFF10B981)),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  isTracking
                      ? 'Command center is actively observing your GPS telemetry trail for safety.'
                      : 'Enable tracking to broadcast telemetry directly to nearby rescue authorities.',
                  style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatusBanner(BuildContext context, LocationState locationState) {
    Color bannerColor;
    IconData icon;
    String title;
    String description;

    switch (locationState.status) {
      case TrackingStatus.trackingEnabled:
        bannerColor = AppColors.success;
        icon = Icons.radio_button_checked;
        title = 'TRACKING ENABLED';
        description = 'Real-time GPS coordinates are streaming to Authority Command.';
        break;
      case TrackingStatus.permissionDenied:
        bannerColor = AppColors.danger;
        icon = Icons.location_disabled;
        title = 'PERMISSION DENIED';
        description = 'Location permission is required to enable tourist safety tracking.';
        break;
      case TrackingStatus.locationUnavailable:
        bannerColor = AppColors.warning;
        icon = Icons.gps_off;
        title = 'LOCATION UNAVAILABLE';
        description = 'Device GPS service is currently turned off or unavailable.';
        break;
      case TrackingStatus.trackingDisabled:
        bannerColor = AppColors.textMuted;
        icon = Icons.pause_circle_outline;
        title = 'TRACKING DISABLED';
        description = 'Press below to start real-time journey observation.';
        break;
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: bannerColor.withValues(alpha: 0.12),
        border: Border(bottom: BorderSide(color: bannerColor.withValues(alpha: 0.3))),
      ),
      child: Row(
        children: [
          Icon(icon, color: bannerColor, size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: bannerColor, letterSpacing: 0.5),
                ),
                Text(
                  description,
                  style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTelemetryCard({
    required String title,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 14, color: color),
              const SizedBox(width: 6),
              Text(
                title,
                style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppColors.textMuted, letterSpacing: 0.5),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
          ),
        ],
      ),
    );
  }
}
