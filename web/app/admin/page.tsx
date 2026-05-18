import { OwnerDashboard } from "@/components/owner/owner-dashboard";
import { getCurrentAccount } from "@/lib/api/account";
import { getOwnerDashboardData } from "@/lib/api/admin-dashboard";

export const dynamic = "force-dynamic";

export default async function OwnerAdminPage() {
  const account = await getCurrentAccount();
  const data = await getOwnerDashboardData(account);

  return <OwnerDashboard data={data} />;
}
