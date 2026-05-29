"use client";

import { SubmitButton } from "@/components/ui/submit-button";

export function LogoutLink() {
  return (
    <form action="/logout" method="get">
      <SubmitButton pendingLabel="Wylogowuję…" variant="outline">
        Wyloguj
      </SubmitButton>
    </form>
  );
}
