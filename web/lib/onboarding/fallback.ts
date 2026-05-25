import "server-only";

import type { AccountProfile } from "@/lib/api/account";
import { hasCurrentBillingAccess } from "@/lib/billing/access";

export type FallbackOnboardingProgress = {
  completed: boolean;
  nextStep: string;
  access: {
    active: boolean;
    type: "paid" | "trial" | null;
    betaEligible: false;
  };
  steps: {
    payment: boolean;
    google: boolean;
    resources: boolean;
    telegram: boolean;
  };
};

function fallbackAccessType(profile: AccountProfile | null | undefined) {
  if (profile?.subscription_status === "trialing") return "trial";
  if (profile?.subscription_status === "active") return "paid";
  return null;
}

export function fallbackOnboardingProgress(
  profile: AccountProfile | null | undefined,
): FallbackOnboardingProgress {
  const payment = hasCurrentBillingAccess(profile);
  const completed = payment && Boolean(profile?.onboarding_completed);

  let nextStep = "/onboarding/platnosc";
  if (completed) {
    nextStep = "/dashboard";
  } else if (payment) {
    nextStep = "/onboarding/google";
  }

  return {
    completed,
    nextStep,
    access: {
      active: payment,
      type: payment ? fallbackAccessType(profile) : null,
      betaEligible: false,
    },
    steps: {
      payment,
      google: false,
      resources: false,
      telegram: false,
    },
  };
}
