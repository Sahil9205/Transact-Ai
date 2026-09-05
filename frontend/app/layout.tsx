import type { Metadata } from "next";
import { Plus_Jakarta_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { ToastProvider } from "@/components/ui/Toast";
import SiteShell from "@/components/layout/SiteShell";

const sans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  weight: ["400", "500", "600", "700", "800"],
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "TransactAI — AI Commerce Execution Agent",
  description:
    "Provider-independent AI Commerce Execution Agent. Bridging autonomous assistants with deterministic verification and Razorpay settlements.",
  icons: {
    icon: "/logo_icon.png",
    shortcut: "/favicon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable}`}>
      <body className="min-h-screen flex flex-col antialiased selection:bg-[#FF203D] selection:text-white font-sans bg-[#FFF9F2] text-[#171717]">
        <ToastProvider>
          <SiteShell>{children}</SiteShell>
        </ToastProvider>
      </body>
    </html>
  );
}

