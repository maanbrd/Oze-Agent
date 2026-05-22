import "server-only";

import type { AccountProfile } from "@/lib/api/account";

function acceptsStripeLivemode(stripeLivemode: boolean | null | undefined) {
  if (stripeLivemode === true) return true;
  if (stripeLivemode === false) {
    return (
      process.env.VERCEL_ENV === "preview" ||
      process.env.VERCEL_ENV === "development" ||
      process.env.NODE_ENV === "development"
    );
  }

  return false;
}

export function hasCurrentBillingAccess(
  profile: AccountProfile | null | undefined,
) {
  if (!profile) return false;
  const hasAccessStatus =
    profile.subscription_status === "trialing" ||
    (profile.subscription_status === "active" && Boolean(profile.activation_paid));
  if (!hasAccessStatus) {
    return false;
  }
  if (!acceptsStripeLivemode(profile.stripe_livemode)) return false;
  const periodEnd = profile.subscription_current_period_end
    ? Date.parse(profile.subscription_current_period_end)
    : Number.NaN;
  return Number.isFinite(periodEnd) && periodEnd > Date.now();
}
