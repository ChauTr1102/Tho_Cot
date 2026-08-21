"use client";

import * as React from "react";
import { AgentLoading } from "./agent-loading";
import { CheckCircle2, MessageSquare, Send, ThumbsUp } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";

export const StageUserReview: React.FC = () => {
  const [isProcessing, setIsProcessing] = React.useState(true);
  const [feedback, setFeedback] = React.useState("");
  const [isSending, setIsSending] = React.useState(false);
  const [isApproved, setIsApproved] = React.useState(false);

  React.useEffect(() => {
    const timer = setTimeout(() => setIsProcessing(false), 2000);
    return () => clearTimeout(timer);
  }, []);

  const steps = [
    "Preparing review dashboard...",
    "Loading generated assets...",
    "Awaiting user feedback..."
  ];

  const handleSendFeedback = () => {
    if (!feedback.trim()) return;
    setIsSending(true);
    setTimeout(() => {
      setIsSending(false);
      setFeedback("");
      // Logic để back lại stage trước nếu cần
    }, 1500);
  };

  const handleApprove = () => {
    setIsApproved(true);
  };

  if (isProcessing) {
    return (
      <div className="h-full flex flex-col justify-center max-w-xl mx-auto w-full">
        <AgentLoading agentName="USER_REVIEW_AGENT" steps={steps} isComplete={false} />
      </div>
    );
  }

  return (
    <div className="space-y-6 h-full flex flex-col animate-in fade-in duration-500">
      <div className="space-y-2 border-b border-foreground/10 pb-4 shrink-0">
        <h2 className="text-lg font-bold font-mono tracking-wider text-foreground">ĐÁNH GIÁ TỪ NGƯỜI DÙNG</h2>
        <p className="text-sm font-mono text-foreground/40">
          Vui lòng kiểm tra đối chiếu các tài sản chiến dịch với checklist và cung cấp phản hồi nếu cần chỉnh sửa.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-6 pr-2 pb-8">
        
        {/* Checklist */}
        <div className="border border-foreground/10 bg-background p-5 space-y-4">
          <h3 className="text-xs font-mono font-bold text-[#35ea52] tracking-widest uppercase border-b border-foreground/10 pb-2 flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            Checklist Duyệt Sản Phẩm
          </h3>
          <ul className="space-y-3 text-sm font-mono text-foreground/80">
            <li className="flex items-start gap-3 p-2 bg-foreground/[0.02] hover:bg-foreground/[0.05] transition-colors cursor-pointer border border-foreground/5">
              <input type="checkbox" className="mt-1 w-4 h-4 accent-[#35ea52] cursor-pointer" />
              <span>Nội dung video / hình ảnh đã tuân thủ đúng màu sắc và nhận diện thương hiệu.</span>
            </li>
            <li className="flex items-start gap-3 p-2 bg-foreground/[0.02] hover:bg-foreground/[0.05] transition-colors cursor-pointer border border-foreground/5">
              <input type="checkbox" className="mt-1 w-4 h-4 accent-[#35ea52] cursor-pointer" />
              <span>Tiêu đề và mô tả sản phẩm chứa đủ các thông tin quan trọng & key selling points.</span>
            </li>
            <li className="flex items-start gap-3 p-2 bg-foreground/[0.02] hover:bg-foreground/[0.05] transition-colors cursor-pointer border border-foreground/5">
              <input type="checkbox" className="mt-1 w-4 h-4 accent-[#35ea52] cursor-pointer" />
              <span>Không có vi phạm bản quyền hay từ ngữ bị cấm (như claim chữa bệnh, so sánh đối thủ).</span>
            </li>
            <li className="flex items-start gap-3 p-2 bg-foreground/[0.02] hover:bg-foreground/[0.05] transition-colors cursor-pointer border border-foreground/5">
              <input type="checkbox" className="mt-1 w-4 h-4 accent-[#35ea52] cursor-pointer" />
              <span>Thông điệp khuyến mãi (9.9, Mua 3 tặng 1) hiển thị rõ ràng trên Banner.</span>
            </li>
          </ul>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Feedback Form */}
          <div className="border border-foreground/10 bg-foreground/[0.02] p-5 space-y-4">
            <h3 className="text-xs font-mono font-bold text-foreground/70 tracking-widest uppercase border-b border-foreground/10 pb-2 flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Yêu cầu chỉnh sửa
            </h3>
            <p className="text-[11px] font-mono text-foreground/50">
              Agent sẽ nhận feedback này, quay lại bước Sáng tạo nội dung để chỉnh sửa và tự động sinh lại các tài sản.
            </p>
            <Textarea
              placeholder="VD: Cần đổi tone màu banner Route B sang đỏ sậm hơn. Video Route A thêm hiệu ứng khói rõ hơn..."
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              className="bg-background border-foreground/20 text-sm font-mono min-h-[120px] focus:border-[#35ea52]/50"
              disabled={isSending || isApproved}
            />
            <button
              onClick={handleSendFeedback}
              disabled={!feedback.trim() || isSending || isApproved}
              className="w-full flex items-center justify-center gap-2 py-2 border border-foreground/30 bg-background hover:bg-foreground/10 text-xs font-mono font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSending ? (
                <span className="animate-pulse">ĐANG GỬI PHẢN HỒI...</span>
              ) : (
                <>
                  <Send className="h-3.5 w-3.5" /> GỬI PHẢN HỒI CHO AGENT
                </>
              )}
            </button>
          </div>

          {/* Approve Panel */}
          <div className="border border-[#35ea52]/20 bg-[#35ea52]/[0.02] p-5 space-y-4 flex flex-col justify-between">
            <div>
              <h3 className="text-xs font-mono font-bold text-[#35ea52] tracking-widest uppercase border-b border-[#35ea52]/20 pb-2 flex items-center gap-2">
                <ThumbsUp className="h-4 w-4" />
                Phê duyệt Chiến dịch
              </h3>
              <p className="text-sm font-mono text-foreground/80 mt-4 leading-relaxed">
                Nếu tất cả các nội dung đã đạt yêu cầu, bạn có thể phê duyệt để chuyển sang bước Đóng gói (Package) & Triển khai (Deploy).
              </p>
            </div>
            
            {isApproved ? (
              <div className="flex items-center justify-center gap-2 py-3 bg-[#35ea52]/20 text-[#35ea52] border border-[#35ea52]/30 text-xs font-mono font-bold">
                <CheckCircle2 className="h-4 w-4" /> ĐÃ PHÊ DUYỆT
              </div>
            ) : (
              <button
                onClick={handleApprove}
                disabled={isSending}
                className="w-full flex items-center justify-center gap-2 py-3 bg-[#35ea52] text-black hover:bg-[#35ea52]/80 text-xs font-mono font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <CheckCircle2 className="h-4 w-4" /> PHÊ DUYỆT & TIẾP TỤC
              </button>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
