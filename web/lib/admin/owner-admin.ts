import type { CurrentAccount } from "@/lib/api/account";

const OWNER_ADMIN_EMAILS = process.env.OWNER_ADMIN_EMAILS ?? "";

export function parseOwnerAdminEmails(raw = OWNER_ADMIN_EMAILS) {
  return new Set(
    raw
      .split(",")
      .map((email) => email.trim().toLowerCase())
      .filter(Boolean),
  );
}

export function isOwnerAdminEmail(email: string | null | undefined) {
  if (!email) return false;
  return parseOwnerAdminEmails().has(email.trim().toLowerCase());
}

export function isOwnerAdminAccount(account: CurrentAccount) {
  if (!account.authenticated) return false;
  return isOwnerAdminEmail(account.profile?.email ?? account.email);
}
