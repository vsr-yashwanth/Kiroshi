import 'package:flutter/material.dart';
import '../core/constants/endpoints.dart';
import '../core/network/api_client.dart';
import '../domain/models/trip.dart';
import '../domain/models/itinerary.dart';

class TripState extends ChangeNotifier {
  final ApiClient _apiClient = ApiClient();

  List<TripModel> _trips = [];
  bool _isLoading = false;
  String? _errorMessage;

  List<TripModel> get trips => _trips;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  Future<void> fetchTrips() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final res = await _apiClient.get(Endpoints.trips);
      final List<dynamic> list = res as List<dynamic>;
      _trips = list.map((e) => TripModel.fromJson(e as Map<String, dynamic>)).toList();
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<TripModel?> createTrip({
    required String title,
    String? description,
    required DateTime startDate,
    required DateTime endDate,
    List<ItineraryModel> waypoints = const [],
  }) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final res = await _apiClient.post(
        Endpoints.trips,
        body: {
          'title': title,
          'description': description,
          'start_date': startDate.toIso8601String(),
          'end_date': endDate.toIso8601String(),
          'itineraries': waypoints.map((w) => w.toJson()).toList(),
        },
      );
      final newTrip = TripModel.fromJson(res);
      await fetchTrips();
      return newTrip;
    } catch (e) {
      _errorMessage = e.toString();
      notifyListeners();
      return null;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> startTrip(String tripId) async {
    try {
      await _apiClient.post(Endpoints.startTrip(tripId));
      await fetchTrips();
      return true;
    } catch (e) {
      _errorMessage = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<bool> stopTrip(String tripId) async {
    try {
      await _apiClient.post(Endpoints.stopTrip(tripId));
      await fetchTrips();
      return true;
    } catch (e) {
      _errorMessage = e.toString();
      notifyListeners();
      return false;
    }
  }
}
