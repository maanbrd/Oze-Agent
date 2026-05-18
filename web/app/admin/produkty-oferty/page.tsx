import { OwnerProductsDashboard } from "@/components/owner/owner-admin-views";
import { getCurrentAccount } from "@/lib/api/account";
import { getOwnerDashboardData } from "@/lib/api/admin-dashboard";

export const dynamic = "force-dynamic";

export default async function OwnerProductsOffersPage() {
  const account = await getCurrentAccount();
  const data = await getOwnerDashboardData(account);

  return <OwnerProductsDashboard data={data} />;
}
