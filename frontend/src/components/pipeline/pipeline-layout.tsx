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
        <div className="flex-1 bg-background relative p-0 overflow-hidden max-w-[1760px] w-full mx-auto flex flex-col border border-foreground/10">
          {/* Subtle corner elements matching Landing Page */}
          <div className="absolute top-2 left-2 w-1.5 h-1.5 bg-[#28C840] opacity-60 rounded-full z-10" />
          <div className="absolute top-2 right-2 w-1.5 h-1.5 bg-[#28C840] opacity-60 rounded-full z-10" />
          <div className="absolute bottom-2 left-2 w-1.5 h-1.5 bg-[#28C840] opacity-60 rounded-full z-10" />
          <div className="absolute bottom-2 right-2 w-1.5 h-1.5 bg-[#28C840] opacity-60 rounded-full z-10" />

          {children}
        </div>

        {/* Action Bar */}
        <div className="mt-4 flex items-center justify-between max-w-[1760px] w-full mx-auto">
          <button
            type="button"
            onClick={onBack}
            disabled={isFirst}
            className="px-6 py-2.5 border border-foreground/20 text-xs font-mono font-bold text-foreground/70 tracking-wider hover:text-foreground hover:border-foreground/50 rounded-sm transition-all disabled:opacity-30 disabled:cursor-not-allowed active:scale-[0.98]"
          >
            ← QUAY LẠI
          </button>

          <button
            type="button"
            onClick={onNext}
            disabled={isNextDisabled}
            className={`px-8 py-3 text-xs font-mono font-bold tracking-wider rounded-sm transition-all flex items-center gap-2 select-none ${isNextDisabled
                ? "bg-[#28C840]/30 text-white/50 cursor-not-allowed"
                : "bg-[#28C840] hover:bg-[#22B038] text-white shadow-[0_0_18px_rgba(40,200,64,0.22)] hover:scale-[1.02] active:scale-[0.98]"
              }`}
          >
            <span>{nextLabel}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
