import 'dart:async';
import 'package:http/http.dart' as http;
import '../constants/endpoints.dart';

class ConnectivityService {
  final http.Client _httpClient;
  final Duration checkTimeout;

  bool _isBackendReachable = true;
  Timer? _periodicCheckTimer;
  final _statusController = StreamController<bool>.broadcast();

  ConnectivityService({
    http.Client? httpClient,
    this.checkTimeout = const Duration(seconds: 3),
  }) : _httpClient = httpClient ?? http.Client();

  bool get isBackendReachable => _isBackendReachable;
  Stream<bool> get onConnectivityChanged => _statusController.stream;

  void startMonitoring({Duration interval = const Duration(seconds: 15)}) {
    _periodicCheckTimer?.cancel();
    _periodicCheckTimer = Timer.periodic(interval, (_) async {
      await checkBackendReachable();
    });
    // Immediate initial check
    checkBackendReachable();
  }

  void stopMonitoring() {
    _periodicCheckTimer?.cancel();
    _periodicCheckTimer = null;
  }

  Future<bool> checkBackendReachable() async {
    bool reachable = false;
    try {
      final url = Uri.parse(Endpoints.health);
      final response = await _httpClient.get(url).timeout(checkTimeout);
      reachable = (response.statusCode == 200);
    } catch (_) {
      reachable = false;
    }

    if (reachable != _isBackendReachable) {
      _isBackendReachable = reachable;
      _statusController.add(_isBackendReachable);
    }

    return reachable;
  }

  void dispose() {
    stopMonitoring();
    _statusController.close();
  }
}
