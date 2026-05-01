import { LogoutButton } from "@/components/logout-button";

export default function OnboardingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <div className="fixed bottom-5 right-5 z-50">
        <LogoutButton className="bg-[#050607]/90 backdrop-blur" />
      </div>
      {children}
    </>
  );
}
