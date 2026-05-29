import { SkeletonCard, SkeletonLine, SkeletonCta } from "@/components/ui/skeleton";

export default function LoadingPaymentStep() {
  return (
    <main className="min-h-screen bg-[#050607] px-6 py-16 flex items-start justify-center">
      <div className="w-full max-w-6xl grid gap-6 lg:grid-cols-[0.9fr_0.7fr]">
        <SkeletonCard>
          <SkeletonLine variant="title" />
          <SkeletonLine variant="sub" delay={150} />
          <SkeletonLine variant="body" delay={300} />
          <SkeletonLine variant="body" delay={450} />
          <SkeletonCta delay={600} />
        </SkeletonCard>
        <SkeletonCard>
          <SkeletonLine variant="title" />
          <SkeletonLine variant="body" delay={150} />
          <SkeletonLine variant="body" delay={300} />
          <SkeletonCta delay={450} />
        </SkeletonCard>
      </div>
    </main>
  );
}
