enum TrackingStatus {
  trackingEnabled,
  trackingDisabled,
  permissionDenied,
  locationUnavailable,
}

class LocationPoint {
  final double latitude;
  final double longitude;
  final double accuracy;
  final double? altitude;
  final double? speed;
  final double? heading;
  final DateTime recordedAt;

  const LocationPoint({
    required this.latitude,
    required this.longitude,
    required this.accuracy,
    this.altitude,
    this.speed,
    this.heading,
    required this.recordedAt,
  });

  Map<String, dynamic> toJson(String tripId) {
    return {
      'trip_id': tripId,
      'latitude': latitude,
      'longitude': longitude,
      'accuracy': accuracy,
      'altitude': altitude,
      'speed': speed,
      'heading': heading,
      'recorded_at': recordedAt.toUtc().toIso8601String(),
    };
  }
}
