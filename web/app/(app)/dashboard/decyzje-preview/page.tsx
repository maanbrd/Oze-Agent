import type { Metadata } from "next";
import { DecyzjePreview } from "@/components/dashboard/decyzje-preview";

export const metadata: Metadata = {
  title: "Wymagają decyzji — prototyp | Agent OZE",
  description: "Prototyp UI dla zmiany statusu klienta z poziomu dashboardu.",
};

export default function DecyzjePreviewPage() {
  return <DecyzjePreview />;
}
