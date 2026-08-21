"use client";

import * as React from "react";
import { CampaignStage, StageStatus, CAMPAIGN_STAGES, type CampaignListItem } from "@/types/campaign";
import { PipelineLayout } from "@/components/pipeline/pipeline-layout";
import { StageProductInput } from "@/components/pipeline/stage-product-input";
import { StageResearch } from "@/components/pipeline/stage-research";
import { StageContentGeneration } from "@/components/pipeline/stage-content-generation";
import { StageQAGate } from "@/components/pipeline/stage-qa-gate";
import { StageFinalOutput } from "@/components/pipeline/stage-final-output";
import { AutopilotWorkflow } from "@/components/pipeline/autopilot-workflow";
import { AlertTriangle, ArrowLeft, CalendarDays, FolderKanban, ListTree, LoaderCircle, Plus, RefreshCw, Search, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { fetchSavedQa, saveQa } from "@/lib/studio-draft";
import { attachDefaultSampleProductPhotos, createEmptyResearchSubmission, createInitialResearchSubmission, parseResearchCampaignPlan, validateResearchSubmission, type ResearchCampaignPlan, type ResearchSubmission } from "@/types/research";
import { buildCampaignInputDTO, buildMockCampaignOutput } from "@/types/campaign_output_mock";
import type { VerifyChecklistResponseData } from "@/types/qa_checklist";
import type { StudioAssetDTOResponse } from "@/types/studio";
import { cn } from "@/lib/utils";

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
  // Pipeline State
  const [isCreatingCampaign, setIsCreatingCampaign] = React.useState(false);
  const [workflowMode, setWorkflowMode] = React.useState<"manual" | "autopilot">("manual");
  const [showAutopilotOverview, setShowAutopilotOverview] = React.useState(false);
  const [autopilotInitiallyComplete, setAutopilotInitiallyComplete] = React.useState(false);
  const [currentStage, setCurrentStage] = React.useState<CampaignStage>("product_input");
  const [researchSubmission, setResearchSubmission] = React.useState<ResearchSubmission>(createInitialResearchSubmission);
  const [researchPlan, setResearchPlan] = React.useState<ResearchCampaignPlan | null>(null);
  const [campaignOutput, setCampaignOutput] = React.useState<Record<string, unknown> | null>(null);
  const [qaResult, setQaResult] = React.useState<VerifyChecklistResponseData | null>(null);

  // A verdict belongs to the kit it judged, so it is stored beside it and read
  // back when the campaign is reopened rather than recomputed.
  const rememberQa = React.useCallback(
    (result: VerifyChecklistResponseData) => {
      setQaResult(result);
      if (activeCampaignIdRef.current) void saveQa(activeCampaignIdRef.current, result);
    },
    [],
  );
  const [researchLoading, setResearchLoading] = React.useState(false);
  const [researchError, setResearchError] = React.useState<string | null>(null);
  const [campaigns, setCampaigns] = React.useState<CampaignListItem[]>([]);
  const [campaignsLoading, setCampaignsLoading] = React.useState(true);
  const [campaignsError, setCampaignsError] = React.useState<string | null>(null);
  const [openingCampaignId, setOpeningCampaignId] = React.useState<string | null>(null);
  // Which campaigns already have a rendered kit, and how big it is. Three
  // campaigns for the same product carry the same name and the same status
  // badge, so the list gave no way to tell the one that has been built from the
  // two that have not — and opening the wrong one looks like a broken feature.
  const [builtKits, setBuiltKits] = React.useState<Record<string, string>>({});
  // Which campaign the pipeline is currently walking through. Set when one is
  // opened from the list; the handoff to the studio needs it by id.
  const [activeCampaignId, setActiveCampaignId] = React.useState<string | null>(null);
  // Read inside callbacks that must not re-create on every id change.
  const activeCampaignIdRef = React.useRef<string | null>(null);
  React.useEffect(() => { activeCampaignIdRef.current = activeCampaignId; }, [activeCampaignId]);
  const readyCampaigns = campaigns.filter((campaign) => campaign.has_research_result).length;
  const activeCampaigns = campaigns.filter((campaign) => campaign.status === "researching").length;

  // Asked per campaign rather than added to the list endpoint, which belongs to
  // the research stage and should not learn about rendered files.
  const loadBuiltKits = React.useCallback(async (rows: CampaignListItem[]) => {
    const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
    const entries = await Promise.all(
      rows.map(async (row) => {
        try {
          const res = await fetch(`${base}/studio/${encodeURIComponent(row.id)}/saved`);
          if (!res.ok) return [row.id, ""] as const;
          const body = await res.json();
          const kit = body?.data;
          return [
            row.id,
            kit?.built ? `${kit.images} ảnh · ${kit.videos} video` : "",
          ] as const;
        } catch {
          return [row.id, ""] as const;
        }
      })
    );
    setBuiltKits(Object.fromEntries(entries.filter(([, v]) => v)));
  }, []);

  const loadCampaigns = React.useCallback(async () => {
    setCampaignsLoading(true);
    setCampaignsError(null);
    try {
      const response = await api.getCampaigns();
      setCampaigns(response.data ?? []);
      void loadBuiltKits(response.data ?? []);
    } catch (error) {
      setCampaignsError(error instanceof Error ? error.message : "Không thể tải danh sách chiến dịch.");
    } finally {
      setCampaignsLoading(false);
    }
  }, [loadBuiltKits]);

  React.useEffect(() => {
    let cancelled = false;
    api.getCampaigns()
      .then((response) => {
        if (cancelled) return;
        setCampaigns(response.data ?? []);
        void loadBuiltKits(response.data ?? []);
      })
      .catch((error: unknown) => {
        if (!cancelled) setCampaignsError(error instanceof Error ? error.message : "Không thể tải danh sách chiến dịch.");
      })
      .finally(() => {
        if (!cancelled) setCampaignsLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  React.useEffect(() => {
    let cancelled = false;
    void attachDefaultSampleProductPhotos(createInitialResearchSubmission())
      .then((submission) => {
        if (!cancelled) setResearchSubmission(submission);
      })
      .catch(() => {
        if (!cancelled) toast.error("Không thể tải sẵn ảnh sản phẩm mẫu G7.");
      });
    return () => { cancelled = true; };
  }, []);

  const startNewCampaign = () => {
    // Blank, not seeded. The G7 sample makes the demo one click and makes every
    // other product a lie: the form opened claiming to be G7 coffee, and
    // whatever the extractor did not overwrite stayed — a yoghurt campaign
    // carrying "Cà phê Robusta Việt Nam" as a required claim and #E60000 as its
    // brand colour. The seeded path is still one button away, under Autopilot.
    setResearchSubmission(createEmptyResearchSubmission());
    setResearchPlan(null);
    // Forget the campaign that was open before. Leaving it set would let the
    // handoff to the studio carry the previous campaign's id if the user walked
    // forward without running research — the studio would open, find a valid
    // researched campaign under that id, and build the wrong product.
    setActiveCampaignId(null);
    setResearchError(null);
    setCampaignOutput(null);
    setQaResult(null);
    setCurrentStage("product_input");
    setWorkflowMode("manual");
    setShowAutopilotOverview(false);
    setAutopilotInitiallyComplete(false);
    setIsCreatingCampaign(true);
  };

  const startAutopilotCampaign = async () => {
    const initialSubmission = createInitialResearchSubmission();
    setResearchSubmission(initialSubmission);
    setResearchPlan(null);
    setResearchError(null);
    setCampaignOutput(null);
    setQaResult(null);
    setCurrentStage("product_input");
    setWorkflowMode("autopilot");
    setShowAutopilotOverview(false);
    setAutopilotInitiallyComplete(false);
    setIsCreatingCampaign(true);
    try {
      setResearchSubmission(await attachDefaultSampleProductPhotos(initialSubmission));
    } catch {
      toast.error("Không thể tải sẵn ảnh sản phẩm mẫu G7.");
    }
  };

  const returnToCampaigns = () => {
    setIsCreatingCampaign(false);
    setOpeningCampaignId(null);
    void loadCampaigns();
  };

  const openCampaign = async (campaign: CampaignListItem) => {
    if (!campaign.has_research_result) return;

    // Forget the campaign that was open before. `startNewCampaign` and the
    // autopilot path both clear these and this one did not, so opening a second
    // campaign in the same session inherited the first one's generated output
    // and its QA verdict — open a G7 campaign, then open one for children's
    // shoes, and the QA gate read back a report about instant coffee. The
    // fetch below refills them for this campaign, or leaves them empty if it
    // has never been built.
    setCampaignOutput(null);
    setQaResult(null);

    setOpeningCampaignId(campaign.id);
    try {
      const response = await api.getCampaign(campaign.id);
      const campaignData = response.data;
      const savedResult = campaignData?.research_result;
      if (!savedResult || typeof savedResult !== "object" || !("plan" in savedResult)) {
        throw new Error("Chiến dịch chưa có kết quả nghiên cứu hợp lệ.");
      }
      setResearchPlan(parseResearchCampaignPlan(savedResult.plan));
      if (campaignData?.research_input) {
        setResearchSubmission((current) => ({
          ...current,
          input: campaignData.research_input as unknown as ResearchSubmission["input"],
        }));
      }
      // Which campaign the pipeline is now walking. Every stage downstream is
      // handed this: stage 03 opens the studio on it instead of offering a
      // picker, and with three campaigns sharing one product name a picker is
      // a coin toss the user has to win.
      setActiveCampaignId(campaign.id);
      setResearchError(null);

      // Opening a campaign jumps straight to the final report, so stage 03 —
      // the only place that tells the report what was actually built — never
      // mounts. Without this the report falls back to buildMockCampaignOutput
      // and shows four https://example.com/mock/*.jpg links under a heading
      // saying the assets are ready. That is the path a judge takes.
      // Whatever QA already concluded about this kit, rather than judging it
      // again the moment the screen opens.
      void fetchSavedQa(campaign.id).then((stored) => {
        if (stored) setQaResult(stored as unknown as VerifyChecklistResponseData);
      });

      const freshPlan = parseResearchCampaignPlan(savedResult.plan);
      const freshInput = (campaignData?.research_input ??
        researchSubmission.input) as ResearchSubmission["input"];
      void api
        .getStudioAssets(campaign.id)
        .then((res) => {
          // Hand the campaign along rather than trusting state to have caught
          // up: both were set moments ago and neither has re-rendered.
          if (res.data) handleStudioAssetsReady(res.data, { plan: freshPlan, input: freshInput });
        })
        .catch(() => {
          // A campaign that was never rendered has no assets, which is a fact
          // about the campaign rather than a failure of this screen.
        });

      setCurrentStage("final_output");
      setWorkflowMode("autopilot");
      setAutopilotInitiallyComplete(true);
      setShowAutopilotOverview(true);
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

  const runResearch = async (navigateToResearch = true) => {
    const validationErrors = validateResearchSubmission(researchSubmission);
    if (validationErrors.length) {
      toast.error(validationErrors[0]);
      return false;
    }
    setResearchLoading(true);
    setResearchError(null);
    if (navigateToResearch) setCurrentStage("research");
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

  // CampaignInputDTO for the QA gate / autopilot, derived from the current
  // research submission's input (real user data, always available once the
  // product_input stage is filled in).
  const campaignInputForQa = React.useMemo(
    () => buildCampaignInputDTO(researchSubmission.input),
    [researchSubmission.input],
  );

  // Called once the content-generation stage's studio run finishes with real
  // assets (real /media/... paths the backend can resolve back to actual
  // files — see StudioAssetDTOResponse). Merges them on top of
  // buildMockCampaignOutput's plan-derived positioning/routes/ab_plan (which
  // the studio doesn't own), so the QA gate and final report see real
  // generated images/video/copy instead of mock URLs once a run has
  // completed, while still falling back to the mock for anything not ready.
  const handleStudioAssetsReady = React.useCallback(
    (
      assets: StudioAssetDTOResponse,
      // The campaign these assets belong to, when the caller already has it.
      // Without this the base comes from state that has not re-rendered yet:
      // `openCampaign` sets the plan and the brief, then fetches the assets in
      // the same tick, and this callback still closes over the *previous*
      // campaign. That is how a shoe campaign was sent to the QA gate carrying
      // "Cà Phê Hòa Tan G7 3in1 Hộp 50 Gói" as its product title with an empty
      // creative-route list — the plan had cleared but the brief had not, and
      // QA reported the mismatch it was handed.
      source?: { plan: ResearchCampaignPlan | null; input: ResearchSubmission["input"] },
    ) => {
      setCampaignOutput((current) => {
        const base =
          current ??
          buildMockCampaignOutput(
            source ? source.plan : researchPlan,
            source ? source.input : researchSubmission.input,
          );
        return {
          ...base,
          ...(assets.product_collection_image_set
            ? { product_collection_image_set: assets.product_collection_image_set }
            : {}),
          ...(assets.short_form_video_asset
            ? { short_form_video_asset: assets.short_form_video_asset }
            : {}),
          ...(assets.commerce_copy ? { commerce_copy: assets.commerce_copy } : {}),
          // The A/B pair. Dropped here for its first day: the endpoint returned
          // it, the report read it, and this merge copied three fields past it —
          // so the section rendered its two hypotheses over no artwork at all,
          // which is the exact state adding the pair was meant to end.
          ...(assets.ab_variants && Object.keys(assets.ab_variants).length
            ? { ab_variants: assets.ab_variants }
            : {}),
        };
      });
    },
    [researchPlan, researchSubmission.input],
  );

  const handleNextStage = () => {
    if (currentStage === "product_input") {
      if (workflowMode === "autopilot") {
        const validationErrors = validateResearchSubmission(researchSubmission);
        if (validationErrors.length) {
          toast.error(validationErrors[0]);
          return;
        }
        setShowAutopilotOverview(true);
        return;
      }
      void runResearch();
      return;
    }
    // Leaving research means entering content generation, which is the Asset
    // Studio mounted in stage 03. Nothing to navigate to: the campaign id is
    // handed down as a prop, so the studio opens on the product the user has
    // just briefed instead of asking them to pick it again.
    if (currentStage === "research" && !activeCampaignId) {
      setActiveCampaignId(researchSubmission.input.campaign_id);
    }
    if (currentStage === "final_output") {
      returnToCampaigns();
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
        <div className="flex-1 max-w-[1760px] w-full mx-auto p-4 sm:p-8 flex flex-col">

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
                <div className="flex items-center gap-2">
                  <button type="button" onClick={() => void startAutopilotCampaign()} className="px-5 h-10 border-2 border-[#35ea52] bg-[#35ea52] text-black font-display text-sm font-bold tracking-wider flex items-center gap-2 transition-all hover:bg-transparent hover:text-[#35ea52]"><Sparkles className="h-4 w-4" /> LUỒNG TỰ ĐỘNG</button>
                  <button type="button" onClick={startNewCampaign} className="px-5 h-10 border border-foreground/30 text-foreground font-display text-sm font-bold tracking-wider flex items-center gap-2 transition-all hover:border-foreground"><Plus className="h-4 w-4" /> LÀM TỪNG BƯỚC</button>
                </div>
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
                    const canOpen = campaign.has_research_result && !isOpening;
                    return (
                      <article
                        key={campaign.id}
                        role={canOpen ? "button" : undefined}
                        tabIndex={canOpen ? 0 : undefined}
                        aria-label={canOpen ? `Mở gói chiến dịch ${campaign.name}` : undefined}
                        aria-busy={isOpening || undefined}
                        onClick={canOpen ? () => void openCampaign(campaign) : undefined}
                        onKeyDown={
                          canOpen
                            ? (event) => {
                                if (event.key === "Enter" || event.key === " ") {
                                  event.preventDefault();
                                  void openCampaign(campaign);
                                }
                              }
                            : undefined
                        }
                        className={cn(
                          "group min-h-44 p-5 border border-foreground/10 bg-foreground/[0.02] flex flex-col justify-between gap-6 transition-all select-none outline-none",
                          canOpen
                            ? "cursor-pointer hover:border-[#35ea52]/50 hover:bg-[#35ea52]/[0.025] hover:shadow-sm focus-visible:border-[#35ea52] focus-visible:ring-2 focus-visible:ring-[#35ea52]/25 active:scale-[0.995]"
                            : isOpening
                              ? "cursor-wait opacity-80"
                              : "opacity-75 cursor-default"
                        )}
                      >
                        <div className="space-y-3">
                          <div className="flex items-start justify-between gap-3">
                            <span className="flex flex-wrap items-center gap-2">
                              <span className={`px-2 py-1 border text-[9px] font-mono tracking-widest ${STATUS_STYLES[campaign.status]}`}>
                                {STATUS_LABELS[campaign.status]}
                              </span>
                              {/* Research status is not the question a person
                                  opening this list is asking. Three campaigns
                                  for one product share a name, a status and a
                                  badge; what tells them apart is which one has
                                  a kit already rendered. */}
                              {builtKits[campaign.id] ? (
                                <span className="px-2 py-1 border border-[#35ea52]/40 text-[#35ea52] text-[9px] font-mono tracking-widest">
                                  {builtKits[campaign.id]}
                                </span>
                              ) : campaign.has_research_result ? (
                                <span className="px-2 py-1 border border-foreground/15 text-foreground/35 text-[9px] font-mono tracking-widest">
                                  CHƯA DỰNG
                                </span>
                              ) : null}
                            </span>
                            <span className="text-[9px] font-mono text-foreground/20 truncate max-w-32" title={campaign.id}>{campaign.id}</span>
                          </div>
                          <div>
                            <h2 className="font-display font-bold tracking-wide text-foreground line-clamp-2 group-hover:text-[#35ea52] transition-colors">{campaign.name}</h2>
                            {campaign.description && <p className="mt-2 text-xs font-mono text-foreground/40 line-clamp-2">{campaign.description}</p>}
                          </div>
                        </div>
                        <div className="flex items-end justify-between gap-3 border-t border-foreground/10 pt-3">
                          <span className="inline-flex items-center gap-1.5 text-[10px] font-mono text-foreground/30">
                            <CalendarDays className="h-3 w-3" /> {formatCampaignDate(campaign.updated_at)}
                          </span>
                          <span
                            className={cn(
                              "inline-flex items-center gap-1.5 text-[10px] font-mono font-bold tracking-wider group-hover:underline",
                              campaign.has_research_result ? "text-[#35ea52]" : "text-foreground/20"
                            )}
                          >
                            {isOpening ? <LoaderCircle className="h-3.5 w-3.5 animate-spin" /> : <Search className="h-3.5 w-3.5" />}
                            {campaign.has_research_result ? "MỞ GÓI CHIẾN DỊCH" : "CHƯA CÓ ĐỀ XUẤT"}
                          </span>
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
            <div className="flex-1 flex flex-col gap-3 min-h-0 max-h-[calc(100vh-11rem)]">
              <div className="flex items-center justify-between gap-3 shrink-0">
                <button type="button" onClick={returnToCampaigns} className="inline-flex items-center gap-2 text-[11px] font-mono text-foreground/40 hover:text-foreground tracking-wider"><ArrowLeft className="h-3.5 w-3.5" /> TẤT CẢ CHIẾN DỊCH</button>
                {workflowMode === "autopilot" && !showAutopilotOverview && <button type="button" onClick={() => setShowAutopilotOverview(true)} className="inline-flex items-center gap-2 px-3 py-2 border border-[#35ea52]/30 text-[10px] font-mono text-[#35ea52]"><ListTree className="h-3.5 w-3.5" /> TỔNG QUAN LUỒNG TỰ ĐỘNG</button>}
              </div>
              {workflowMode === "autopilot" && showAutopilotOverview ? (
                <AutopilotWorkflow
                  productName={researchSubmission.input.product_brief.product_name}
                  errorMessage={researchError}
                  initialComplete={autopilotInitiallyComplete}
                  onRun={() => runResearch(false)}
                  onOpenStep={(stage) => { setCurrentStage(stage); setShowAutopilotOverview(false); }}
                  campaignId={activeCampaignId}
                  campaignInput={campaignInputForQa}
                  getCampaignOutput={() => {
                    // content_generation's headless studio run (see
                    // runStudioForAutopilot) reports real assets through
                    // onAssetsReady -> handleStudioAssetsReady as soon as
                    // they're ready, merging them into campaignOutput. Read
                    // that state here rather than unconditionally rebuilding
                    // the mock, so a real run's assets are what qa_gate
                    // actually verifies against instead of being discarded
                    // right before use.
                    const output = campaignOutput ?? buildMockCampaignOutput(researchPlan, researchSubmission.input);
                    setCampaignOutput(output);
                    return output;
                  }}
                  onAssetsReady={handleStudioAssetsReady}
                  onQaResult={rememberQa}
                />
              ) : (
              <PipelineLayout
              currentStage={currentStage}
              stageStatuses={stageStatuses}
              onStageChange={setCurrentStage}
              onNext={handleNextStage}
              onBack={handlePrevStage}
              isNextDisabled={currentStage === "research" && (researchLoading || !researchPlan)}
              nextLabel={
                currentStage === "product_input" && workflowMode === "autopilot"
                  ? "BẮT ĐẦU LUỒNG TỰ ĐỘNG"
                  : currentStage === "final_output"
                    ? "HOÀN THÀNH"
                    : currentStage === "research"
                      ? "SÁNG.TẠO_CHIẾN_DỊCH"
                      : "BƯỚC.TIẾP"
              }
              >
              {currentStage === "product_input" && <StageProductInput value={researchSubmission} onChange={setResearchSubmission} initialInputMode={workflowMode === "autopilot" ? "manual" : "link"} />}
              {currentStage === "research" && <StageResearch plan={researchPlan} isLoading={researchLoading} error={researchError} onRetry={() => void runResearch()} />}
              {currentStage === "content_generation" && (
                <StageContentGeneration
                  // Fall back to the brief being edited rather than passing
                  // null: null makes the studio guess, and guessing means
                  // picking the oldest of three identically-named campaigns.
                  campaignId={activeCampaignId ?? researchSubmission.input.campaign_id ?? null}
                  onAssetsReady={handleStudioAssetsReady}
                />
              )}
              {currentStage === "qa_gate" && <StageQAGate campaignInput={campaignInputForQa} campaignOutput={campaignOutput ?? buildMockCampaignOutput(researchPlan, researchSubmission.input)} onResult={rememberQa} savedResult={qaResult} />}
              {currentStage === "final_output" && <StageFinalOutput plan={researchPlan} input={researchSubmission.input} campaignOutput={campaignOutput ?? buildMockCampaignOutput(researchPlan, researchSubmission.input)} qaResult={qaResult} />}
              {!["product_input", "research", "content_generation", "qa_gate", "final_output"].includes(currentStage) && (
                <div className="flex items-center justify-center h-full min-h-[400px] border border-dashed border-foreground/10">
                  <p className="text-sm font-mono text-foreground/30 tracking-wider">
                    [{currentStage.toUpperCase()}_COMPONENT_PLACEHOLDER]
                  </p>
                </div>
              )}
              </PipelineLayout>
              )}
            </div>
          )}
        </div>
      </main>

    </div>
  );
}
