import type { CurrentAccount } from "@/lib/api/account";
import { fastApiBaseUrl } from "@/lib/api/base-url";

export type OwnerCounterRow = {
  label: string;
  count: number;
  share_pct?: number;
  conversion_pct?: number;
};

export type OwnerIntegrationRow = {
  label: string;
  ok: number;
  total: number;
};

export type OwnerAttentionRow = {
  label: string;
  count: number;
  detail: string;
};

export type OwnerDashboardData = {
  business: {
    mrr_pln: number;
    active_paid_accounts: number;
    pending_payment_accounts: number;
    pending_payment_pln: number;
    canceled_accounts: number;
    ai_cost_usd_month: number;
    estimated_gross_margin_pln: number;
    active_7d_accounts: number;
  };
  funnel: Array<{ label: string; count: number; conversion_pct: number }>;
  oze: {
    offers_total: number;
    average_offer_price_pln: number;
    total_pv_kwp: number;
    total_storage_kwh: number;
    popular_offer_types: OwnerCounterRow[];
    top_cities: OwnerCounterRow[];
    crm_statuses: OwnerCounterRow[];
    components: OwnerCounterRow[];
  };
  operations: {
    system_status: string;
    integrations: OwnerIntegrationRow[];
    attention: OwnerAttentionRow[];
  };
  links: {
    sheets_url: string | null;
    calendar_url: string | null;
  };
  error?: string | null;
};

export function emptyOwnerDashboardData(error: string | null = null): OwnerDashboardData {
  return {
    business: {
      mrr_pln: 0,
      active_paid_accounts: 0,
      pending_payment_accounts: 0,
      pending_payment_pln: 0,
      canceled_accounts: 0,
      ai_cost_usd_month: 0,
      estimated_gross_margin_pln: 0,
      active_7d_accounts: 0,
    },
    funnel: [
      "Rejestracja",
      "Płatność",
      "Onboarding",
      "Google podpięte",
      "Telegram aktywny",
      "Pierwsze kontakty",
      "Pierwsza oferta",
    ].map((label) => ({ label, count: 0, conversion_pct: 0 })),
    oze: {
      offers_total: 0,
      average_offer_price_pln: 0,
      total_pv_kwp: 0,
      total_storage_kwh: 0,
      popular_offer_types: [],
      top_cities: [],
      crm_statuses: [],
      components: [],
    },
    operations: {
      system_status: "brak danych",
      integrations: [],
      attention: [],
    },
    links: {
      sheets_url: null,
      calendar_url: null,
    },
    error,
  };
}

export async function getOwnerDashboardData(
  account: CurrentAccount,
): Promise<OwnerDashboardData> {
  if (!account.authenticated || !account.accessToken) {
    return emptyOwnerDashboardData("Brak aktywnej sesji.");
  }

  const baseUrl = fastApiBaseUrl();
  if (!baseUrl) {
    return emptyOwnerDashboardData("Brak konfiguracji FASTAPI_INTERNAL_BASE_URL.");
  }

  try {
    const response = await fetch(`${baseUrl}/api/admin/dashboard`, {
      headers: {
        Authorization: `Bearer ${account.accessToken}`,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      return emptyOwnerDashboardData(`API admina zwróciło status ${response.status}.`);
    }

    return {
      ...emptyOwnerDashboardData(),
      ...((await response.json()) as OwnerDashboardData),
      error: null,
    };
  } catch {
    return emptyOwnerDashboardData("Nie udało się połączyć z API admina.");
  }
}
