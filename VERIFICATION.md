# Verification record

Local verification performed on 6 November 2026. These checks establish operation and declared behaviour, not scientific model validation.

| Check | Result | Scope |
| --- | --- | --- |
| Backend offline regressions | 31 passed | Geometry, photo GPS, confirmation, persistence, missing evidence, forecasting, moisture interpretation, nearby-history scope and steep-ground constraints. |
| Frontend production build | Passed | React/Vite build; the large map-library chunk produces a non-blocking size warning. |
| Desktop/mobile browser workflow | Passed | Map initialization, coordinates, boundary/small-plot selection, confirmation invalidation, report tabs, export and layout. |
| Start-button rejection and recovery | Passed | Missing inputs give visible guidance; a real boundary rejection appears beside Start; correcting it starts a job and reaches its report. |
| Photo-to-report browser workflow | Passed | Photo upload, local vision, manual location, boundary import, submission, saved property reference, report, mobile layout and export. |
| Live public-provider assessment | Passed with explicit gaps | All nine sources were available in the final verification report. Missing acquisitions/product years keep the report partial. |
| Local vision runtime | Passed | SHA-256-verified downloads, loopback health and a real image request. |

The photo workflow uses a labelled map screenshot of a public Johannesburg engineering-verification extent, not a private ground photograph. Browser checks were also run outside the restricted execution network to inspect real map tiles.

The built-area check withheld redevelopment scoring. A rural check withheld solar scoring on steep terrain and explained low restoration potential, low rainfall and climatic water demand.

## Reproduce

Follow the [README testing instructions](README.md#testing). Offline regressions use temporary storage and mocked providers. Live/browser checks require running services, may create labelled verification records and need internet access. Photo checks additionally need the local vision assistant and a Johannesburg workflow-verification record.

GitHub Actions runs offline backend tests and the frontend build. Live-provider and browser checks are separate.

## Limits

- These tests do not validate national geolocation accuracy or a trained land-use suitability model.
- Local photo AI can misdescribe features; it does not determine coordinates, owners or scores.
- Provider outages, clouds and missing historical products remain possible.
- No title registry is connected; previous owners and exact activity history remain unverified.
- Regional environmental grids do not replace field measurements.
- This verification does not establish public multi-user deployment readiness.

Raw screenshots, logs and exports remain in ignored `artifacts/`. Only curated documentation captures are published.
