import { SkeletonCard, SkeletonLine } from "@/components/ui/skeleton";

export default function LoadingCalendar() {
  return (
    <div className="min-h-screen bg-[#050607] p-6 space-y-4">
      {Array.from({ length: 5 }).map((_, dayIndex) => (
        <SkeletonCard key={dayIndex}>
          <SkeletonLine variant="title" delay={dayIndex * 100} />
          <SkeletonLine variant="sub" delay={dayIndex * 100 + 80} />
          <SkeletonLine variant="body" delay={dayIndex * 100 + 160} />
          <SkeletonLine variant="body" delay={dayIndex * 100 + 240} />
        </SkeletonCard>
      ))}
    </div>
  );
}
