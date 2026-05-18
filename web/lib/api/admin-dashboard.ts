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

export type OwnerDataQuality = "real" | "estimated" | "missing" | string;

export type OwnerTrendPoint = {
  date: string;
  mrr_pln: number;
  revenue_pln_month: number;
  ai_cost_usd_month: number;
  ai_cost_pln_month: number;
  gross_margin_after_ai_pln: number;
  active_paid_accounts: number;
  pending_payment_accounts: number;
  active_7d_accounts: number;
};

export type OwnerSyncStatus = {
  last_run_at: string | null;
  ok: boolean | null;
  skipped: boolean | null;
  contacts: number;
  calendar_events: number;
  errors: unknown[];
};

export type OwnerDashboardData = {
  business: {
    mrr_pln: number;
    revenue_pln_month: number;
    active_paid_accounts: number;
    pending_payment_accounts: number;
    pending_payment_pln: number;
    canceled_accounts: number;
    ai_cost_usd_month: number;
    ai_cost_pln_month: number;
    gross_margin_after_ai_pln: number;
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
  trends: OwnerTrendPoint[];
  sync: OwnerSyncStatus;
  data_quality: Record<string, OwnerDataQuality>;
  error?: string | null;
};

export function emptyOwnerDashboardData(error: string | null = null): OwnerDashboardData {
  return {
    business: {
      mrr_pln: 0,
      revenue_pln_month: 0,
      active_paid_accounts: 0,
      pending_payment_accounts: 0,
      pending_payment_pln: 0,
      canceled_accounts: 0,
      ai_cost_usd_month: 0,
      ai_cost_pln_month: 0,
      gross_margin_after_ai_pln: 0,
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
    trends: [],
    sync: {
      last_run_at: null,
      ok: null,
      skipped: null,
      contacts: 0,
      calendar_events: 0,
      errors: [],
    },
    data_quality: {
      mrr_pln: "missing",
      revenue_pln_month: "missing",
      pending_payment_pln: "missing",
      ai_cost_usd_month: "missing",
      ai_cost_pln_month: "missing",
      gross_margin_after_ai_pln: "missing",
      active_7d_accounts: "missing",
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

    const fallback = emptyOwnerDashboardData();
    const payload = (await response.json()) as Partial<OwnerDashboardData>;

    return {
      ...fallback,
      ...payload,
      business: {
        ...fallback.business,
        ...payload.business,
      },
      oze: {
        ...fallback.oze,
        ...payload.oze,
      },
      operations: {
        ...fallback.operations,
        ...payload.operations,
      },
      links: {
        ...fallback.links,
        ...payload.links,
      },
      sync: {
        ...fallback.sync,
        ...payload.sync,
      },
      data_quality: {
        ...fallback.data_quality,
        ...payload.data_quality,
      },
      trends: payload.trends ?? fallback.trends,
      funnel: payload.funnel ?? fallback.funnel,
      error: null,
    };
  } catch {
    return emptyOwnerDashboardData("Nie udało się połączyć z API admina.");
  }
}
