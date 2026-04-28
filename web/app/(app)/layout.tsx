import { redirect } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { getCurrentAccount } from "@/lib/api/account";

export default async function LoggedInLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const account = await getCurrentAccount();
  if (!account.authenticated) {
    redirect("/login?next=/dashboard");
  }

  return <AppShell account={account}>{children}</AppShell>;
}
