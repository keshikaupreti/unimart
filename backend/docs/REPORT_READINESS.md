# UniMart implementation and verification evidence

Verified on 21 September 2026. This records the implemented project and checks performed; it is not a substitute for your university's report template or marking rubric.

## Completed fixes

- Purchase, sale, review, dispute, and reporting workflows are available in the frontend. Open a listing to request a purchase or report a concern. Open the account menu → **Purchases, sales & reports** to manage transactions and follow moderation outcomes.
- Missing, malformed, and inaccessible transaction action targets return HTTP 404 instead of an uncaught exception.
- Registration uses Django's configured password validators and prevents client-supplied privilege escalation.
- Invalid UUIDs in review summaries return a validation error.
- Duplicate active disputes return a validation error. Dispute creation rechecks eligibility while holding a transaction lock; closed disputes cannot be reopened through the review action.
- Next.js forwards API POST requests with Django's required trailing slash. Media file paths are forwarded without an added slash.
- The missing global stylesheet was restored, including responsive layouts for the new workflows.
- Local dependencies were restored from the existing lockfiles after macOS offloaded dependency files caused read timeouts. Dependency versions were not changed.

## Verification results

| Check | Result | Evidence / scope |
| --- | --- | --- |
| Django automated tests | **20 passed** | Accounts, listings, saved items, transactions, reviews, moderation, REST/WebSocket chat, UUID models |
| Django system check | **Passed** | No issues identified |
| Migration consistency | **Passed** | `makemigrations --check --dry-run`: no changes detected |
| Frontend TypeScript | **Passed** | Standalone typecheck and build typecheck |
| Frontend automated tests | **6 passed** | Four browser workflow tests and two actual Next.js forwarding tests |
| Frontend build | **Passed** | Normal `npm run build`, using the project's default Turbopack build |
| Real API browser walkthrough | **Passed** | Login → report → purchase request → seller acceptance → dispute → completion → review |
| Mobile activity layout | **Passed** | Tested at 390 × 844; no horizontal dialog overflow |

Backend tests initially ran in an isolated environment installed from `uv.lock`; the normal `.venv` was then repaired using the same lockfile and its system check passed. The final frontend tests and build ran from the actual frontend project folder after its dependencies were repaired.

The four frontend workflow tests use mocked API responses to test UI behavior, role-specific actions, request payloads, and error handling. The routing tests use a local echo server to verify real forwarding. Separately, the real API walkthrough used two browser sessions and an isolated SQLite database; no existing project records were changed. The temporary test servers were stopped afterward.

## Screenshots

The screenshots use clearly labeled demonstration data from the isolated database:

- [Marketplace desktop](screenshots/marketplace-desktop.png)
- [Purchases, sales, disputes, and reports](screenshots/activity-desktop.png)
- [Mobile activity panel](screenshots/activity-mobile.png)

## Reproduce the checks

From `backend`:

```sh
.venv/bin/python manage.py test --noinput
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
```

From `frontend`:

```sh
npm run typecheck
npm run build
PLAYWRIGHT_CHANNEL=chrome npm test
```

The browser suite uses locally installed Google Chrome with the command above. Alternatively, run `npx playwright install chromium`, then `npm test`. Ports 3100 and 8101 must be available for the automated frontend tests.

## Final report scope

Describe implemented behavior accurately:

- Buyers and sellers arrange local meetups. Payments happen between participants; there is no online payment gateway.
- A seller confirms transaction completion. Each participant may then leave one review.
- Reports and disputes can be submitted and tracked from the frontend. Staff manage them through Django admin or the moderation API.
- REST and WebSocket chat are implemented and tested in the backend. The current frontend inbox refreshes message history every five seconds; do not describe the frontend as using WebSocket delivery.
- Categories and active meetup locations must be added through Django admin before the corresponding listing/purchase workflows can be demonstrated.
- The preview collection shown when the API is unavailable is demonstration data. Use a connected API for final functional screenshots and demonstrations.

For submission, fit this evidence into your required chapters: objectives and scope, requirements, architecture, database/ER diagram, use cases, implementation, test cases/results, screenshots, limitations, and future work. The grading rubric and report draft were not supplied, so academic formatting and completeness against that rubric remain to be checked.
