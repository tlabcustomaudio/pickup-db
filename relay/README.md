# pickup-db relay

RackNAM's Coil of Duty shares the captures its users save, with no GitHub account and no question asked (the users
accept the sharing notice once). The apps `POST` the profile JSON to this Cloudflare Worker at `/capture`; the Worker
opens the **Pickup capture** issue with the same body as the form, and the `capture-issue` Action does the rest (pull
request, review, index). The Worker holds the only write token, so no app carries one.

Deploy (once):

1. GitHub > Settings > Developer settings > fine-grained token: repository `pickup-db` only, **Issues: read and write**,
   **Contents: read**.
2. `npx wrangler login`, then in this folder `npx wrangler secret put GITHUB_TOKEN` (paste the token) and
   `npx wrangler deploy`.
3. The URL must match `shareRelay` in RackNAM `src/CoilOfDuty.cpp` (`https://pickup-db-relay.<subdomain>.workers.dev/capture`).

Replies: 201 opened, 409 already in the database or already submitted, 422 not a shareable profile, 502 GitHub failed;
the app retries 429/5xx and offline later. Test: `node relay/test.mjs` (fake GitHub, no network).
