import { OwnerAccountsDashboard } from "@/components/owner/owner-admin-views";
import { getCurrentAccount } from "@/lib/api/account";
import { getOwnerDashboardData } from "@/lib/api/admin-dashboard";

export const dynamic = "force-dynamic";

export default async function OwnerCustomersAccountsPage() {
  const account = await getCurrentAccount();
  const data = await getOwnerDashboardData(account);

  return <OwnerAccountsDashboard data={data} />;
}
