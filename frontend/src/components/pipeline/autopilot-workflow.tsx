"use client";

import * as React from "react";
import { ArrowRight, Check, FileInput, FileText, FlaskConical, Loader2, Microscope, Sparkles, WandSparkles, Zap } from "lucide-react";
import type { CampaignStage } from "@/types/campaign";
import { api } from "@/lib/api";
import type { VerifyChecklistResponseData } from "@/types/qa_checklist";

type RunState = "idle" | "running" | "complete" | "failed";
type NodeState = "waiting" | "running" | "complete" | "failed";

const steps: Array<{ id: CampaignStage; title: string; description: string; icon: React.ElementType; agent: string }> = [
  { id: "product_input", title: "Hiểu sản phẩm", description: "Đọc brief, hình ảnh, khách hàng và mục tiêu", icon: FileInput, agent: "AGENT TIẾP NHẬN" },
  { id: "research", title: "Nghiên cứu thị trường", description: "Tìm bằng chứng, định vị và góc chiến dịch", icon: Microscope, agent: "AGENT NGHIÊN CỨU" },
  { id: "content_generation", title: "Sáng tạo chiến dịch", description: "Tạo phương án, hình ảnh, video và nội dung bán hàng", icon: WandSparkles, agent: "AGENT SÁNG TẠO" },
  { id: "qa_gate", title: "Kiểm duyệt chất lượng", description: "Kiểm tra claim, tính nhất quán và yêu cầu nền tảng", icon: FlaskConical, agent: "AGENT KIỂM DUYỆT" },
  { id: "final_output", title: "Báo cáo cuối cùng", description: "Tổng hợp, tải xuống và triển khai chiến dịch", icon: FileText, agent: "AGENT BÀN GIAO" },
];

const activities: Record<CampaignStage, string[]> = {
  product_input: ["Đọc và chuẩn hoá các trường trong product brief", "Kiểm tra định dạng, dung lượng ảnh sản phẩm", "Đối chiếu thị trường, nền tảng và mục tiêu chiến dịch"],
  research: ["Mã hoá ảnh và chuẩn bị ngữ cảnh đa phương thức", "Phân tích USP, mức giá và định vị hiện tại", "Tìm kiếm xu hướng thị trường từ nguồn bên ngoài", "Đọc nguồn và kiểm chứng tín hiệu liên quan", "So sánh góc truyền thông của nhóm đối thủ", "Tổng hợp bằng chứng cho hai hướng chiến dịch", "Hoàn thiện campaign plan theo schema đầu ra"],
  content_generation: ["Chuyển campaign plan thành creative brief", "Phát triển phương án quảng cáo A và B", "Soạn tiêu đề, mô tả, caption và CTA theo nền tảng", "Xây dựng storyboard video ngắn 9:16", "Chuẩn bị prompt cho bộ hình ảnh sản phẩm", "Tổng hợp tài sản sáng tạo vào manifest"],
  qa_gate: ["Kiểm tra đủ các loại tài sản bắt buộc", "Đối chiếu required claim và nội dung bị cấm", "Kiểm tra tính nhất quán giữa brief, copy và hình ảnh", "Kiểm tra kích thước và yêu cầu TikTok Shop, Shopee", "Phân loại lỗi blocker, warning và đề xuất sửa", "Xác nhận bộ tài sản vượt qua cổng chất lượng"],
  final_output: ["Tổng hợp chiến lược và hai phương án quảng cáo", "Gắn nội dung bán hàng với từng tài sản", "Chuẩn hoá tên tệp và metadata bàn giao", "Tạo manifest cho gói chiến dịch", "Chuẩn bị file ZIP và dữ liệu triển khai nền tảng", "Hoàn thiện báo cáo cuối cùng"],
};

const stateLabels: Record<NodeState, string> = { waiting: "CHỜ XỬ LÝ", running: "ĐANG CHẠY", complete: "HOÀN TẤT", failed: "THẤT BẠI" };

const wait = (milliseconds: number) => new Promise((resolve) => setTimeout(resolve, milliseconds));

interface Props {
  productName: string;
  errorMessage?: string | null;
  initialComplete?: boolean;
  onRun: () => Promise<boolean>;
  onOpenStep: (stage: CampaignStage) => void;
  /** CampaignInputDTO JSON (snake_case), matching backend/app/schemas/campaign_dto.py. */
  campaignInput: Record<string, unknown>;
  /** Computed lazily since the mock output depends on researchPlan, which is only available after the research step completes. */
  getCampaignOutput: () => Record<string, unknown>;
  onQaResult: (result: VerifyChecklistResponseData) => void;
}

export const AutopilotWorkflow: React.FC<Props> = ({ productName, errorMessage, initialComplete = false, onRun, onOpenStep, campaignInput, getCampaignOutput, onQaResult }) => {
  const [runState, setRunState] = React.useState<RunState>(initialComplete ? "complete" : "idle");
  const [nodeStates, setNodeStates] = React.useState<Record<CampaignStage, NodeState>>(() => ({
    product_input: initialComplete ? "complete" : "waiting",
    research: initialComplete ? "complete" : "waiting",
    content_generation: initialComplete ? "complete" : "waiting",
    qa_gate: initialComplete ? "complete" : "waiting",
    final_output: initialComplete ? "complete" : "waiting",
  }));
  const [activityIndex, setActivityIndex] = React.useState(0);
  const [elapsedSeconds, setElapsedSeconds] = React.useState(0);

  const activeStage = steps.find((step) => nodeStates[step.id] === "running")?.id;
  const completedCount = Object.values(nodeStates).filter((state) => state === "complete").length;

  React.useEffect(() => {
    if (runState !== "running") return;
    const timer = window.setInterval(() => setElapsedSeconds((value) => value + 1), 1000);
    return () => window.clearInterval(timer);
  }, [runState]);

  React.useEffect(() => {
    if (runState !== "running" || !activeStage) return;
    const timer = window.setInterval(() => {
      setActivityIndex((value) => Math.min(value + 1, activities[activeStage].length - 1));
    }, 6500);
    return () => window.clearInterval(timer);
  }, [activeStage, runState]);

  const setNode = (id: CampaignStage, state: NodeState) => setNodeStates((current) => ({ ...current, [id]: state }));

  const run = async () => {
    setRunState("running");
    setElapsedSeconds(0);
    setActivityIndex(0);
    setNodeStates({ product_input: "running", research: "waiting", content_generation: "waiting", qa_gate: "waiting", final_output: "waiting" });
    await wait(500);
    setNode("product_input", "complete");
    setActivityIndex(0);
    setNode("research", "running");
    const succeeded = await onRun();
    if (!succeeded) {
      setNode("research", "failed");
      setRunState("failed");
      return;
    }
    setNode("research", "complete");
    for (const id of ["content_generation", "qa_gate", "final_output"] as CampaignStage[]) {
      setActivityIndex(0);
      setNode(id, "running");
      if (id === "qa_gate") {
        try {
          const response = await api.verifyChecklist({
            campaign_input: campaignInput,
            campaign_output: getCampaignOutput(),
            iteration: 1,
          });
          if (!response.data) throw new Error("QA checklist backend trả về dữ liệu trống.");
          onQaResult(response.data);
        } catch {
          // QA failures in autopilot must surface, not be swallowed —
          // mirrors the existing research failure handling above.
          setNode("qa_gate", "failed");
          setRunState("failed");
          return;
        }
      } else {
        await wait(8000);
      }
      setNode(id, "complete");
    }
    setRunState("complete");
  };

  const formattedElapsed = `${Math.floor(elapsedSeconds / 60).toString().padStart(2, "0")}:${(elapsedSeconds % 60).toString().padStart(2, "0")}`;

  return (
    <div className="relative overflow-hidden border border-[#35ea52]/20 bg-background p-5 sm:p-6 flex flex-col min-h-0 h-full">
      <div className="absolute inset-0 dot-grid opacity-40 pointer-events-none" />
      <div className="relative flex flex-col gap-4 min-h-0 flex-1">
        <header className="flex items-center justify-between gap-4 shrink-0">
          <div className="inline-flex items-center gap-2 text-[10px] font-mono tracking-[0.2em] text-[#35ea52]"><Zap className="h-4 w-4" /> QUY TRÌNH TỰ ĐỘNG</div>
          <div className="text-right"><p className="text-[9px] font-mono text-foreground/30 tracking-wider">CHIẾN DỊCH ĐANG XỬ LÝ</p><p className="text-sm font-mono text-foreground mt-0.5">{productName}</p></div>
        </header>

        <div className="border border-foreground/10 bg-foreground/[0.03] p-4 flex flex-col gap-3 min-h-0 flex-1">
          <div className="flex items-center gap-3 shrink-0">
            <span className="text-[9px] font-mono text-foreground/30 tracking-wider shrink-0">TIẾN ĐỘ TỔNG</span>
            <div className="h-1 flex-1 bg-foreground/10 overflow-hidden">
              <div className="h-full bg-[#35ea52] transition-[width] duration-700" style={{ width: `${(completedCount / steps.length) * 100}%` }} />
            </div>
            <span className="text-[9px] font-mono text-[#35ea52] shrink-0">{completedCount}/{steps.length}</span>
            {runState === "running" && <span className="text-[9px] font-mono text-foreground/40 shrink-0">({formattedElapsed})</span>}
          </div>

          <div className="flex flex-col divide-y divide-foreground/10 min-h-0 overflow-y-auto">
            {steps.map((step, index) => {
              const state = nodeStates[step.id];
              const canOpen = state === "complete" || state === "failed";
              const isRunning = state === "running";
              const Icon = step.icon;
              return (
                <div key={step.id}>
                  <button type="button" disabled={!canOpen} onClick={() => canOpen && onOpenStep(step.id)} aria-label={`${step.title} · ${stateLabels[state]}${canOpen ? " · Mở chi tiết" : " · Chưa có chi tiết"}`} className={`relative flex w-full items-center gap-3 text-left px-2 py-2.5 transition-all group ${isRunning ? "bg-[#35ea52]/10 cursor-wait" : state === "complete" ? "cursor-pointer hover:bg-[#35ea52]/[0.05]" : state === "failed" ? "bg-red-500/5 cursor-pointer" : "cursor-not-allowed"}`}>
                    <span className="text-[10px] font-mono text-foreground/25 w-5 shrink-0">0{index + 1}</span>
                    <div className={`h-7 w-7 flex items-center justify-center border shrink-0 ${isRunning || state === "complete" ? "border-[#35ea52]/40 text-[#35ea52]" : "border-foreground/10 text-foreground/35"}`}><Icon className="h-3.5 w-3.5" /></div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <h2 className="text-xs font-display font-bold text-foreground truncate">{step.title}</h2>
                        {isRunning && <span className="text-[9px] font-mono text-[#35ea52] shrink-0">({formattedElapsed})</span>}
                      </div>
                      <p className="text-[9px] text-foreground/40 truncate">{step.agent}</p>
                    </div>
                    <span className={`shrink-0 inline-flex items-center gap-1 text-[8px] font-mono tracking-wider ${isRunning ? "text-[#35ea52]" : state === "complete" ? "text-[#35ea52]" : state === "failed" ? "text-red-400" : "text-foreground/25"}`}>{isRunning && <Loader2 className="h-3 w-3 animate-spin" />}{state === "complete" && <Check className="h-3 w-3" />}{stateLabels[state]}</span>
                    {canOpen && <ArrowRight className="h-3 w-3 text-foreground/25 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />}
                  </button>
                  {isRunning && (
                    <div className="pl-[3.25rem] pr-3 pb-3 -mt-0.5 bg-[#35ea52]/[0.04] animate-in fade-in slide-in-from-top-1 duration-300">
                      <div className="flex flex-col gap-1.5 pt-1">
                        {activities[step.id].map((activity, activityIdx) => (
                          <div key={activity} className={`flex items-center gap-2 text-[10px] font-mono ${activityIdx === activityIndex ? "text-[#35ea52]" : activityIdx < activityIndex ? "text-foreground/45" : "text-foreground/25"}`}>
                            {activityIdx < activityIndex ? (
                              <Check className="h-3 w-3 text-[#35ea52] shrink-0" />
                            ) : activityIdx === activityIndex ? (
                              <Loader2 className="h-3 w-3 text-[#35ea52] animate-spin shrink-0" />
                            ) : (
                              <span className="h-1.5 w-1.5 rounded-full mx-[3px] bg-foreground/15 shrink-0" />
                            )}
                            {activity}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border border-foreground/10 bg-foreground/[0.02] p-4 shrink-0">
          <div><p className="text-xs font-mono font-bold text-foreground">{runState === "complete" ? "Báo cáo chiến dịch đã sẵn sàng" : runState === "running" ? "Các agent đang xây dựng chiến dịch" : runState === "failed" ? "Quy trình cần được xử lý" : "Sẵn sàng chạy toàn bộ quy trình"}</p><p className={`text-[10px] mt-1 ${runState === "failed" ? "text-red-400" : "text-foreground/35"}`}>{runState === "complete" ? "Mở báo cáo cuối để kiểm tra, tải xuống hoặc triển khai." : runState === "failed" ? (errorMessage || "Nghiên cứu thất bại. Mở bước Nghiên cứu để xem chi tiết rồi thử lại.") : "Bạn có thể mở các bước đã hoàn tất mà không làm gián đoạn quy trình."}</p></div>
          {runState === "complete" ? <button type="button" onClick={() => onOpenStep("final_output")} className="h-11 px-6 bg-[#35ea52] text-black text-xs font-mono font-bold inline-flex items-center gap-2 shrink-0"><FileText className="h-4 w-4" /> MỞ BÁO CÁO CUỐI</button> : <button type="button" onClick={() => void run()} disabled={runState === "running"} className="h-11 px-6 bg-[#35ea52] text-black text-xs font-mono font-bold inline-flex items-center gap-2 disabled:opacity-60 shrink-0">{runState === "running" ? <><Loader2 className="h-4 w-4 animate-spin" /> ĐANG CHẠY QUY TRÌNH</> : <><Sparkles className="h-4 w-4" /> TẠO TOÀN BỘ CHIẾN DỊCH</>}</button>}
        </div>
      </div>
    </div>
  );
};
