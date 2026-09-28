# NETWORK_POLICY

**KSHAYA is designed as an offline-first, authorised-use-only platform.**

## 1. Default Network Behavior
By default, the application makes **NO outbound network calls**. 
The architecture consists solely of:
- A local Tauri desktop shell
- A local React UI communicating only with the local Python backend
- A local Python FastAPI backend, strictly bound to `127.0.0.1`

## 2. Binding Restrictions
The Python backend contains hardcoded startup checks. It must refuse to start if instructed to bind to any network interface other than `127.0.0.1` (localhost). This prevents local network exposure of the backend API.

## 3. Extending Network Capabilities (Future Modules)
Any future module or feature that requires network access must adhere to the following rules:
- Must be registered in a documented allowlist within this repository.
- Must be gated behind an explicit "Online Mode" setting.
- "Online Mode" must default to **OFF** for all new deployments and sessions.
- No analytics, telemetry, or remote crash reporting are permitted to bypass these restrictions.
