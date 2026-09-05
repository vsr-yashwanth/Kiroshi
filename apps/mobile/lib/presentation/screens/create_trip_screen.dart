import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/constants/app_colors.dart';
import '../../application/trip_state.dart';
import '../../domain/models/itinerary.dart';

class CreateTripScreen extends StatefulWidget {
  const CreateTripScreen({super.key});

  @override
  State<CreateTripScreen> createState() => _CreateTripScreenState();
}

class _CreateTripScreenState extends State<CreateTripScreen> {
  final _titleController = TextEditingController();
  final _descController = TextEditingController();
  final _waypointNameController = TextEditingController();
  final _latController = TextEditingController();
  final _lngController = TextEditingController();

  final List<ItineraryModel> _waypoints = [];
  final DateTime _startDate = DateTime.now().add(const Duration(days: 1));
  final DateTime _endDate = DateTime.now().add(const Duration(days: 5));
  bool _isSubmitting = false;

  @override
  void dispose() {
    _titleController.dispose();
    _descController.dispose();
    _waypointNameController.dispose();
    _latController.dispose();
    _lngController.dispose();
    super.dispose();
  }

  void _addWaypoint() {
    final name = _waypointNameController.text.trim();
    final lat = double.tryParse(_latController.text.trim());
    final lng = double.tryParse(_lngController.text.trim());

    if (name.isEmpty || lat == null || lng == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter valid waypoint name and numeric coordinates.')),
      );
      return;
    }

    setState(() {
      _waypoints.add(
        ItineraryModel(
          id: '',
          tripId: '',
          destinationName: name,
          latitude: lat,
          longitude: lng,
          sequenceOrder: _waypoints.length + 1,
        ),
      );
      _waypointNameController.clear();
      _latController.clear();
      _lngController.clear();
    });
  }

  void _submit() async {
    final title = _titleController.text.trim();
    if (title.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Trip title is required.')),
      );
      return;
    }

    setState(() => _isSubmitting = true);
    final tripState = Provider.of<TripState>(context, listen: false);

    final created = await tripState.createTrip(
      title: title,
      description: _descController.text.trim().isNotEmpty ? _descController.text.trim() : null,
      startDate: _startDate,
      endDate: _endDate,
      waypoints: _waypoints,
    );

    setState(() => _isSubmitting = false);

    if (created != null && mounted) {
      Navigator.of(context).pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.surface,
        title: const Text('Plan New Expedition', style: TextStyle(color: AppColors.textPrimary)),
        iconTheme: const IconThemeData(color: AppColors.textPrimary),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _titleController,
              style: const TextStyle(color: AppColors.textPrimary),
              decoration: const InputDecoration(
                labelText: 'Trip Title *',
                labelStyle: TextStyle(color: AppColors.textSecondary),
                filled: true,
                fillColor: AppColors.surface,
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _descController,
              maxLines: 2,
              style: const TextStyle(color: AppColors.textPrimary),
              decoration: const InputDecoration(
                labelText: 'Description / Route Objectives',
                labelStyle: TextStyle(color: AppColors.textSecondary),
                filled: true,
                fillColor: AppColors.surface,
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              'Planned Waypoints',
              style: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.border),
              ),
              child: Column(
                children: [
                  TextField(
                    controller: _waypointNameController,
                    style: const TextStyle(color: AppColors.textPrimary),
                    decoration: const InputDecoration(
                      labelText: 'Waypoint Name (e.g. Basecamp)',
                      labelStyle: TextStyle(color: AppColors.textSecondary),
                      isDense: true,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _latController,
                          keyboardType: TextInputType.number,
                          style: const TextStyle(color: AppColors.textPrimary),
                          decoration: const InputDecoration(
                            labelText: 'Latitude (e.g. 32.24)',
                            labelStyle: TextStyle(color: AppColors.textSecondary),
                            isDense: true,
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: TextField(
                          controller: _lngController,
                          keyboardType: TextInputType.number,
                          style: const TextStyle(color: AppColors.textPrimary),
                          decoration: const InputDecoration(
                            labelText: 'Longitude (e.g. 77.18)',
                            labelStyle: TextStyle(color: AppColors.textSecondary),
                            isDense: true,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Align(
                    alignment: Alignment.centerRight,
                    child: OutlinedButton.icon(
                      onPressed: _addWaypoint,
                      icon: const Icon(Icons.add_location_alt_outlined, size: 16),
                      label: const Text('Add Waypoint'),
                      style: OutlinedButton.styleFrom(foregroundColor: AppColors.primaryLight),
                    ),
                  ),
                ],
              ),
            ),
            if (_waypoints.isNotEmpty) ...[
              const SizedBox(height: 16),
              ..._waypoints.map((w) => Card(
                    color: AppColors.surfaceLight,
                    margin: const EdgeInsets.only(bottom: 8),
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: AppColors.primary,
                        radius: 14,
                        child: Text('${w.sequenceOrder}', style: const TextStyle(fontSize: 12, color: Colors.white)),
                      ),
                      title: Text(w.destinationName, style: const TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.bold)),
                      subtitle: Text('${w.latitude}°, ${w.longitude}°', style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
                      trailing: IconButton(
                        icon: const Icon(Icons.delete_outline, color: AppColors.danger),
                        onPressed: () => setState(() => _waypoints.remove(w)),
                      ),
                    ),
                  )),
            ],
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: _isSubmitting ? null : _submit,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              child: _isSubmitting
                  ? const CircularProgressIndicator(color: Colors.white)
                  : const Text('Confirm & Save Expedition', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            ),
          ],
        ),
      ),
    );
  }
}
