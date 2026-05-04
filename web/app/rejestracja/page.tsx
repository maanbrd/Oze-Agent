import type { Metadata } from "next";
import { AuthPage } from "@/components/auth/auth-page";

export const metadata: Metadata = {
  title: "Rejestracja | Agent-OZE",
  description: "Rejestracja konta handlowca w Agent-OZE.",
};

export default function RegistrationPage() {
  return <AuthPage mode="register" />;
}
