"use client";

import { Sidebar } from "@/components/layout/Sidebar";
import { BottomNav } from "@/components/layout/BottomNav";
import { useSidebar } from "@/providers/SidebarProvider";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { collapsed } = useSidebar();

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main
        className={cn(
          "min-h-screen pb-16 md:pb-0 transition-[margin] duration-200",
          "md:ml-14", // icon-only sidebar on md
          collapsed ? "lg:ml-14" : "lg:ml-56" // full/collapsed on lg+
        )}
      >
        {children}
      </main>
      <BottomNav />
    </div>
  );
}
