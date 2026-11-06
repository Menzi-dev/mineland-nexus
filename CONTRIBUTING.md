# Contributing

MineLand Nexus turns public land evidence into understandable reports. Contributions should improve reliability, clarity and traceability.

## Set up

Follow the [README](README.md#quick-start). The active application lives in `backend/app/national/` and `frontend/src/App.jsx`; older dashboard code is retained for reference.

Install backend test tools in your project environment:

```shell
python -m pip install -r backend/requirements-dev.txt
python backend/tests/test_national.py
```

Build the frontend from its directory:

```shell
npm ci
npm run build
```

Offline regression tests use temporary storage and mocked providers. They must not require credentials, modify real assessments, or contact live data services. For browser and live-provider checks, see [testing](README.md#testing).

## Change expectations

- Keep each change focused and describe the problem, resulting behaviour and validation in the pull request.
- Include regression coverage for meaningful processing, API or workflow changes.
- Preserve source links, retrieval dates, units, coverage and missing-data explanations.
- Distinguish observations, classifications, estimates, visual clues and user-provided information.
- Never convert an absent provider result into an invented score or history.
- Keep user photos, location records, tokens, databases, downloaded rasters and model weights out of commits.
- Avoid collecting personal ownership information without a reliable parcel-specific source and an appropriate integration.
- Keep the application bound to loopback by default.

## Reporting bugs

Include the steps to reproduce, the expected and actual result, operating system, Python/Node versions and any visible error text. Remove coordinates, photo metadata and personal information from logs or screenshots before sharing them. The issue template provides a checklist.

## Data and licensing

New providers need documented coverage, terms, attribution and failure behaviour. See [data sources](docs/DATA_SOURCES.md). No source-code licence has been selected by the repository owner; do not assume that public visibility grants reuse rights. Dataset and model licences are separate from application-code rights.
