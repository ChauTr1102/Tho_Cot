"use client";

import * as React from "react";
import { CampaignStage, CAMPAIGN_STAGES, StageStatus } from "@/types/campaign";

interface PipelineLayoutProps {
  currentStage: CampaignStage;
  stageStatuses: Record<CampaignStage, StageStatus>;
  onStageChange: (stage: CampaignStage) => void;
  onNext: () => void;
  onBack: () => void;
  isNextDisabled?: boolean;
  nextLabel?: string;
  children: React.ReactNode;
}

export const PipelineLayout: React.FC<PipelineLayoutProps> = ({
  currentStage,
  onNext,
  onBack,
  isNextDisabled = false,
  nextLabel = "BƯỚC.TIẾP",
  children,
}) => {
  const currentIndex = CAMPAIGN_STAGES.findIndex((s) => s.id === currentStage);
  const isFirst = currentIndex === 0;

  return (
    <div className="flex flex-col min-h-full space-y-4 animate-in fade-in duration-300">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        <div className="flex-1 border border-foreground/10 bg-background relative p-4 lg:p-8 overflow-y-auto max-w-7xl w-full mx-auto">
          <div className="absolute top-0 left-0 w-3 h-3 border-t border-l border-foreground/20" />
          <div className="absolute top-0 right-0 w-3 h-3 border-t border-r border-foreground/20" />
          
          {children}
          
          <div className="absolute bottom-0 left-0 w-3 h-3 border-b border-l border-foreground/20" />
          <div className="absolute bottom-0 right-0 w-3 h-3 border-b border-r border-foreground/20" />
        </div>

        {/* Action Bar */}
        <div className="mt-4 flex items-center justify-between max-w-7xl w-full mx-auto">
          <button
            type="button"
            onClick={onBack}
            disabled={isFirst}
            className="px-6 py-2 border border-foreground/20 text-xs font-mono text-foreground/50 tracking-widest hover:text-foreground hover:border-foreground/50 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          >
            QUAY LẠI
          </button>

          <button
            type="button"
            onClick={onNext}
            disabled={isNextDisabled}
            className="px-8 py-2.5 border-2 border-foreground bg-foreground text-white text-sm font-display font-bold tracking-widest hover:bg-transparent hover:text-foreground transition-all disabled:opacity-30 disabled:cursor-not-allowed disabled:bg-transparent disabled:text-foreground/30 disabled:border-foreground/20"
          >
            {nextLabel}
          </button>
        </div>
      </div>
    </div>
  );
};
