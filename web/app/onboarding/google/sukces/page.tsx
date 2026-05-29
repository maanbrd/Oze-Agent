import { redirect } from "next/navigation";

export default async function GoogleSuccessPage() {
  redirect("/onboarding/przekierowuje?to=next");
}
