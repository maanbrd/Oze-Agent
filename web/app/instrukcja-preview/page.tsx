import { notFound } from "next/navigation";
import { InstructionGuide } from "@/components/instruction-guide";

export const dynamic = "force-dynamic";

export default function InstructionPreviewPage() {
  if (process.env.NODE_ENV !== "development") {
    notFound();
  }

  return (
    <main className="min-h-screen bg-[#050607] px-5 py-6 text-zinc-100 lg:px-8">
      <InstructionGuide />
    </main>
  );
}
