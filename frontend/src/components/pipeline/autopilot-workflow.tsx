"use client";

import * as React from "react";
import { Activity, ArrowRight, Check, FileInput, FileText, FlaskConical, Loader2, Microscope, Sparkles, WandSparkles, Zap } from "lucide-react";
import type { CampaignStage } from "@/types/campaign";

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
}

export const AutopilotWorkflow: React.FC<Props> = ({ productName, errorMessage, initialComplete = false, onRun, onOpenStep }) => {
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
      await wait(8000);
      setNode(id, "complete");
    }
    setRunState("complete");
  };

  return (
    <div className="relative min-h-[720px] overflow-hidden border border-[#35ea52]/20 bg-background p-5 sm:p-8 lg:p-10">
      <div className="absolute inset-0 dot-grid opacity-40 pointer-events-none" />
      <div className="absolute -top-40 left-1/3 h-96 w-96 rounded-full bg-[#35ea52]/10 blur-3xl pointer-events-none" />
      <div className="relative space-y-10">
        <header className="flex flex-col lg:flex-row lg:items-end justify-between gap-6 border-b border-foreground/10 pb-7">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 text-[10px] font-mono tracking-[0.2em] text-[#35ea52]"><Zap className="h-4 w-4" /> QUY TRÌNH TỰ ĐỘNG</div>
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-display font-bold text-foreground">Một brief. Một lần chạy. Trọn bộ chiến dịch.</h1>
            <p className="max-w-2xl text-sm text-foreground/45 leading-relaxed">Theo dõi các agent xử lý từ bước hiểu sản phẩm đến báo cáo sẵn sàng triển khai. Màn hình chi tiết sẽ mở khi từng bước hoàn tất.</p>
          </div>
          <div className="lg:text-right"><p className="text-[9px] font-mono text-foreground/30 tracking-wider">CHIẾN DỊCH ĐANG XỬ LÝ</p><p className="text-sm font-mono text-foreground mt-1">{productName}</p></div>
        </header>

        <div className="relative py-5">
          <div className="mb-5 flex items-center gap-3">
            <span className="text-[9px] font-mono text-foreground/30 tracking-wider shrink-0">TIẾN ĐỘ TỔNG</span>
            <div className="h-1 flex-1 bg-foreground/10 overflow-hidden">
              <div className="h-full bg-[#35ea52] transition-[width] duration-700" style={{ width: `${(completedCount / steps.length) * 100}%` }} />
            </div>
            <span className="text-[9px] font-mono text-[#35ea52] shrink-0">{completedCount}/{steps.length}</span>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 lg:gap-3">
            {steps.map((step, index) => {
              const state = nodeStates[step.id];
              const canOpen = state === "complete" || state === "failed";
              const Icon = step.icon;
              return <button key={step.id} type="button" disabled={!canOpen} onClick={() => canOpen && onOpenStep(step.id)} aria-label={`${step.title} · ${stateLabels[state]}${canOpen ? " · Mở chi tiết" : " · Chưa có chi tiết"}`} className={`relative text-left p-4 lg:pt-6 border min-h-44 transition-all group ${state === "running" ? "border-[#35ea52] bg-[#35ea52]/10 shadow-[0_0_35px_rgba(53,234,82,0.12)] cursor-wait" : state === "complete" ? "border-[#35ea52]/35 bg-[#35ea52]/[0.035] cursor-pointer hover:border-[#35ea52]/60" : state === "failed" ? "border-red-500/50 bg-red-500/5 cursor-pointer" : "border-foreground/10 bg-background cursor-not-allowed"}`}>
                <div className="flex items-start justify-between"><span className="text-[10px] font-mono text-foreground/25">0{index + 1}</span><span className={`h-6 px-2 inline-flex items-center gap-1 text-[8px] font-mono tracking-wider ${state === "running" ? "text-[#35ea52]" : state === "complete" ? "text-[#35ea52]" : state === "failed" ? "text-red-400" : "text-foreground/25"}`}>{state === "running" && <Loader2 className="h-3 w-3 animate-spin" />}{state === "complete" && <Check className="h-3 w-3" />}{stateLabels[state]}</span></div>
                <div className={`mt-3 h-10 w-10 flex items-center justify-center border ${state === "running" || state === "complete" ? "border-[#35ea52]/40 text-[#35ea52]" : "border-foreground/10 text-foreground/35"}`}><Icon className="h-5 w-5" /></div>
                <h2 className="mt-4 text-sm font-display font-bold text-foreground">{step.title}</h2><p className="mt-2 text-[10px] leading-relaxed text-foreground/40">{step.description}</p><div className="mt-4 flex items-center justify-between text-[8px] font-mono text-foreground/25"><span>{step.agent}</span>{canOpen && <ArrowRight className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />}</div>
              </button>;
            })}
          </div>
        </div>

        {(runState === "running" || runState === "failed") && (
          <section className="grid grid-cols-1 lg:grid-cols-[1fr_240px] gap-4 border border-foreground/10 bg-black/10 p-5">
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-[10px] font-mono text-[#35ea52] tracking-wider"><Activity className="h-4 w-4" /> HOẠT ĐỘNG ĐANG DIỄN RA</div>
              {activeStage ? <><p className="text-sm font-mono font-bold text-foreground">{activities[activeStage][activityIndex]}</p><div className="space-y-2">{activities[activeStage].map((activity, index) => <div key={activity} className={`flex items-center gap-2 text-[10px] font-mono ${index === activityIndex ? "text-[#35ea52]" : index < activityIndex ? "text-foreground/50" : "text-foreground/25"}`}>{index < activityIndex ? <Check className="h-3 w-3 text-[#35ea52] shrink-0" /> : <span className={`h-1.5 w-1.5 rounded-full mx-[3px] ${index === activityIndex ? "bg-[#35ea52] animate-pulse" : "bg-foreground/15"}`} />}{activity}</div>)}</div></> : <p className={`text-sm font-mono ${runState === "failed" ? "text-red-400" : "text-[#35ea52]"}`}>{errorMessage || "Đang chờ cập nhật từ agent."}</p>}
            </div>
            <div className="grid grid-cols-2 lg:grid-cols-1 gap-3 lg:border-l border-foreground/10 lg:pl-5"><div><p className="text-[9px] font-mono text-foreground/30">TIẾN ĐỘ</p><p className="text-2xl font-display font-bold text-foreground mt-1">{completedCount}/5</p></div><div><p className="text-[9px] font-mono text-foreground/30">THỜI GIAN ĐÃ CHẠY</p><p className="text-2xl font-display font-bold text-foreground mt-1">{Math.floor(elapsedSeconds / 60).toString().padStart(2, "0")}:{(elapsedSeconds % 60).toString().padStart(2, "0")}</p></div></div>
          </section>
        )}

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5 border border-foreground/10 bg-foreground/[0.02] p-5">
          <div><p className="text-xs font-mono font-bold text-foreground">{runState === "complete" ? "Báo cáo chiến dịch đã sẵn sàng" : runState === "running" ? "Các agent đang xây dựng chiến dịch" : runState === "failed" ? "Quy trình cần được xử lý" : "Sẵn sàng chạy toàn bộ quy trình"}</p><p className={`text-[10px] mt-1 ${runState === "failed" ? "text-red-400" : "text-foreground/35"}`}>{runState === "complete" ? "Mở báo cáo cuối để kiểm tra, tải xuống hoặc triển khai." : runState === "failed" ? (errorMessage || "Nghiên cứu thất bại. Mở bước Nghiên cứu để xem chi tiết rồi thử lại.") : "Bạn có thể mở các bước đã hoàn tất mà không làm gián đoạn quy trình."}</p></div>
          {runState === "complete" ? <button type="button" onClick={() => onOpenStep("final_output")} className="h-11 px-6 bg-[#35ea52] text-black text-xs font-mono font-bold inline-flex items-center gap-2"><FileText className="h-4 w-4" /> MỞ BÁO CÁO CUỐI</button> : <button type="button" onClick={() => void run()} disabled={runState === "running"} className="h-11 px-6 bg-[#35ea52] text-black text-xs font-mono font-bold inline-flex items-center gap-2 disabled:opacity-60">{runState === "running" ? <><Loader2 className="h-4 w-4 animate-spin" /> ĐANG CHẠY QUY TRÌNH</> : <><Sparkles className="h-4 w-4" /> TẠO TOÀN BỘ CHIẾN DỊCH</>}</button>}
        </div>
      </div>
    </div>
  );
};
