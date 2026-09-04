# Mobile Location Tracking — KIROSHI v0.2

> Status: IMPLEMENTED (v0.2) | Application: `apps/mobile`

---

## 1. Overview

The KIROSHI mobile application provides background and foreground GPS location streaming for active tourist journeys. Tracking is explicitly opt-in and bound to the lifecycle of an active trip.

```
┌─────────────────────────────────────────────────────────┐
│                      Trip Lifecycle                     │
│  [PLANNED] ──► [ACTIVE (Start Trip)] ──► [COMPLETED]   │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│            Location Tracking State Machine              │
│                                                         │
│     ┌──────────────────────────────────────────┐        │
│     │            TRACKING_DISABLED             │        │
│     └────────────────────┬─────────────────────┘        │
│                          │ User enables tracking        │
│                          ▼                              │
│            Check Permissions & GPS Hardware             │
│            ┌─────────────┴─────────────┐                │
│            ▼                           ▼                │
│   [PERMISSION_DENIED]         [LOCATION_UNAVAILABLE]    │
│            │                           │                │
│            │ (Permission Granted)      │ (GPS Turned On)│
│            └─────────────┬─────────────┘                │
│                          ▼                              │
│     ┌──────────────────────────────────────────┐        │
│     │             TRACKING_ENABLED             │        │
│     │  • Distance filter: 10 meters            │        │
│     │  • LocationAccuracy: high                │        │
│     │  • Push to POST /api/v1/location         │        │
│     └──────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Permissions Handling

The application queries permissions gracefully via `Geolocator`:
1. **Service Enabled Check**: Tests `Geolocator.isLocationServiceEnabled()`. If disabled, transitions state to `TrackingStatus.locationUnavailable` and prompts user to toggle device GPS.
2. **Permission Check**: Tests `Geolocator.checkPermission()`.
   - If `LocationPermission.denied`, requests permission via `Geolocator.requestPermission()`.
   - If `LocationPermission.deniedForever`, transitions state to `TrackingStatus.permissionDenied` and directs user to app settings.
3. **Tracking Authorization**: Location listening starts only after `LocationPermission.whileInUse` or `always` is granted.

---

## 3. Battery-Conscious Adaptive Tracking

Continuous GPS polling can rapidly drain mobile batteries, especially in wilderness and alpine environments. KIROSHI mitigates this with hardware-level distance filtering:
- **Distance Filter**: Configured to `10 meters`. The mobile OS suspends high-power GPS polling while the user remains stationary, waking the hardware only when displacement exceeds the threshold.
- **Accuracy Level**: Configured to `LocationAccuracy.high` for precise mountain and trail tracking.
- **Batching & Network Conservation**: In v0.2, positions exceeding the filter are transmitted to `POST /api/v1/location`. Network errors are logged gracefully to `LocationState.lastError` without interrupting ongoing GPS polling.

---

## 4. Security & Privacy Guarantees

- **No Covert Tracking**: Location is only polled when the user explicitly enables tracking on an active trip.
- **Trip Association**: Every location point is tied to an active `trip_id` owned by the authenticated tourist.
- **Encrypted Transmission**: All coordinates are transmitted over HTTPS / TLS to the API server.
- **Clear UI Indicators**: When tracking is active, the app displays a prominent status banner and real-time telemetry card suite indicating current coordinates, satellite fix accuracy, elevation, and ground speed.
