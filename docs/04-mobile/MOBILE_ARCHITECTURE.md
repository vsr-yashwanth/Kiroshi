# Mobile Architecture — KIROSHI Tourist Client

> Status: IMPLEMENTED (v0.1 Foundation & Architecture) | Framework: Flutter / Dart

---

## 1. Clean Architecture Model

The mobile application is structured around Clean Architecture principles to keep UI concerns decoupled from network and business domain rules:

```text
apps/mobile/lib/
├── core/
│   ├── api/             # HTTP client, interceptors, auth token handling
│   ├── constants/       # App colors, typography, endpoints
│   ├── errors/          # Failure models and user-friendly error mappers
│   └── routing/         # Application route configuration
│
├── domain/
│   ├── models/          # Immutable domain models (User, Profile, Trip, Itinerary)
│   └── repositories/    # Abstract repository interfaces
│
├── application/
│   ├── auth/            # Auth state machine (unauthenticated, authenticating, authenticated)
│   ├── profile/         # Profile state management
│   └── trips/           # Trip lifecycle state management
│
└── presentation/
    ├── screens/         # Login, Register, Profile, TripList, CreateTrip, TripDetails
    └── widgets/         # Reusable buttons, cards, status chips, loading/empty states
```

---

## 2. Authentication State Machine

The client maintains an explicit, reactive authentication state:
- `AuthInitial`: Reading persisted JWT from secure storage.
- `AuthUnauthenticated`: Displaying onboarding / login / registration views.
- `AuthLoading`: Processing network handshake.
- `AuthAuthenticated`: Access token loaded; router redirects to tourist dashboard.
- `AuthError`: Displays actionable feedback (e.g. invalid credentials).

---

## 3. Planned Evolution (Future Milestones)

- **v0.2**: Foreground & background GPS stream provider, location permission handling, battery-optimized ingestion intervals.
- **v0.5**: Local SQLite/Isar database, offline event queue, background synchronization worker.
