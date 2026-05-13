"use client";

import { useFormStatus } from "react-dom";

export function ResourceSubmitButton() {
  const { pending } = useFormStatus();

  return (
    <button
      disabled={pending}
      className="w-fit rounded-full bg-[#3DFF7A] px-5 py-3 text-sm font-semibold text-black transition hover:bg-[#6DFF98] disabled:cursor-not-allowed disabled:opacity-60"
    >
      {pending ? "Tworzę zasoby..." : "Utwórz brakujące zasoby"}
    </button>
  );
}
