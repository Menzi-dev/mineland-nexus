# MineLand Nexus frontend

React national assessment workspace. See the [project README](../README.md) for the complete workflow, real data sources, scientific limits and setup.

```powershell
# Start the national FastAPI service first, then:
npm.cmd ci
npm.cmd run dev
```

Open http://127.0.0.1:5173. `/api` and `/health` are proxied to port 8000. To use a different backend, set `VITE_API_BASE_URL` as shown in `.env.example`.

```powershell
npm.cmd run build
npm.cmd audit
node browser-check.mjs
```

The browser check requires the backend/frontend running and Microsoft Edge installed. Maps and reports load on demand. The active workflow uses `services/national.js`, `AssessmentMap`, `AssessmentReport` and `EvidenceChart`. Older dashboard components are retained as historical reference and are not rendered by the active application.
