import { notFound, redirect } from "next/navigation";
import { OwnerAdminShell } from "@/components/owner/owner-admin-shell";
import { getCurrentAccount } from "@/lib/api/account";
import { isOwnerAdminAccount } from "@/lib/admin/owner-admin";

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const account = await getCurrentAccount();
  if (!account.authenticated) {
    redirect("/login?next=/admin");
  }

  if (!isOwnerAdminAccount(account)) {
    notFound();
  }

  return <OwnerAdminShell account={account}>{children}</OwnerAdminShell>;
}
