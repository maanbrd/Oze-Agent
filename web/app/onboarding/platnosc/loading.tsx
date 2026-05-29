import { SkeletonCard, SkeletonLine, SkeletonCta } from "@/components/ui/skeleton";

export default function LoadingPaymentStep() {
  return (
    <main className="min-h-screen bg-[#050607] px-6 py-16 flex items-start justify-center">
      <div className="w-full max-w-2xl">
        <SkeletonCard>
          <SkeletonLine variant="title" />
          <SkeletonLine variant="sub" delay={150} />
          <SkeletonLine variant="body" delay={300} />
          <SkeletonLine variant="body" delay={450} />
          <SkeletonCta delay={600} />
        </SkeletonCard>
      </div>
    </main>
  );
}
