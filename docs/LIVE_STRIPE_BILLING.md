# Live Stripe Billing

Current live Stripe account: `The Great MF LLC`.

Live billing objects created for production:

- Product: `prod_UXoLeO22grkQXC` (`Agent OZE`)
- Price: `price_1TYiiiFzlMN5xVVkZdOzZRGo`
- Amount: `39900` minor units, `pln`, recurring monthly
- Trial: none
- Activation fee: none

The Stripe connector used during setup could not set `lookup_key`. Either set
`STRIPE_PRICE_MONTHLY=price_1TYiiiFzlMN5xVVkZdOzZRGo` in production, or set the
Stripe Dashboard lookup key `agent_oze_monthly_399` on the live price and use
that lookup key in env.

Required production env:

- Vercel: `STRIPE_SECRET_KEY=sk_live...`
- Vercel: `STRIPE_WEBHOOK_SECRET=whsec_...`
- Vercel: `STRIPE_PRICE_MONTHLY=price_1TYiiiFzlMN5xVVkZdOzZRGo`
- Vercel: `NEXT_PUBLIC_APP_URL=https://agent-oze.pl`
- Vercel: `FASTAPI_INTERNAL_BASE_URL=https://api-production-c066.up.railway.app`
- Vercel: `BILLING_INTERNAL_SECRET=<same value as Railway>`
- Railway API/bot: `BILLING_INTERNAL_SECRET=<same value as Vercel>`
- Railway API/bot: `MONTHLY_SUBSCRIPTION_PLN=399`
- Railway API/bot: `DASHBOARD_URL=https://agent-oze.pl`

Create the live Stripe webhook endpoint manually in Dashboard if it is not
already present:

- URL: `https://agent-oze.pl/api/webhooks/stripe`
- Events: `checkout.session.completed`,
  `checkout.session.async_payment_succeeded`, `invoice.payment_succeeded`,
  `invoice.payment_failed`, `customer.subscription.updated`,
  `customer.subscription.deleted`

After env changes, redeploy Vercel and restart/redeploy Railway API/bot. Run the
live smoke with a new webapp account, pay `399 zl`, confirm `cs_live`,
`invoice.paid`, active subscription, Supabase `stripe_livemode=true`, and a
future `subscription_current_period_end`. Then cancel/refund the smoke
subscription manually in Stripe Dashboard.
