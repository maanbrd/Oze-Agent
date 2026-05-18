import { OwnerOperationsDashboard } from "@/components/owner/owner-admin-views";
import { getCurrentAccount } from "@/lib/api/account";
import { getOwnerDashboardData } from "@/lib/api/admin-dashboard";

export const dynamic = "force-dynamic";

export default async function OwnerOperationsPage() {
  const account = await getCurrentAccount();
  const data = await getOwnerDashboardData(account);

  return <OwnerOperationsDashboard data={data} />;
}
