import { notFound } from "next/navigation";
import FaqPage from "@/app/(app)/faq/page";

export const dynamic = "force-dynamic";

export default function FaqPreviewPage() {
  if (process.env.NODE_ENV !== "development") {
    notFound();
  }

  return (
    <main className="min-h-screen bg-[#050607] px-5 py-6 text-zinc-100 lg:px-8">
      <FaqPage />
    </main>
  );
}
