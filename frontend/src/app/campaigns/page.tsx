"use client";

import * as React from "react";
import { CampaignStage, StageStatus, CAMPAIGN_STAGES } from "@/types/campaign";
import { PipelineLayout } from "@/components/pipeline/pipeline-layout";
import { StageProductInput } from "@/components/pipeline/stage-product-input";
import { StageResearch } from "@/components/pipeline/stage-research";
import { StagePositioning } from "@/components/pipeline/stage-positioning";
import { StageContentGeneration } from "@/components/pipeline/stage-content-generation";
import { StageQAGate } from "@/components/pipeline/stage-qa-gate";
import { StageFinalOutput } from "@/components/pipeline/stage-final-output";
import { StageUserReview } from "@/components/pipeline/stage-user-review";
import { StagePackage } from "@/components/pipeline/stage-package";
import { StageDeploy } from "@/components/pipeline/stage-deploy";
import { Plus, FolderKanban } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { createInitialResearchSubmission, validateResearchSubmission, type ResearchCampaignPlan, type ResearchSubmission } from "@/types/research";

export default function CampaignsPage() {
  // Pipeline State
  const [isCreatingCampaign, setIsCreatingCampaign] = React.useState(false);
  const [currentStage, setCurrentStage] = React.useState<CampaignStage>("product_input");
  const [researchSubmission, setResearchSubmission] = React.useState<ResearchSubmission>(createInitialResearchSubmission);
  const [researchPlan, setResearchPlan] = React.useState<ResearchCampaignPlan | null>(null);
  const [researchLoading, setResearchLoading] = React.useState(false);
  const [researchError, setResearchError] = React.useState<string | null>(null);

  // Mock statuses where current is active, previous are completed, next are locked
  const stageStatuses = React.useMemo(() => {
    const statuses: Partial<Record<CampaignStage, StageStatus>> = {};
    const currentIndex = CAMPAIGN_STAGES.findIndex(s => s.id === currentStage);

    CAMPAIGN_STAGES.forEach((stage, index) => {
      if (index < currentIndex) statuses[stage.id] = "completed";
      else if (index === currentIndex) statuses[stage.id] = "active";
      else statuses[stage.id] = "locked";
    });

    return statuses as Record<CampaignStage, StageStatus>;
  }, [currentStage]);

  const runResearch = async () => {
    const validationErrors = validateResearchSubmission(researchSubmission);
    if (validationErrors.length) {
      toast.error(validationErrors[0]);
      return false;
    }
    setResearchLoading(true);
    setResearchError(null);
    setCurrentStage("research");
    try {
      setResearchPlan(await api.runResearch(researchSubmission));
      return true;
    } catch (error) {
      setResearchError(error instanceof Error ? error.message : "Research backend không phản hồi.");
      return false;
    } finally {
      setResearchLoading(false);
    }
  };

  const handleNextStage = () => {
    if (currentStage === "product_input") {
      void runResearch();
      return;
    }
    const currentIndex = CAMPAIGN_STAGES.findIndex(s => s.id === currentStage);
    if (currentIndex < CAMPAIGN_STAGES.length - 1) {
      setCurrentStage(CAMPAIGN_STAGES[currentIndex + 1].id);
    }
  };

  const handlePrevStage = () => {
    const currentIndex = CAMPAIGN_STAGES.findIndex(s => s.id === currentStage);
    if (currentIndex > 0) {
      setCurrentStage(CAMPAIGN_STAGES[currentIndex - 1].id);
    }
  };

  return (
    <div className="min-h-screen bg-transparent text-foreground/80 flex relative">
      {/* Global Corner Frame Accents */}
      <div className="fixed top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-foreground/20 z-50 pointer-events-none" />
      <div className="fixed top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-foreground/20 z-50 pointer-events-none" />
      <div className="fixed bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-foreground/20 z-50 pointer-events-none" />
      <div className="fixed bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-foreground/20 z-50 pointer-events-none" />

      {/* Top Status Bar */}
      <div className="fixed top-0 left-0 right-0 z-40 border-b border-foreground/10 bg-background/90 backdrop-blur-sm">
        <div className="flex items-center justify-between px-12 py-1.5">
          <div className="flex items-center gap-4 text-[10px] font-mono text-foreground/30 tracking-widest">
            <span>CAIBS.AI.ADS</span>
            <div className="w-1 h-1 bg-foreground/20 rounded-full" />
            <span>EST.2025</span>
          </div>
          <div className="flex items-center gap-4 text-[10px] font-mono text-foreground/25 tracking-widest">
            <span>LAT: 10.7626°</span>
            <div className="w-1 h-1 bg-foreground/15 rounded-full" />
            <span>LONG: 106.6602°</span>
          </div>
        </div>
      </div>

      {/* Bottom Status Bar */}
      <div className="fixed bottom-0 left-0 right-0 z-40 border-t border-foreground/10 bg-background/90 backdrop-blur-sm">
        <div className="flex items-center justify-between px-12 py-1.5">
          <div className="flex items-center gap-4 text-[10px] font-mono text-foreground/25 tracking-widest">
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-[#35ea52] animate-pulse" />
              <span>HỆ THỐNG.HOẠT ĐỘNG</span>
            </div>
            <span>V2.0.0</span>
          </div>
          <div className="flex items-center gap-4 text-[10px] font-mono text-foreground/20 tracking-widest">
            <span>◐ LÕI.ĐA.TÁC.TỬ</span>
            <div className="flex gap-1">
              <div className="w-1 h-1 bg-foreground/40 rounded-full animate-pulse" />
              <div className="w-1 h-1 bg-foreground/25 rounded-full animate-pulse" style={{ animationDelay: "0.2s" }} />
              <div className="w-1 h-1 bg-foreground/10 rounded-full animate-pulse" style={{ animationDelay: "0.4s" }} />
            </div>
            <span>KHUNG: ∞</span>
          </div>
        </div>
      </div>

      {/* Main Workspace Area */}
      <main className="flex-1 min-w-0 flex flex-col min-h-screen bg-transparent pt-7 pb-6">
        <div className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-8 flex flex-col">

          {/* TAB: CAMPAIGNS */}
          {!isCreatingCampaign && (
            <div className="space-y-6 animate-in fade-in flex-1">
              <div className="flex items-end justify-between">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 opacity-40">
                    <div className="w-6 h-px bg-foreground" />
                    <span className="text-[11px] font-mono tracking-widest">∞</span>
                    <div className="flex-1 h-px bg-foreground" />
                  </div>
                  <h1 className="text-2xl font-bold tracking-wider text-foreground font-display uppercase">CHIẾN DỊCH</h1>
                  <p className="text-sm text-foreground/35 font-mono tracking-wider">Quản lý các chiến dịch quảng cáo do AI tạo.</p>
                </div>
                <button
                  type="button"
                  onClick={() => setIsCreatingCampaign(true)}
                  className="px-5 h-10 border-2 border-foreground bg-foreground text-black font-display text-sm font-bold tracking-wider flex items-center gap-2 transition-all hover:bg-transparent hover:text-foreground"
                >
                  <Plus className="h-4 w-4" />
                  CHIẾN DỊCH.MỚI
                </button>
              </div>

              <div className="p-12 text-center border border-dashed border-foreground/15 space-y-3 dot-grid">
                <FolderKanban className="h-8 w-8 text-foreground/20 mx-auto" />
                <p className="text-sm font-mono text-foreground/50 tracking-wider">CHƯA CÓ CHIẾN DỊCH</p>
                <p className="text-xs font-mono text-foreground/25">Tạo chiến dịch mới để bắt đầu quy trình.</p>
              </div>
            </div>
          )}

          {/* PIPELINE VIEW */}
          {isCreatingCampaign && (
            <PipelineLayout
              currentStage={currentStage}
              stageStatuses={stageStatuses}
              onStageChange={setCurrentStage}
              onNext={handleNextStage}
              onBack={handlePrevStage}
              isNextDisabled={currentStage === "research" && (researchLoading || !researchPlan)}
              nextLabel={currentStage === "deploy" ? "HOÀN THÀNH" : "BƯỚC.TIẾP"}
            >
              {currentStage === "product_input" && <StageProductInput value={researchSubmission} onChange={setResearchSubmission} />}
              {currentStage === "research" && <StageResearch plan={researchPlan} isLoading={researchLoading} error={researchError} onRetry={() => void runResearch()} />}
              {currentStage === "positioning" && <StagePositioning />}
              {currentStage === "content_generation" && <StageContentGeneration />}
              {currentStage === "qa_gate" && <StageQAGate />}
              {currentStage === "final_output" && <StageFinalOutput />}
              {currentStage === "user_review" && <StageUserReview />}
              {currentStage === "package" && <StagePackage />}
              {currentStage === "deploy" && <StageDeploy />}
              {!["product_input", "research", "positioning", "content_generation", "qa_gate", "final_output", "user_review", "package", "deploy"].includes(currentStage) && (
                <div className="flex items-center justify-center h-full min-h-[400px] border border-dashed border-foreground/10">
                  <p className="text-sm font-mono text-foreground/30 tracking-wider">
                    [{currentStage.toUpperCase()}_COMPONENT_PLACEHOLDER]
                  </p>
                </div>
              )}
            </PipelineLayout>
          )}
        </div>
      </main>

    </div>
  );
}
