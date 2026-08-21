"use client";

import * as React from "react";

interface AgentLoadingProps {
  agentName: string;
  steps?: string[];
  isComplete?: boolean;
}

export const AgentLoading: React.FC<AgentLoadingProps> = ({
  agentName,
  steps = [],
  isComplete = false,
}) => {
  const [visibleSteps, setVisibleSteps] = React.useState<number>(0);

  React.useEffect(() => {
    if (isComplete) { 
      setTimeout(() => setVisibleSteps(steps.length), 0);
      return; 
    }
    if (visibleSteps >= steps.length) return;
    const timer = setTimeout(() => setVisibleSteps((v) => v + 1), 400 + Math.random() * 300);
    return () => clearTimeout(timer);
  }, [visibleSteps, steps.length, isComplete]);

  return (
    <div className="border border-foreground/10 bg-background p-5 space-y-4 relative">
      <div className="absolute top-0 left-0 w-3 h-3 border-t border-l border-foreground/20" />
      <div className="absolute top-0 right-0 w-3 h-3 border-t border-r border-foreground/20" />

      {/* Header */}
      <div className="flex items-center gap-3">
        {!isComplete && <div className="w-2 h-2 rounded-full bg-[#35ea52] animate-pulse" />}
        {isComplete && <div className="w-2 h-2 rounded-full bg-foreground/50" />}
        <span className="text-xs font-mono text-foreground/50 tracking-widest uppercase">
          {isComplete ? `${agentName} — HOÀN THÀNH` : `${agentName} — ĐANG XỬ LÝ`}
        </span>
      </div>

      {/* Terminal output */}
      <div className="font-mono text-xs space-y-1 pl-2 border-l border-foreground/10">
        {steps.slice(0, visibleSteps).map((step, i) => (
          <div key={i} className="flex items-start gap-2">
            <span className="text-foreground/20 shrink-0">{String(i + 1).padStart(2, "0")}</span>
            <span className="text-foreground/50">{step}</span>
            <span className="text-[#35ea52] ml-auto shrink-0">✓</span>
          </div>
        ))}
        {!isComplete && visibleSteps < steps.length && (
          <div className="flex items-start gap-2">
            <span className="text-foreground/20 shrink-0">{String(visibleSteps + 1).padStart(2, "0")}</span>
            <span className="text-foreground/30 terminal-cursor">{steps[visibleSteps]}</span>
          </div>
        )}
        {!isComplete && visibleSteps >= steps.length && (
          <div className="flex items-center gap-2 text-foreground/20">
            <span className="animate-pulse">█</span>
            <span>Đang hoàn tất phân tích...</span>
          </div>
        )}
      </div>

      {/* Progress bar */}
      <div className="h-px bg-foreground/10 relative overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 bg-[#35ea52] transition-all duration-500"
          style={{ width: isComplete ? "100%" : `${(visibleSteps / Math.max(steps.length, 1)) * 100}%` }}
        />
      </div>

      <div className="absolute bottom-0 left-0 w-3 h-3 border-b border-l border-foreground/20" />
      <div className="absolute bottom-0 right-0 w-3 h-3 border-b border-r border-foreground/20" />
    </div>
  );
};
