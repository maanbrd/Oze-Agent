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
const adminApiSource = readSource("../lib/api/admin-dashboard.ts");
const adminLayoutSource = readSource("../app/admin/layout.tsx");
const adminMirrorPreviewPath = new URL("../app/admin-mirror-preview/page.tsx", import.meta.url);

const adminRoutes = [
  ["/admin", "../app/admin/page.tsx", "Centrum Właściciela"],
  [
    "/admin/analityka-danych-oze",
    "../app/admin/analityka-danych-oze/page.tsx",
    "Analityka danych OZE",
  ],
  [
    "/admin/operacje-zdrowie",
    "../app/admin/operacje-zdrowie/page.tsx",
    "Operacje i zdrowie",
  ],
  ["/admin/klienci-konta", "../app/admin/klienci-konta/page.tsx", "Klienci i konta"],
  [
    "/admin/platnosci-subskrypcje",
    "../app/admin/platnosci-subskrypcje/page.tsx",
    "Płatności i subskrypcje",
  ],
  [
    "/admin/produkty-oferty",
    "../app/admin/produkty-oferty/page.tsx",
    "Produkty i oferty",
  ],
  ["/admin/integracje", "../app/admin/integracje/page.tsx", "Integracje"],
  ["/admin/raporty", "../app/admin/raporty/page.tsx", "Raporty"],
  ["/admin/ustawienia", "../app/admin/ustawienia/page.tsx", "Ustawienia"],
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
    const [, path, label] = routeConfig;
    const url = new URL(path, import.meta.url);
    const source = readSource(path);

    assert.equal(existsSync(url), true, `missing ${path}`);
    assert.equal(source.includes("CrmShell"), false, `${label} must not use CrmShell`);
    assert.equal(source.includes("@/components/crm-shell"), false, `${label} must not import CrmShell`);
  }
});

test("owner dashboard consumes admin API data and does not ship mock metrics", () => {
  assert.match(adminApiSource, /\/api\/admin\/dashboard/);
  assert.match(adminApiSource, /Authorization: `Bearer \$\{account\.accessToken\}`/);
  assert.match(ownerDashboardSource, /MRR/);
  assert.match(ownerDashboardSource, /Lejek Agent-OZE/);
  assert.match(ownerDashboardSource, /Przychód vs koszt AI/);
  assert.equal(ownerDashboardSource.includes("127 430"), false);
  assert.equal(ownerDashboardSource.includes("312"), false);
});

test("old admin mirror preview route is removed after production admin layer exists", () => {
  assert.equal(existsSync(adminMirrorPreviewPath), false);
});
