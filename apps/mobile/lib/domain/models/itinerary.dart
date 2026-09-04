class ItineraryModel {
  final String id;
  final String tripId;
  final String destinationName;
  final DateTime? plannedArrival;
  final DateTime? plannedDeparture;
  final double latitude;
  final double longitude;
  final int sequenceOrder;

  ItineraryModel({
    required this.id,
    required this.tripId,
    required this.destinationName,
    this.plannedArrival,
    this.plannedDeparture,
    required this.latitude,
    required this.longitude,
    required this.sequenceOrder,
  });

  factory ItineraryModel.fromJson(Map<String, dynamic> json) {
    return ItineraryModel(
      id: json['id'] as String,
      tripId: json['trip_id'] as String,
      destinationName: json['destination_name'] as String,
      plannedArrival: json['planned_arrival'] != null ? DateTime.parse(json['planned_arrival']) : null,
      plannedDeparture: json['planned_departure'] != null ? DateTime.parse(json['planned_departure']) : null,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      sequenceOrder: json['sequence_order'] as int? ?? 1,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'destination_name': destinationName,
      'latitude': latitude,
      'longitude': longitude,
      'sequence_order': sequenceOrder,
    };
  }
}
