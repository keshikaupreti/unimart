# UniMart backend

Run the local API and WebSocket server with:

```sh
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

The API uses JWT access tokens from `POST /api/auth/login/`. All UniMart model IDs are UUIDs.

Removed listings are hidden from other users in listing searches and detail requests. Their seller and staff can still view them. Once a sale request is accepted, the listing is reserved and its seller cannot change its text, price, condition, or images. The seller can edit it again if that accepted transaction is cancelled; completed listings stay locked.

`DELETE /api/listings/<listing UUID>/` archives the listing by marking it removed. This preserves transaction history, rejects pending purchase requests, and clears saved bookmarks. A reserved listing must have its accepted transaction cancelled before staff can archive it; sellers cannot delete reserved listings.

## Saved listings

An authenticated buyer can save an available listing with `POST /api/saved-listings/` and a JSON body such as `{"listing":"<listing UUID>"}`. `GET /api/saved-listings/` returns only that user's saved items, including listing details. `DELETE /api/saved-listings/<saved UUID>/` removes one. A user cannot save their own listing or save the same listing twice.

## Listing conversations

An authenticated buyer starts a conversation with `POST /api/conversations/` and `{"listing":"<listing UUID>"}`. The API supports:

| Request | Purpose |
| --- | --- |
| `GET /api/conversations/` | List the buyer's or seller's conversations |
| `GET /api/conversations/<conversation UUID>/` | Get one conversation |
| `GET /api/conversations/<conversation UUID>/messages/` | Load paginated message history |
| `POST /api/conversations/<conversation UUID>/messages/` with `{"content":"Hello"}` | Send a message |

Only the buyer and seller in a conversation can access its messages. Messages are limited to 2,000 characters. A buyer can start one conversation per available listing; existing conversations remain accessible after a listing is reserved or sold.

For real-time updates, connect to `ws://127.0.0.1:8000/ws/conversations/<conversation UUID>/?token=<JWT access token>`. Send JSON like `{"type":"message","content":"Hello"}`. Both participants receive `{"type":"message","message":{...}}` when a message is sent through either the WebSocket or REST endpoint. A new access token is needed after the 30-minute JWT lifetime.

The WebSocket token is in the URL because browser WebSocket clients cannot set an `Authorization` header. Use this only for the local project demo; URL logging can expose tokens. The in-memory Channels layer delivers live events within one server process. Message history is stored in the database.

The importable `UniMart.postman_collection.json` tests the REST endpoints. Its folder 02b covers saved listings and conversations. WebSocket connections can be tested in Postman's WebSocket request tab with the URL above.

## Purchases, reviews, and moderation in the frontend

Run the sibling `frontend` app with `npm ci` and `npm run dev`. Listing details now include **Request to buy**, seller reviews, and **Report listing or seller**. The account menu's **Purchases, sales & reports** panel supports seller acceptance/rejection, cancellation, completion, reviews, disputes, and status tracking. Add at least one active meetup location in Django admin before requesting a purchase. Payment happens in person; this project does not process online payments.

Registration applies the configured Django password validators, including common-password and similarity checks. Refresh tokens rotate on refresh and are blacklisted on logout. Existing access tokens remain valid until their expiry.

A transaction action on a missing or inaccessible transaction returns HTTP 404. Reviews require a completed transaction and one review per participant. Disputes require an accepted or completed transaction, allow one active dispute per transaction, and cannot reopen a closed dispute through the review action. Staff manage reports and disputes through Django admin or the moderation API.

## Local verification

```sh
.venv/bin/python manage.py test --noinput
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
```

The backend tests cover account registration/login/profile/token rotation/logout, listing privacy and saved items, purchase lifecycle and access control, reviews, moderation permissions and dispute lifecycle, and REST/WebSocket chat. See `../frontend/README.md` for frontend checks and browser tests.

## Docker Compose

From this directory, run `docker compose up --build -d --wait` to start both the backend and sibling frontend. Open http://localhost:3000 for the app and http://localhost:8000/admin/ for administration. Docker uses its own persistent SQLite and media volumes, leaving your local data untouched.

See [Docker setup and verification](docker/README.md) for first-use steps, container checks, ports, and shutdown commands.
