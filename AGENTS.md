# Agent Instructions

Current task scope: AGX module only.

Rules:
- Read docs/agx_spec.md before implementation.
- Only modify files under agx/ plus root support files explicitly requested by the task.
- Do not modify esp32/ or raspberry-pi/ unless explicitly requested.
- Do not create agx/models/best.pt.
- Do not create agx/config.py.
- Do not create real secret files or real API keys.
- Create agx/config.example.py only for AGX configuration examples.
- All configurable values must come from config.py.
- Follow docs/agx_spec.md and the API contract exactly.
- ValueError returns HTTP 422.
- Other exceptions return HTTP 500.
