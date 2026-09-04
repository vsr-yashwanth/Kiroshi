import 'itinerary.dart';

typedef Trip = TripModel;

class TripModel {
  final String id;
  final String touristId;
  final String title;
  final String? description;
  final DateTime startDate;
  final DateTime endDate;
  final String status;
  final String emergencyStatus;
  final List<ItineraryModel> itineraries;

  TripModel({
    required this.id,
    required this.touristId,
    required this.title,
    this.description,
    required this.startDate,
    required this.endDate,
    required this.status,
    required this.emergencyStatus,
    required this.itineraries,
  });

  factory TripModel.fromJson(Map<String, dynamic> json) {
    return TripModel(
      id: json['id'] as String,
      touristId: json['tourist_id'] as String,
      title: json['title'] as String,
      description: json['description'] as String?,
      startDate: DateTime.parse(json['start_date']),
      endDate: DateTime.parse(json['end_date']),
      status: json['status'] as String? ?? 'PLANNED',
      emergencyStatus: json['emergency_status'] as String? ?? 'NORMAL',
      itineraries: (json['itineraries'] as List<dynamic>?)
              ?.map((item) => ItineraryModel.fromJson(item as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}
