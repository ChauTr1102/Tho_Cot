"use client";

import Link from "next/link";
import { ThemeToggle } from "@/components/theme-toggle";
import { Badge } from "@/components/ui/badge";
import { Activity, Layers, Terminal } from "lucide-react";

interface NavbarProps {
  isBackendConnected: boolean | null;
  serverVersion?: string;
}

export function Navbar({ isBackendConnected, serverVersion }: NavbarProps) {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold shadow-sm">
            <Layers className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold tracking-tight text-foreground">FastAPI + Next.js</span>
              <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-mono font-medium text-muted-foreground">
                MVP Base
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Backend Connection Indicator */}
          <div className="flex items-center gap-2">
            {isBackendConnected === null ? (
              <Badge variant="outline" className="flex items-center gap-1.5 border-amber-500/30 text-amber-600 dark:text-amber-400 bg-amber-500/10">
                <span className="h-1.5 w-1.5 animate-ping rounded-full bg-amber-500" />
                Connecting BE...
              </Badge>
            ) : isBackendConnected ? (
              <Badge variant="outline" className="flex items-center gap-1.5 border-emerald-500/30 text-emerald-600 dark:text-emerald-400 bg-emerald-500/10">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                FastAPI Live {serverVersion && `v${serverVersion}`}
              </Badge>
            ) : (
              <Badge variant="outline" className="flex items-center gap-1.5 border-rose-500/30 text-rose-600 dark:text-rose-400 bg-rose-500/10">
                <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
                Backend Offline
              </Badge>
            )}
          </div>

          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="hidden sm:inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
          >
            <Terminal className="h-3.5 w-3.5" />
            Swagger /docs
          </a>

          <div className="h-4 w-px bg-border hidden sm:block" />

          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
