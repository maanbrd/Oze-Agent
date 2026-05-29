import { SkeletonCard, SkeletonLine } from "@/components/ui/skeleton";

export default function LoadingCalendar() {
  return (
    <div className="min-h-screen bg-[#050607] p-6 grid gap-3 md:grid-cols-7">
      {Array.from({ length: 14 }).map((_, i) => (
        <SkeletonCard key={i}>
          <SkeletonLine variant="sub" delay={i * 60} />
          <SkeletonLine variant="body" delay={i * 60 + 80} />
        </SkeletonCard>
      ))}
    </div>
  );
}
