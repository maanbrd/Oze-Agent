import { SkeletonCard, SkeletonLine } from "@/components/ui/skeleton";

export default function LoadingDashboard() {
  return (
    <div className="min-h-screen bg-[#050607] p-6 grid gap-4 md:grid-cols-2">
      <SkeletonCard>
        <SkeletonLine variant="title" />
        <SkeletonLine variant="body" delay={150} />
        <SkeletonLine variant="body" delay={300} />
      </SkeletonCard>
      <SkeletonCard>
        <SkeletonLine variant="title" />
        <SkeletonLine variant="body" delay={150} />
        <SkeletonLine variant="body" delay={300} />
      </SkeletonCard>
    </div>
  );
}
