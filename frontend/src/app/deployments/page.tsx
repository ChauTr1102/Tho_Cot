"use client";

import * as React from "react";
import { Rocket } from "lucide-react";

export default function DeploymentsPage() {
  return (
    <div className="min-h-screen flex flex-col bg-transparent pt-7 pb-6 relative text-foreground">
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-8 flex flex-col mt-10">
        <div className="space-y-6 animate-in fade-in flex-1">
          <div className="space-y-2">
            <div className="flex items-center gap-2 opacity-40">
              <div className="w-6 h-px bg-foreground" />
              <span className="text-[11px] font-mono tracking-widest">∞</span>
              <div className="flex-1 h-px bg-foreground" />
            </div>
            <h1 className="text-2xl font-bold tracking-wider text-foreground font-mono uppercase">DEPLOYMENTS</h1>
            <p className="text-sm text-foreground/35 font-mono tracking-wider">Manage deployed campaigns across platforms.</p>
          </div>
          <div className="p-12 text-center border border-dashed border-foreground/15 space-y-3 dot-grid">
            <Rocket className="h-8 w-8 text-foreground/20 mx-auto" />
            <p className="text-sm font-mono text-foreground/50 tracking-wider">NO_ACTIVE_DEPLOYMENTS</p>
          </div>
        </div>
      </main>
    </div>
  );
}
