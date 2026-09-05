import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/constants/app_colors.dart';
import '../../application/trip_state.dart';
import '../../domain/models/trip.dart';
import 'live_tracking_screen.dart';

class TripDetailsScreen extends StatefulWidget {
  final String tripId;

  const TripDetailsScreen({super.key, required this.tripId});

  @override
  State<TripDetailsScreen> createState() => _TripDetailsScreenState();
}

class _TripDetailsScreenState extends State<TripDetailsScreen> {
  bool _isProcessing = false;

  @override
  Widget build(BuildContext context) {
    final tripState = Provider.of<TripState>(context);
    final trip = tripState.trips.firstWhere(
      (t) => t.id == widget.tripId,
      orElse: () => TripModel(
        id: widget.tripId,
        touristId: '',
        title: 'Trip Details',
        startDate: DateTime.now(),
        endDate: DateTime.now(),
        status: 'PLANNED',
        emergencyStatus: 'NORMAL',
        itineraries: [],
      ),
    );

    final isPlanned = trip.status == 'PLANNED';
    final isActive = trip.status == 'ACTIVE';

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.surface,
        title: Text(trip.title, style: const TextStyle(color: AppColors.textPrimary)),
        iconTheme: const IconThemeData(color: AppColors.textPrimary),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.border),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        trip.title,
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: (isActive ? AppColors.success : AppColors.primary).withOpacity(0.15),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          trip.status,
                          style: TextStyle(
                            color: isActive ? AppColors.success : AppColors.primaryLight,
                            fontWeight: FontWeight.bold,
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ],
                  ),
                  if (trip.description != null) ...[
                    const SizedBox(height: 8),
                    Text(trip.description!, style: const TextStyle(color: AppColors.textMuted)),
                  ],
                  const SizedBox(height: 16),
                  Text(
                    'Dates: ${trip.startDate.toLocal().toString().split(' ')[0]} to ${trip.endDate.toLocal().toString().split(' ')[0]}',
                    style: const TextStyle(color: AppColors.textSecondary, fontSize: 13),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            Text(
              'Waypoint Itinerary (${trip.itineraries.length})',
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
            ),
            const SizedBox(height: 12),
            if (trip.itineraries.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 24),
                child: Center(
                  child: Text('No waypoints registered for this journey', style: TextStyle(color: AppColors.textMuted)),
                ),
              )
            else
              ListView.separated(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: trip.itineraries.length,
                separatorBuilder: (_, __) => const SizedBox(height: 8),
                itemBuilder: (context, index) {
                  final waypoint = trip.itineraries[index];
                  return Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.surface,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: Row(
                      children: [
                        CircleAvatar(
                          radius: 14,
                          backgroundColor: AppColors.primaryLight.withOpacity(0.2),
                          child: Text(
                            '${waypoint.sequenceOrder}',
                            style: const TextStyle(color: AppColors.primaryLight, fontWeight: FontWeight.bold, fontSize: 12),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(waypoint.destinationName, style: const TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.bold)),
                              Text('${waypoint.latitude.toStringAsFixed(4)}°, ${waypoint.longitude.toStringAsFixed(4)}°', style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
                            ],
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            const SizedBox(height: 32),
            if (isPlanned)
              ElevatedButton.icon(
                onPressed: _isProcessing
                    ? null
                    : () async {
                        final messenger = ScaffoldMessenger.of(context);
                        setState(() => _isProcessing = true);
                        final ok = await tripState.startTrip(trip.id);
                        setState(() => _isProcessing = false);
                        if (mounted) {
                          messenger.showSnackBar(
                            SnackBar(
                              content: Text(ok ? 'Trip is now ACTIVE! Safe travels.' : 'Failed to start trip.'),
                              backgroundColor: ok ? AppColors.success : AppColors.danger,
                            ),
                          );
                        }
                      },
                icon: const Icon(Icons.play_arrow),
                label: const Text('Start Expedition Now', style: TextStyle(fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.success,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
            if (isActive) ...[
              ElevatedButton.icon(
                onPressed: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => LiveTrackingScreen(trip: trip),
                    ),
                  );
                },
                icon: const Icon(Icons.satellite_alt_rounded),
                label: const Text('Open Real-Time GPS Tracking', style: TextStyle(fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primaryLight,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
              const SizedBox(height: 12),
              ElevatedButton.icon(
                onPressed: _isProcessing
                    ? null
                    : () async {
                        final messenger = ScaffoldMessenger.of(context);
                        setState(() => _isProcessing = true);
                        final ok = await tripState.stopTrip(trip.id);
                        setState(() => _isProcessing = false);
                        if (mounted) {
                          messenger.showSnackBar(
                            SnackBar(
                              content: Text(ok ? 'Expedition concluded.' : 'Failed to conclude trip.'),
                              backgroundColor: ok ? AppColors.primary : AppColors.danger,
                            ),
                          );
                        }
                      },
                icon: const Icon(Icons.stop),
                label: const Text('Conclude Expedition', style: TextStyle(fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.danger,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
