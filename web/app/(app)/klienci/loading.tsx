import { SkeletonCard, SkeletonLine } from "@/components/ui/skeleton";

export default function LoadingClients() {
  return (
    <div className="min-h-screen bg-[#050607] p-6 space-y-4">
      <SkeletonCard>
        <SkeletonLine variant="title" />
        <SkeletonLine variant="sub" delay={120} />
      </SkeletonCard>
      <SkeletonCard>
        <SkeletonLine variant="sub" />
        {Array.from({ length: 8 }).map((_, i) => (
          <SkeletonLine
            key={i}
            variant="body"
            delay={i * 80 + 100}
          />
        ))}
      </SkeletonCard>
    </div>
  );
}
