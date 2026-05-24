# Google OAuth + Meta Ads Readiness

_Last updated: 24.05.2026_

## Current state

- Google OAuth code requests:
  - `https://www.googleapis.com/auth/spreadsheets`
  - `https://www.googleapis.com/auth/calendar`
  - `https://www.googleapis.com/auth/drive.file`
  - `https://www.googleapis.com/auth/gmail.send`
- Public legal pages are live in the web app:
  - `/polityka-prywatnosci`
  - `/regulamin`
- Public legal operator for this verification pass:
  - `GREAT MF LLC`
  - EIN `36-5120312`
  - `810 Pony Express Rd, Cheyenne, WY 82009, USA`
  - Source document: `/Users/mansoniasty/Downloads/EIN229.pdf`
- Later B2B/team contracts are not covered by the public signup terms. They
  require a separate signed B2B agreement.
- Later migration to a Polish operating entity requires updated legal pages,
  user notice, and a new Google OAuth consent review if Google-facing legal
  identity changes materially.
- Meta Ads target account is `Agent-OZE (958523370306013)` under
  `business_id=1342119567777973`.
- `Fortnite Merch` is excluded. Do not pay balance, request review, activate,
  or change anything on that account.

## Google OAuth verification checklist

1. In Google Cloud Console, open the OAuth consent / Branding configuration.
2. Confirm app identity:
   - App name: `Agent OZE`
   - Support email: `support@agent-oze.pl` or the configured owner support email
   - Operator shown in legal pages: `GREAT MF LLC`
   - Homepage URL: production `https://agent-oze.pl/`
   - Privacy policy URL: `https://agent-oze.pl/polityka-prywatnosci`
   - Terms URL: `https://agent-oze.pl/regulamin`
3. Confirm authorized domain:
   - `agent-oze.pl` must be verified in Google Search Console.
4. Confirm OAuth client redirect URI:
   - It must exactly match Railway `GOOGLE_REDIRECT_URI`.
   - Current backend route is `/auth/google/callback`.
5. Add the exact scopes from `oze-agent/shared/google_auth.py`.
6. Submit scope justifications:
   - Sheets: create, read and update the user's CRM spreadsheet.
   - Calendar: create a dedicated Agent OZE calendar, create/read/update sales
     actions and show the day plan.
   - Drive file: create/use customer photo folders and files created by the app.
   - Gmail send: send confirmed offer PDFs from the user's Gmail after
     `✅ Wysłać`.
7. Publish the app to production and submit for Google verification.

## Legal review checklist

Before paid public launch, a Polish lawyer should review:

1. GREAT MF LLC as temporary non-EU operator for Polish/EOG users.
2. RODO/GDPR information duties, transfer language and supervisory authority
   wording.
3. Consumer withdrawal wording for digital services and subscription renewal.
4. Liability limits split between consumers and business users.
5. Separate B2B/team agreement template.
6. Future operator migration path from GREAT MF LLC to a Polish entity.

## Business benefits captured in the public documents

The current legal pages intentionally reserve these review-safe benefits:

- product analytics and operational metrics;
- AI usage/cost analysis;
- admin mirror for owner operations;
- short-term conversation history for bot memory;
- admin-only user behavior profiles;
- aggregated/anonymized product benchmarks;
- workflow profiling without solely automated legal effects;
- use of feedback and suggestions for product development;
- marketing email and phone contact through separate optional consents;
- case studies, logo use and public references only with separate consent or
  agreement.

Hard boundary: Google API data is not used for ads, retargeting, data sale,
data brokers, credit scoring, or hidden monetization outside the user-facing
service.

## Google review demo video script

Record a short end-to-end video using a test account and fictional data:

1. Open the production homepage and show links to privacy policy and terms.
2. Register or log in.
3. Start onboarding and click Google connection.
4. Show Google OAuth consent screen with all requested scopes visible.
5. Complete OAuth and return to `/onboarding/google/sukces`.
6. Create Google resources: Sheets, Calendar, Drive.
7. Pair Telegram.
8. In Telegram, add a fictional client and confirm `✅ Zapisać`.
9. Show the created Sheets row.
10. Add a fictional meeting and confirm `✅ Zapisać`.
11. Show the created Calendar event.
12. Upload a fictional photo and confirm `✅ Zapisać`.
13. Show the created/used Drive folder.
14. Send a test offer to a controlled email and confirm `✅ Wysłać`.
15. Show Gmail sent state or the bot success confirmation.

## Meta Ads readiness checklist

Use only the Agent OZE ad account:

- Business ID: `1342119567777973`
- Ad account: `Agent-OZE (958523370306013)`
- Page asset seen in Business Suite: `Agent OZE`

Before launching the first campaign:

1. Open Billing & payments for `Agent-OZE (958523370306013)`.
2. Add a payment method.
3. Fill business info if Meta requires it. Current observed state on 24.05.2026:
   - Current balance: `0.00 zł`
   - Payment methods: none
   - Business name: `-`
   - Country/address: Poland
   - Currency: Polish Zloty PLN
4. Re-open Account Quality for the Agent OZE account and confirm no restrictions.
5. Create a draft campaign only after billing is configured.

Do not use or repair `Fortnite Merch` for Agent OZE campaigns.
