import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { test } from "node:test";

function readSource(path) {
  const url = new URL(path, import.meta.url);
  return existsSync(url) ? readFileSync(url, "utf8") : "";
}

const crmLayoutSource = readSource("../app/(app)/layout.tsx");
const ownerHelperSource = readSource("../lib/admin/owner-admin.ts");
const ownerShellSource = readSource("../components/owner/owner-admin-shell.tsx");
const ownerDashboardSource = readSource("../components/owner/owner-dashboard.tsx");
const ownerAdminViewsSource = readSource("../components/owner/owner-admin-views.tsx");
const adminApiSource = readSource("../lib/api/admin-dashboard.ts");
const adminLayoutSource = readSource("../app/admin/layout.tsx");
const adminMirrorPreviewPath = new URL("../app/admin-mirror-preview/page.tsx", import.meta.url);
const ownerSectionPagePath = new URL("../components/owner/owner-section-page.tsx", import.meta.url);

const adminRoutes = [
  ["/admin", "../app/admin/page.tsx", "Centrum Właściciela", "OwnerDashboard"],
  [
    "/admin/analityka-danych-oze",
    "../app/admin/analityka-danych-oze/page.tsx",
    "Analityka danych OZE",
    "OwnerAnalyticsDashboard",
  ],
  [
    "/admin/operacje-zdrowie",
    "../app/admin/operacje-zdrowie/page.tsx",
    "Operacje i zdrowie",
    "OwnerOperationsDashboard",
  ],
  [
    "/admin/klienci-konta",
    "../app/admin/klienci-konta/page.tsx",
    "Klienci i konta",
    "OwnerAccountsDashboard",
  ],
  [
    "/admin/platnosci-subskrypcje",
    "../app/admin/platnosci-subskrypcje/page.tsx",
    "Płatności i subskrypcje",
    "OwnerBillingDashboard",
  ],
  [
    "/admin/produkty-oferty",
    "../app/admin/produkty-oferty/page.tsx",
    "Produkty i oferty",
    "OwnerProductsDashboard",
  ],
  ["/admin/integracje", "../app/admin/integracje/page.tsx", "Integracje", "OwnerIntegrationsDashboard"],
  ["/admin/raporty", "../app/admin/raporty/page.tsx", "Raporty", "OwnerReportsDashboard"],
  ["/admin/ustawienia", "../app/admin/ustawienia/page.tsx", "Ustawienia", "OwnerSettingsDashboard"],
];

test("CRM private layout redirects owner admins before onboarding and before CrmShell", () => {
  const adminCheckIndex = crmLayoutSource.indexOf("isOwnerAdminAccount(account)");
  const adminRedirectIndex = crmLayoutSource.indexOf('redirect("/admin")');
  const onboardingIndex = crmLayoutSource.indexOf("const onboardingStatus = await getOnboardingStatus()");
  const crmShellIndex = crmLayoutSource.indexOf("<CrmShell");

  assert.match(crmLayoutSource, /import \{ isOwnerAdminAccount \} from "@\/lib\/admin\/owner-admin"/);
  assert.notEqual(adminCheckIndex, -1);
  assert.notEqual(adminRedirectIndex, -1);
  assert.notEqual(onboardingIndex, -1);
  assert.notEqual(crmShellIndex, -1);
  assert.ok(adminCheckIndex < onboardingIndex);
  assert.ok(adminRedirectIndex < onboardingIndex);
  assert.ok(adminRedirectIndex < crmShellIndex);
});

test("owner admin email helper is driven by OWNER_ADMIN_EMAILS", () => {
  assert.match(ownerHelperSource, /OWNER_ADMIN_EMAILS/);
  assert.match(ownerHelperSource, /isOwnerAdminAccount/);
  assert.match(ownerHelperSource, /toLowerCase\(\)/);
  assert.match(ownerHelperSource, /split\(","\)/);
});

test("owner admin shell is separate from CrmShell and has real route tabs", () => {
  assert.equal(ownerShellSource.includes("CrmShell"), false);
  assert.match(adminLayoutSource, /OwnerAdminShell/);
  assert.match(adminLayoutSource, /notFound\(\)/);
  assert.match(adminLayoutSource, /isOwnerAdminAccount/);

  for (const routeConfig of adminRoutes) {
    const [route, , label] = routeConfig;
    assert.equal(ownerShellSource.includes(route), true, `missing ${route}`);
    assert.equal(ownerShellSource.includes(label), true, `missing ${label}`);
  }
});

test("all owner admin tabs are real subpages outside the CRM app layout", () => {
  for (const routeConfig of adminRoutes) {
    const [, path, label, componentName] = routeConfig;
    const url = new URL(path, import.meta.url);
    const source = readSource(path);

    assert.equal(existsSync(url), true, `missing ${path}`);
    assert.equal(source.includes("CrmShell"), false, `${label} must not use CrmShell`);
    assert.equal(source.includes("@/components/crm-shell"), false, `${label} must not import CrmShell`);
    assert.equal(source.includes("OwnerSectionPage"), false, `${label} must not use placeholder section page`);
    assert.match(source, new RegExp(componentName), `${label} must render its admin dashboard component`);
  }
});

test("owner admin subpages use dashboard views and the old placeholder component is gone", () => {
  assert.equal(existsSync(ownerSectionPagePath), false);
  assert.match(ownerAdminViewsSource, /OwnerAnalyticsDashboard/);
  assert.match(ownerAdminViewsSource, /OwnerOperationsDashboard/);
  assert.match(ownerAdminViewsSource, /OwnerAccountsDashboard/);
  assert.match(ownerAdminViewsSource, /OwnerBillingDashboard/);
  assert.match(ownerAdminViewsSource, /OwnerProductsDashboard/);
  assert.match(ownerAdminViewsSource, /OwnerIntegrationsDashboard/);
  assert.match(ownerAdminViewsSource, /OwnerReportsDashboard/);
  assert.match(ownerAdminViewsSource, /OwnerSettingsDashboard/);

  for (const [, path, label] of adminRoutes.slice(1)) {
    const source = readSource(path);

    assert.match(source, /getOwnerDashboardData/, `${label} must fetch admin dashboard data`);
    assert.match(source, /dynamic = "force-dynamic"/, `${label} must be dynamic`);
  }
});

test("owner dashboard consumes admin API data and does not ship mock metrics", () => {
  assert.match(adminApiSource, /\/api\/admin\/dashboard/);
  assert.match(adminApiSource, /Authorization: `Bearer \$\{account\.accessToken\}`/);
  assert.match(ownerDashboardSource, /MRR/);
  assert.match(ownerDashboardSource, /Lejek Agent OZE/);
  assert.match(ownerDashboardSource, /Przychód vs koszt AI/);
  assert.match(ownerAdminViewsSource, /Najczęstsze komponenty ofert/);
  assert.match(ownerAdminViewsSource, /Status integracji/);
  assert.match(ownerAdminViewsSource, /Przychód vs koszt AI/);
  assert.equal(ownerDashboardSource.includes("127 430"), false);
  assert.equal(ownerDashboardSource.includes("312"), false);
  assert.equal(ownerAdminViewsSource.includes("127 430"), false);
  assert.equal(ownerAdminViewsSource.includes("312"), false);
});

test("old admin mirror preview route is removed after production admin layer exists", () => {
  assert.equal(existsSync(adminMirrorPreviewPath), false);
});
