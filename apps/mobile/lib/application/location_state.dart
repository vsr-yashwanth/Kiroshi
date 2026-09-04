import 'package:flutter/foundation.dart';
import '../domain/models/location_tracking_state.dart';
import '../core/services/location_tracking_service.dart';

class LocationState extends ChangeNotifier {
  final LocationTrackingService _service;

  TrackingStatus _status = TrackingStatus.trackingDisabled;
  LocationPoint? _currentLocation;
  final List<LocationPoint> _routeTrail = [];
  String? _lastError;

  LocationState({LocationTrackingService? service})
      : _service = service ?? LocationTrackingService();

  TrackingStatus get status => _status;
  LocationPoint? get currentLocation => _currentLocation;
  List<LocationPoint> get routeTrail => List.unmodifiable(_routeTrail);
  String? get lastError => _lastError;

  Future<void> initializePermissions() async {
    _status = await _service.checkAndRequestPermissions();
    notifyListeners();
  }

  Future<void> startTracking(String tripId) async {
    final permStatus = await _service.checkAndRequestPermissions();
    if (permStatus != TrackingStatus.trackingDisabled) {
      _status = permStatus;
      notifyListeners();
      return;
    }

    _lastError = null;
    _status = TrackingStatus.trackingEnabled;
    notifyListeners();

    await _service.startTracking(
      tripId: tripId,
      onLocationCaptured: (point) {
        _currentLocation = point;
        _routeTrail.add(point);
        _lastError = null;
        notifyListeners();
      },
      onError: (err) {
        _lastError = err;
        notifyListeners();
      },
    );
  }

  Future<void> stopTracking() async {
    await _service.stopTracking();
    _status = TrackingStatus.trackingDisabled;
    notifyListeners();
  }

  void clearTrail() {
    _routeTrail.clear();
    notifyListeners();
  }
}
