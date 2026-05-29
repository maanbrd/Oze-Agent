import { SkeletonCard, SkeletonLine } from "@/components/ui/skeleton";

export default function LoadingClients() {
  return (
    <div className="min-h-screen bg-[#050607] p-6 space-y-3">
      {Array.from({ length: 8 }).map((_, i) => (
        <SkeletonCard key={i}>
          <SkeletonLine variant="title" delay={i * 80} />
          <SkeletonLine variant="sub" delay={i * 80 + 100} />
        </SkeletonCard>
      ))}
    </div>
  );
}
