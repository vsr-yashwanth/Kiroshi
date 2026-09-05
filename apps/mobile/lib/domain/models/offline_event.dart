enum OfflineEventType {
  sos,
  location,
  tripUpdate,
  incidentAction,
}

enum QueueItemStatus {
  pending,
  syncing,
  synced,
  failed,
}

class OfflineEvent {
  final String localEventId;
  final OfflineEventType eventType;
  final DateTime timestamp;
  final Map<String, dynamic> payload;
  int retryCount;
  QueueItemStatus status;
  String? errorReason;
  bool isPermanentFailure;

  OfflineEvent({
    required this.localEventId,
    required this.eventType,
    required this.timestamp,
    required this.payload,
    this.retryCount = 0,
    this.status = QueueItemStatus.pending,
    this.errorReason,
    this.isPermanentFailure = false,
  });

  Map<String, dynamic> toJson() => {
        'local_event_id': localEventId,
        'event_type': eventType.name,
        'timestamp': timestamp.toIso8601String(),
        'payload': payload,
        'retry_count': retryCount,
        'status': status.name,
        'error_reason': errorReason,
        'is_permanent_failure': isPermanentFailure,
      };

  factory OfflineEvent.fromJson(Map<String, dynamic> json) => OfflineEvent(
        localEventId: json['local_event_id'] as String,
        eventType: OfflineEventType.values.firstWhere(
          (e) => e.name == json['event_type'],
          orElse: () => OfflineEventType.location,
        ),
        timestamp: DateTime.parse(json['timestamp'] as String),
        payload: Map<String, dynamic>.from(json['payload'] as Map),
        retryCount: (json['retry_count'] as num?)?.toInt() ?? 0,
        status: QueueItemStatus.values.firstWhere(
          (e) => e.name == json['status'],
          orElse: () => QueueItemStatus.pending,
        ),
        errorReason: json['error_reason'] as String?,
        isPermanentFailure: json['is_permanent_failure'] as bool? ?? false,
      );

  /// Formats this event for transmission to POST /api/v1/sync/events
  Map<String, dynamic> toServerPayload() {
    String serverEventType;
    switch (eventType) {
      case OfflineEventType.sos:
        serverEventType = 'SOS_EVENT';
        break;
      case OfflineEventType.location:
        serverEventType = 'LOCATION_EVENT';
        break;
      case OfflineEventType.tripUpdate:
        serverEventType = 'TRIP_UPDATE';
        break;
      case OfflineEventType.incidentAction:
        serverEventType = 'INCIDENT_ACTION';
        break;
    }

    return {
      'local_event_id': localEventId,
      'event_type': serverEventType,
      'timestamp': timestamp.toUtc().toIso8601String(),
      'payload': payload,
      'retry_count': retryCount,
    };
  }
}
