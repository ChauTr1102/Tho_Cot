"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { CampaignStage, StageStatus, CAMPAIGN_STAGES, type CampaignListItem } from "@/types/campaign";
import { PipelineLayout } from "@/components/pipeline/pipeline-layout";
import { StageProductInput } from "@/components/pipeline/stage-product-input";
import { StageResearch } from "@/components/pipeline/stage-research";
import { StageContentGeneration } from "@/components/pipeline/stage-content-generation";
import { StageQAGate } from "@/components/pipeline/stage-qa-gate";
import { StageFinalOutput } from "@/components/pipeline/stage-final-output";
import { StageUserReview } from "@/components/pipeline/stage-user-review";
import { StagePackage } from "@/components/pipeline/stage-package";
import { StageDeploy } from "@/components/pipeline/stage-deploy";
import { AlertTriangle, ArrowLeft, CalendarDays, FolderKanban, LoaderCircle, Plus, RefreshCw, Search } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { createInitialResearchSubmission, parseResearchCampaignPlan, validateResearchSubmission, type ResearchCampaignPlan, type ResearchSubmission } from "@/types/research";

const STATUS_LABELS: Record<CampaignListItem["status"], string> = {
  draft: "BẢN NHÁP",
  researching: "ĐANG NGHIÊN CỨU",
  researched: "ĐÃ NGHIÊN CỨU",
  failed: "THẤT BẠI",
};

const STATUS_STYLES: Record<CampaignListItem["status"], string> = {
  draft: "border-foreground/20 text-foreground/45",
  researching: "border-amber-400/40 text-amber-400",
  researched: "border-[#35ea52]/40 text-[#35ea52]",
  failed: "border-red-400/40 text-red-400",
};

function formatCampaignDate(value: string) {
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function CampaignsPage() {
  const router = useRouter();
  // Pipeline State
  const [isCreatingCampaign, setIsCreatingCampaign] = React.useState(false);
  const [currentStage, setCurrentStage] = React.useState<CampaignStage>("product_input");
  const [researchSubmission, setResearchSubmission] = React.useState<ResearchSubmission>(createInitialResearchSubmission);
  const [researchPlan, setResearchPlan] = React.useState<ResearchCampaignPlan | null>(null);
  const [researchLoading, setResearchLoading] = React.useState(false);
  const [researchError, setResearchError] = React.useState<string | null>(null);
  const [campaigns, setCampaigns] = React.useState<CampaignListItem[]>([]);
  const [campaignsLoading, setCampaignsLoading] = React.useState(true);
  const [campaignsError, setCampaignsError] = React.useState<string | null>(null);
  const [openingCampaignId, setOpeningCampaignId] = React.useState<string | null>(null);
  // Which campaign the pipeline is currently walking through. Set when one is
  // opened from the list; the handoff to the studio needs it by id.
  const [activeCampaignId, setActiveCampaignId] = React.useState<string | null>(null);
  const readyCampaigns = campaigns.filter((campaign) => campaign.has_research_result).length;
  const activeCampaigns = campaigns.filter((campaign) => campaign.status === "researching").length;

  const loadCampaigns = React.useCallback(async () => {
    setCampaignsLoading(true);
    setCampaignsError(null);
    try {
      const response = await api.getCampaigns();
      setCampaigns(response.data ?? []);
    } catch (error) {
      setCampaignsError(error instanceof Error ? error.message : "Không thể tải danh sách chiến dịch.");
    } finally {
      setCampaignsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    let cancelled = false;
    api.getCampaigns()
      .then((response) => {
        if (!cancelled) setCampaigns(response.data ?? []);
      })
      .catch((error: unknown) => {
        if (!cancelled) setCampaignsError(error instanceof Error ? error.message : "Không thể tải danh sách chiến dịch.");
      })
      .finally(() => {
        if (!cancelled) setCampaignsLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  const startNewCampaign = () => {
    setResearchSubmission(createInitialResearchSubmission());
    setResearchPlan(null);
    setResearchError(null);
    setCurrentStage("product_input");
    setIsCreatingCampaign(true);
  };

  const returnToCampaigns = () => {
    setIsCreatingCampaign(false);
    setOpeningCampaignId(null);
    void loadCampaigns();
  };

  const openCampaign = async (campaign: CampaignListItem) => {
    if (!campaign.has_research_result) return;
    setOpeningCampaignId(campaign.id);
    try {
      const response = await api.getCampaign(campaign.id);
      const savedResult = response.data?.research_result;
      if (!savedResult || typeof savedResult !== "object" || !("plan" in savedResult)) {
        throw new Error("Chiến dịch chưa có kết quả nghiên cứu hợp lệ.");
      }
      setResearchPlan(parseResearchCampaignPlan(savedResult.plan));
      setActiveCampaignId(campaign.id);
      setResearchError(null);
      setCurrentStage("research");
      setIsCreatingCampaign(true);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Không thể mở chiến dịch.");
    } finally {
      setOpeningCampaignId(null);
    }
  };

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
      setActiveCampaignId(researchSubmission.input.campaign_id);
      await loadCampaigns();
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
    // Content generation is a screen of its own — the Asset Studio — so leaving
    // research hands the campaign over rather than advancing an inner step. The
    // id rides in the URL so the studio opens on this campaign already selected
    // and the user never re-picks the product they just briefed.
    if (currentStage === "research") {
      const handoffId = activeCampaignId ?? researchSubmission.input.campaign_id;
      router.push(`/studio?campaign=${encodeURIComponent(handoffId)}`);
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
      {/* Main Workspace Area */}
      <main className="flex-1 min-w-0 flex flex-col min-h-screen bg-transparent py-6">
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
                  <p className="text-sm text-foreground/45 max-w-2xl">Biến thông tin sản phẩm thành góc bán hàng, hai phương án quảng cáo và bộ nội dung sẵn sàng triển khai.</p>
                </div>
                <button
                  type="button"
                  onClick={startNewCampaign}
                  className="px-5 h-10 border-2 border-foreground bg-foreground text-black font-display text-sm font-bold tracking-wider flex items-center gap-2 transition-all hover:bg-transparent hover:text-foreground"
                >
                  <Plus className="h-4 w-4" />
                  CHIẾN DỊCH.MỚI
                </button>
              </div>

              {!campaignsLoading && !campaignsError && campaigns.length > 0 && (
                <div className="grid grid-cols-3 border border-foreground/10 divide-x divide-foreground/10">
                  <div className="p-4"><p className="text-2xl font-display font-bold text-foreground">{campaigns.length}</p><p className="text-[10px] font-mono text-foreground/35 tracking-wider mt-1">TỔNG CHIẾN DỊCH</p></div>
                  <div className="p-4"><p className="text-2xl font-display font-bold text-[#35ea52]">{readyCampaigns}</p><p className="text-[10px] font-mono text-foreground/35 tracking-wider mt-1">CÓ ĐỀ XUẤT BÁN HÀNG</p></div>
                  <div className="p-4"><p className="text-2xl font-display font-bold text-amber-400">{activeCampaigns}</p><p className="text-[10px] font-mono text-foreground/35 tracking-wider mt-1">ĐANG XỬ LÝ</p></div>
                </div>
              )}

              {campaignsLoading && (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4" aria-label="Đang tải chiến dịch">
                  {[0, 1, 2].map((item) => (
                    <div key={item} className="h-44 border border-foreground/10 bg-foreground/[0.02] animate-pulse" />
                  ))}
                </div>
              )}

              {!campaignsLoading && campaignsError && (
                <div className="p-10 text-center border border-red-400/20 bg-red-400/[0.03] space-y-4">
                  <AlertTriangle className="h-8 w-8 text-red-400 mx-auto" />
                  <p className="text-sm font-mono text-red-300">{campaignsError}</p>
                  <button type="button" onClick={() => void loadCampaigns()} className="inline-flex items-center gap-2 px-4 py-2 border border-foreground/20 text-xs font-mono hover:border-foreground/50">
                    <RefreshCw className="h-3.5 w-3.5" /> THỬ LẠI
                  </button>
                </div>
              )}

              {!campaignsLoading && !campaignsError && campaigns.length === 0 && (
                <div className="p-12 text-center border border-dashed border-foreground/15 space-y-3 dot-grid">
                  <FolderKanban className="h-8 w-8 text-foreground/20 mx-auto" />
                  <p className="text-sm font-mono text-foreground/50 tracking-wider">CHƯA CÓ CHIẾN DỊCH</p>
                  <p className="text-xs text-foreground/35 max-w-lg mx-auto">Thêm sản phẩm, thị trường mục tiêu và hình ảnh. Hệ thống sẽ đề xuất thông điệp bán hàng cùng hai hướng quảng cáo để thử nghiệm.</p>
                </div>
              )}

              {!campaignsLoading && !campaignsError && campaigns.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {campaigns.map((campaign) => {
                    const isOpening = openingCampaignId === campaign.id;
                    return (
                      <article key={campaign.id} className="group min-h-44 p-5 border border-foreground/10 bg-foreground/[0.02] hover:border-foreground/30 transition-colors flex flex-col justify-between gap-6">
                        <div className="space-y-3">
                          <div className="flex items-start justify-between gap-3">
                            <span className={`px-2 py-1 border text-[9px] font-mono tracking-widest ${STATUS_STYLES[campaign.status]}`}>
                              {STATUS_LABELS[campaign.status]}
                            </span>
                            <span className="text-[9px] font-mono text-foreground/20 truncate max-w-32" title={campaign.id}>{campaign.id}</span>
                          </div>
                          <div>
                            <h2 className="font-display font-bold tracking-wide text-foreground line-clamp-2">{campaign.name}</h2>
                            {campaign.description && <p className="mt-2 text-xs font-mono text-foreground/40 line-clamp-2">{campaign.description}</p>}
                          </div>
                        </div>
                        <div className="flex items-end justify-between gap-3 border-t border-foreground/10 pt-3">
                          <span className="inline-flex items-center gap-1.5 text-[10px] font-mono text-foreground/30">
                            <CalendarDays className="h-3 w-3" /> {formatCampaignDate(campaign.updated_at)}
                          </span>
                          <button
                            type="button"
                            disabled={!campaign.has_research_result || isOpening}
                            onClick={() => void openCampaign(campaign)}
                            className="inline-flex items-center gap-1.5 text-[10px] font-mono font-bold tracking-wider text-[#35ea52] disabled:text-foreground/20 disabled:cursor-not-allowed"
                          >
                            {isOpening ? <LoaderCircle className="h-3.5 w-3.5 animate-spin" /> : <Search className="h-3.5 w-3.5" />}
                            {campaign.has_research_result ? "MỞ GÓI CHIẾN DỊCH" : "CHƯA CÓ ĐỀ XUẤT"}
                          </button>
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* PIPELINE VIEW */}
          {isCreatingCampaign && (
            <div className="flex-1 flex flex-col gap-3">
              <button type="button" onClick={returnToCampaigns} className="self-start inline-flex items-center gap-2 text-[11px] font-mono text-foreground/40 hover:text-foreground tracking-wider">
                <ArrowLeft className="h-3.5 w-3.5" /> TẤT CẢ CHIẾN DỊCH
              </button>
              <PipelineLayout
              currentStage={currentStage}
              stageStatuses={stageStatuses}
              onStageChange={setCurrentStage}
              onNext={handleNextStage}
              onBack={handlePrevStage}
              isNextDisabled={currentStage === "research" && (researchLoading || !researchPlan)}
              nextLabel={
                currentStage === "deploy"
                  ? "HOÀN THÀNH"
                  : // Leaving research changes screen, not step. Naming the
                    // destination stops the jump reading as a misclick.
                    currentStage === "research"
                    ? "MỞ.XƯỞNG_ẢNH"
                    : "BƯỚC.TIẾP"
              }
              >
              {currentStage === "product_input" && <StageProductInput value={researchSubmission} onChange={setResearchSubmission} />}
              {currentStage === "research" && <StageResearch plan={researchPlan} isLoading={researchLoading} error={researchError} onRetry={() => void runResearch()} />}
              {currentStage === "content_generation" && <StageContentGeneration />}
              {currentStage === "qa_gate" && <StageQAGate />}
              {currentStage === "final_output" && <StageFinalOutput />}
              {currentStage === "user_review" && <StageUserReview />}
              {currentStage === "package" && <StagePackage />}
              {currentStage === "deploy" && <StageDeploy />}
              {!["product_input", "research", "content_generation", "qa_gate", "final_output", "user_review", "package", "deploy"].includes(currentStage) && (
                <div className="flex items-center justify-center h-full min-h-[400px] border border-dashed border-foreground/10">
                  <p className="text-sm font-mono text-foreground/30 tracking-wider">
                    [{currentStage.toUpperCase()}_COMPONENT_PLACEHOLDER]
                  </p>
                </div>
              )}
              </PipelineLayout>
            </div>
          )}
        </div>
      </main>

    </div>
  );
}
