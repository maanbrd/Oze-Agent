import { OwnerUserProfilesDashboard } from "@/components/owner/owner-user-profiles";
import { getCurrentAccount } from "@/lib/api/account";
import { getOwnerUserProfile, getOwnerUserProfiles } from "@/lib/api/admin-user-profiles";

export const dynamic = "force-dynamic";

export default async function OwnerUserProfilesPage({
  searchParams,
}: {
  searchParams?: Promise<{ userId?: string }>;
}) {
  const account = await getCurrentAccount();
  const params = searchParams ? await searchParams : {};
  const data = await getOwnerUserProfiles(account);
  const selectedUserId = typeof params.userId === "string" ? params.userId : null;
  const selected = selectedUserId
    ? await getOwnerUserProfile(account, selectedUserId)
    : { profile: data.profiles[0] ?? null, error: null };

  return (
    <OwnerUserProfilesDashboard
      data={data}
      selectedProfile={selected.profile ?? data.profiles[0] ?? null}
      detailError={selected.error}
    />
  );
}
