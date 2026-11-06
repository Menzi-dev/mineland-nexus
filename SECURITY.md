# Security and privacy

MineLand Nexus currently targets local, single-user use. It has no application authentication or per-user record isolation. Keep the frontend, API and local vision service on loopback; do not expose them directly to the public internet.

## Report a vulnerability

Use the repository's **Security → Report a vulnerability** option if it is available. Otherwise contact the repository owner through the contact information they choose to publish. Do not post credentials, uploaded photos, exact personal locations or exploit details in a public issue.

## Local storage

- Assessment records, extracted GPS metadata and notes: `backend/data/national/assessments.sqlite`.
- Uploaded photo previews: `backend/data/national/media/`.
- Provider responses and processed raster windows: `backend/data/national/cache/`.
- Model weights and local inference runtime: `.local-ai/`.
- Runtime logs and verification outputs: `artifacts/`.

These paths are excluded from version control. Photo previews are saved without EXIF, while extracted GPS may still exist in the assessment database. Backups and report exports can also contain personal information.

Uploaded images are processed locally by the configured local vision assistant. Public data requests disclose the selected coordinates or extent to the relevant providers, and the browser requests map tiles from external map services. Local storage does not mean fully offline operation.

## Secrets

The active workflow requires no paid provider credentials. Legacy integration scripts must read credentials from the environment. Never commit `.env` files, keys or tokens. If a credential is exposed, revoke or rotate it at its provider; deleting it from the latest source is not sufficient if it was published in history.

Public deployment would require authentication, user isolation, durable job workers, quotas, storage controls, monitoring and a separate security review.
