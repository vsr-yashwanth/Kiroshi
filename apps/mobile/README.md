# KIROSHI Mobile Client (Flutter)

> Status: IMPLEMENTED (v0.1 Foundation & Architecture) | Framework: Flutter 3.10+ (Dart 3.0+)

---

## 1. Overview
The KIROSHI Mobile application is the primary traveler client for tourists. It provides:
- Registration, Login, and secure session management.
- Digital profile setup (emergency contact next of kin, critical medical flags, consent).
- Trip planning: creation of trips with sequenced geographic waypoints.
- Live journey lifecycle: start/stop trip with immediate backend synchronization.

---

## 2. Directory Architecture
```text
lib/
├── core/
│   ├── constants/         # App palette, typography, API URLs
│   ├── errors/            # Custom application failures & mappers
│   ├── network/           # HTTP API client with Bearer auth headers
│   └── storage/           # Token and session secure storage
│
├── domain/
│   └── models/            # User, TouristProfile, Trip, Itinerary
│
├── application/
│   ├── auth_state.dart    # Authentication & user session state notifier
│   └── trip_state.dart    # Trip creation & lifecycle state notifier
│
└── presentation/
    ├── screens/           # Login, Register, Profile, TripList, CreateTrip, TripDetails
    └── widgets/           # LoadingView, EmptyView, ErrorView
```

---

## 3. Running Locally
When the Flutter SDK is installed:
```bash
# Get dependencies
flutter pub get

# Run on connected device or simulator
flutter run
```
