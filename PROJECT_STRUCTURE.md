# Project structure

The active application is the national workflow in `backend/app/national/`. Start it with `app.main:app`; install `backend/requirements-national.txt` for runtime dependencies.

```text
backend/
  app/main.py                    Active FastAPI entry point
  app/national/
    router.py                    HTTP endpoints and input validation
    geometry.py                  Area and national-boundary validation
    providers.py                 Satellite, environment and public context
    analysis.py                  Baseline forecasts and screening formulas
    insights.py                  Readable explanations and next steps
    local_ai.py                  Local vision and Ollama integrations
    engine.py                    Background assessment jobs
    store.py                     SQLite records and restart recovery
  data/national/                 Attributed boundary and ignored runtime data
  tests/test_national.py         Offline regression suite
  bootstrap_data.py              Boundary download and attribution
  check_workflow.py              Live submission-to-report verification
  setup_local_vision.py          Verified model/runtime download
  requirements-national.txt      Active runtime dependencies
  requirements-dev.txt           Runtime plus test dependencies
frontend/
  src/App.jsx                    Workspace, inputs and progress
  src/components/
    AssessmentMap.jsx            Satellite map and boundary selection
    AssessmentReport.jsx         Report tabs and evidence export
    EvidenceChart.jsx            Observed/projected vegetation
    LandBrief.jsx                Plain-language summary and history
    LocationHelp.jsx             Place lookup and photo assistant
  src/services/national.js       Active API client
  browser-check.mjs              Desktop/mobile verification
  photo-workflow-check.mjs       Photo AI through report export
  start-assessment-check.mjs     Visible validation and successful retry
  capture-docs.mjs               Documentation screenshot capture
.github/                         CI and contribution templates
docs/                            Data-source methodology and screenshots
Open-MineLand.cmd                 Windows one-click launcher
Open-MineLand.ps1                 Background service launcher
start-backend.ps1                 API-only launcher
start-frontend.cmd                Frontend-only launcher
start-local-ai.ps1                Local vision service launcher
```

## Local-only content

Dependencies, environments, assessment databases, uploaded photos, API/raster caches, generated overlays, logs, model weights and the downloaded runtime are excluded from Git. The country boundary and its source metadata are retained so offline geometry tests can run after cloning.

## Historical code

The earlier fixed-site dashboard is preserved in `backend/app/legacy_main.py`, other older modules, `frontend/src/LegacyApp.jsx`, older components and `document.md`. Legacy dependency manifests and Docker Compose are reference material, not part of the active national startup path.

See the [README](README.md) for setup and [data-source documentation](docs/DATA_SOURCES.md) for interpretation limits.
