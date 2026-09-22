# UniMart frontend

Install the versions recorded in `package-lock.json` with `npm ci`, then run `npm run dev`. Start the Django API on port 8000. The frontend opens on port 3000 and forwards API and media requests to Django.

## Marketplace workflows

- Open an available listing and choose **Request to buy**. Select a meetup location and a future time. Times are entered in your browser's local timezone and sent to the API in UTC.
- Open your account menu → **Purchases, sales & reports** to track requests. Sellers can accept or reject pending requests. Buyers can cancel pending requests; either participant can cancel accepted requests. Sellers confirm completion after the handover.
- After completion, each participant can leave one review. Seller reviews appear in listing details.
- Participants can open a dispute for accepted or completed transactions. Only one active dispute is allowed per transaction. Dispute status and moderator notes appear in activity.
- Choose **Report listing or seller** in listing details to submit a concern. Track its status in activity. Staff review reports and disputes using the Django admin or moderation API.
- A Django administrator must add categories and active meetup locations before users can list items and request purchases. No payment is collected by the app.

## Verification

```sh
npm run typecheck
npm run build
npx playwright install chromium
npm test
```

If Google Chrome is already installed, use `PLAYWRIGHT_CHANNEL=chrome npm test` to avoid downloading a browser. Tests start a local Next.js server on port 3100 and an API echo fixture on port 8101.

Routing tests verify POST bodies, Django trailing slashes, and media paths through the real Next.js forwarding layer. The browser workflow tests mock API responses to check purchase, sale, review, report, dispute, and error-handling interactions. The Django test suite separately verifies API behavior and permissions. These checks do not replace a final demonstration with the frontend connected to the real API.
