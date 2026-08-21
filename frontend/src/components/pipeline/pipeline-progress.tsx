"use client";

import * as React from "react";
import { CampaignStage, CAMPAIGN_STAGES, StageStatus } from "@/types/campaign";

interface PipelineProgressProps {
  currentStage: CampaignStage;
  stageStatuses: Record<CampaignStage, StageStatus>;
  onStageClick: (stage: CampaignStage) => void;
}

const STATUS_STYLES: Record<StageStatus, { dot: string; text: string; border: string }> = {
  locked: { dot: "bg-foreground/10", text: "text-foreground/15", border: "border-foreground/8" },
  active: { dot: "bg-foreground", text: "text-foreground", border: "border-foreground/50" },
  processing: { dot: "bg-[#35ea52] animate-pulse", text: "text-[#35ea52]", border: "border-[#35ea52]/30" },
  completed: { dot: "bg-foreground/50", text: "text-foreground/50", border: "border-foreground/20" },
  failed: { dot: "bg-red-500", text: "text-red-400", border: "border-red-500/30" },
};

export const PipelineProgress: React.FC<PipelineProgressProps> = ({
  currentStage,
  stageStatuses,
  onStageClick,
}) => {
  return (
    <div className="border border-foreground/10 bg-background/50 p-3 relative">
      {/* Corner accents */}
      <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-foreground/20" />
      <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-foreground/20" />

      {/* Label */}
      <div className="flex items-center gap-2 mb-3">
        <div className="w-1.5 h-1.5 rounded-full bg-[#35ea52]" />
        <span className="text-[10px] font-mono text-foreground/25 tracking-widest">TIẾN ĐỘ.QUY TRÌNH</span>
        <div className="flex-1 h-px bg-foreground/8" />
        <span className="text-[10px] font-mono text-foreground/15">
          {CAMPAIGN_STAGES.findIndex((s) => s.id === currentStage) + 1}/{CAMPAIGN_STAGES.length}
        </span>
      </div>

      {/* Stage bar */}
      <div className="flex items-center gap-0.5">
        {CAMPAIGN_STAGES.map((stage, i) => {
          const status = stageStatuses[stage.id];
          const styles = STATUS_STYLES[status];
          const isCurrent = stage.id === currentStage;

          return (
            <React.Fragment key={stage.id}>
              <button
                type="button"
                onClick={() => status !== "locked" && onStageClick(stage.id)}
                disabled={status === "locked"}
                className={`flex items-center gap-1.5 px-2 py-1.5 border transition-all ${styles.border} ${
                  isCurrent ? "bg-foreground/5" : "bg-transparent"
                } ${status === "locked" ? "cursor-not-allowed opacity-40" : "cursor-pointer hover:bg-foreground/[0.03]"}`}
                title={stage.label}
              >
                <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${styles.dot}`} />
                <span className={`text-[10px] font-mono tracking-wider whitespace-nowrap hidden xl:inline ${styles.text}`}>
                  {stage.shortLabel}
                </span>
                <span className={`text-[10px] font-mono tracking-wider xl:hidden ${styles.text}`}>
                  {String(i + 1).padStart(2, "0")}
                </span>
              </button>
              {i < CAMPAIGN_STAGES.length - 1 && (
                <div className={`w-2 h-px shrink-0 ${
                  status === "completed" ? "bg-foreground/30" : "bg-foreground/8"
                }`} />
              )}
            </React.Fragment>
          );
        })}
      </div>

      <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-foreground/20" />
      <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-foreground/20" />
    </div>
  );
};
