"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Navbar } from "./Navbar";
import { Footer } from "./Footer";

export default function SiteShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() || "";
  const isDashboard = pathname.startsWith("/merchant/dashboard");
  const isCheckout = pathname.startsWith("/pay");

  if (isDashboard || isCheckout) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen flex flex-col justify-between">
      <Navbar />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  );
}
