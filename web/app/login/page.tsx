import type { Metadata } from "next";
import { AuthPage } from "@/components/auth/auth-page";

export const metadata: Metadata = {
  title: "Logowanie | Agent-OZE",
  description: "Logowanie do panelu Agent-OZE.",
};

export default function LoginPage() {
  return <AuthPage mode="login" />;
}
