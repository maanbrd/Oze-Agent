import { SkeletonCard, SkeletonLine } from "@/components/ui/skeleton";

export default function LoadingDashboard() {
  return (
    <div className="min-h-screen bg-[#050607] p-6 space-y-4">
      <div className="grid gap-4 lg:grid-cols-12">
        <div className="lg:col-span-8">
          <SkeletonCard>
            <SkeletonLine variant="title" />
            <SkeletonLine variant="sub" delay={120} />
            <SkeletonLine variant="body" delay={240} />
            <SkeletonLine variant="body" delay={360} />
          </SkeletonCard>
        </div>
        <div className="lg:col-span-4">
          <SkeletonCard>
            <SkeletonLine variant="title" />
            <SkeletonLine variant="body" delay={150} />
            <SkeletonLine variant="body" delay={300} />
          </SkeletonCard>
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i}>
            <SkeletonLine variant="sub" delay={i * 80} />
            <SkeletonLine variant="title" delay={i * 80 + 80} />
          </SkeletonCard>
        ))}
      </div>
      <SkeletonCard>
        <SkeletonLine variant="title" />
        <SkeletonLine variant="body" delay={150} />
        <SkeletonLine variant="body" delay={300} />
        <SkeletonLine variant="body" delay={450} />
      </SkeletonCard>
      <div className="grid gap-4 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <SkeletonCard key={i}>
            <SkeletonLine variant="title" delay={i * 80} />
            <SkeletonLine variant="body" delay={i * 80 + 100} />
          </SkeletonCard>
        ))}
      </div>
    </div>
  );
}
