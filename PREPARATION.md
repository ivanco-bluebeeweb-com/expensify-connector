# Expensify Connector -- Preparation (v0.1)

## API surface
Expensify Integration Server API (integrations.expensify.com) -- a single
POST endpoint (`https://integrations.expensify.com/Integration-Server/ExpensifyIntegrations`)
that dispatches on a `requestJobDescription.type` field: `create`, `get`,
`update`, `download`, `file`, `reconciliation`. Confirmed via
integrations.expensify.com/Integration-Server/doc (2026-08-29).

## Auth model
Static **partner credential pair**: `partnerUserID` + `partnerUserSecret`,
generated once from expensify.com/tools/integrations and included in the
`credentials` object of every request body -- NOT OAuth, no token
exchange, no expiry to manage. Simplest auth model of any connector built
this session (no refresh logic needed at all).

## Why BYOK
Same reasoning as every other connector here -- the user's own Expensify
company/policy data lives inside THEIR OWN Expensify account. The
partnerUserID/Secret pair is generated per Expensify account, not a
shared Imperal-wide credential.

## Scope for v1
Read-heavy: policies, employees (policy members), expense reports
(exportable via `get` job type for report data + `create` for the export
template `combinedReportData`), reimbursements. Write: create/update
policy employees. Actual report EXPORT to accounting is templated XML/CSV
and requires a chosen export template per policy -- out of scope for a
generic connector, flagged as explicit follow-up.

## Rate limits / known constraints
Expensify's Integration Server responds asynchronously for large jobs
(returns a `fileID` to poll via a `download` job) -- v1 handles the
synchronous small-payload path (policies/employees/report lists) which
returns inline JSON; the async download-by-fileID path is noted in
IDEAL_ONBOARDING.md as a v2 addition.
