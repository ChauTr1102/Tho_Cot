"use client";

import * as React from "react";
import { ShieldAlert, CheckCircle2, XCircle, RefreshCw } from "lucide-react";

export const StageQAGate: React.FC = () => {
  const [qaState, setQaState] = React.useState<"checking" | "failed" | "passed">("checking");
  const [failedChecks, setFailedChecks] = React.useState<string[]>([]);

  React.useEffect(() => {
    // Simulate QA process
    if (qaState === "checking") {
      const timer = setTimeout(() => {
        // Simulate a failure on the first pass
        setQaState("failed");
        setFailedChecks(["PLATFORM_POLICY_03"]);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [qaState]);

  const handleFixIssues = () => {
    setQaState("checking");
    setTimeout(() => {
      setQaState("passed");
      setFailedChecks([]);
    }, 2000);
  };

  const categories = [
    {
      id: "INTERNAL",
      title: "INTERNAL SYSTEM CRITERIA",
      checks: [
        { id: "INT_01", text: "Brand visual consistency verified", status: "pass" },
        { id: "INT_02", text: "CTA clearly visible in all assets", status: "pass" }
      ]
    },
    {
      id: "MARKET",
      title: "MARKET RESEARCH CRITERIA",
      checks: [
        { id: "MKT_01", text: "Phù hợp xu hướng tiêu dùng văn phòng", status: "pass" },
        { id: "MKT_02", text: "Đóng gói đúng nhận diện truyền thống", status: "pass" }
      ]
    },
    {
      id: "POLICY",
      title: "PLATFORM POLICY CRITERIA",
      checks: [
        { id: "PLATFORM_POLICY_01", text: "Không tuyên bố y tế / sức khỏe tuyệt đối", status: "pass" },
        { 
          id: "PLATFORM_POLICY_03", 
          text: "Không so sánh trực tiếp với đối thủ", 
          status: failedChecks.includes("PLATFORM_POLICY_03") ? "fail" : "pass",
          error: failedChecks.includes("PLATFORM_POLICY_03") ? "Variant A sử dụng từ ngữ ám chỉ so sánh trực tiếp. Yêu cầu sửa đổi để tránh vi phạm chính sách nền tảng." : undefined
        }
      ]
    }
  ];

  return (
    <div className="space-y-6 h-full flex flex-col animate-in fade-in duration-500">
      <div className="space-y-2 border-b border-foreground/10 pb-4">
        <h2 className="text-lg font-bold font-mono tracking-wider text-foreground flex items-center gap-2">
          QA & POLICY GATE
        </h2>
        <p className="text-sm font-mono text-foreground/40">
          Independent verification of all assets against 24 platform, market, and brand rules.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto space-y-6">
        
        {qaState === "checking" && (
          <div className="flex flex-col items-center justify-center p-12 border border-foreground/10 bg-foreground/[0.02] space-y-4">
            <RefreshCw className="h-8 w-8 text-[#35ea52] animate-spin" />
            <p className="text-sm font-mono text-foreground/50 tracking-widest uppercase">Đang chạy xác thực QA...</p>
          </div>
        )}

        {qaState === "failed" && (
          <div className="border-l-2 border-red-500 bg-red-500/[0.05] p-4 flex items-start gap-4">
            <ShieldAlert className="h-6 w-6 text-red-500 shrink-0" />
            <div className="space-y-2 flex-1">
              <h3 className="text-[15px] font-mono font-bold text-red-400">KIỂM DUYỆT CHẤT LƯỢNG THẤT BẠI (1 LỖI NGHIÊM TRỌNG)</h3>
              <p className="text-sm font-mono text-foreground/70">
                The QA Agent has blocked the pipeline because generated assets violate advertising policies (Direct competitor comparison).
              </p>
              <button 
                onClick={handleFixIssues}
                className="mt-2 px-4 py-2 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 text-xs font-mono transition-colors flex items-center gap-2"
              >
                <RefreshCw className="h-3 w-3" /> AUTO-FIX & RE-GENERATE ASSETS
              </button>
            </div>
          </div>
        )}

        {qaState === "passed" && (
          <div className="border-l-2 border-[#35ea52] bg-[#35ea52]/[0.05] p-4 flex items-start gap-4">
            <CheckCircle2 className="h-6 w-6 text-[#35ea52] shrink-0" />
            <div>
              <h3 className="text-[15px] font-mono font-bold text-[#35ea52]">KIỂM DUYỆT CHẤT LƯỢNG THÀNH CÔNG (24/24)</h3>
              <p className="text-sm font-mono text-foreground/70">
                All generated assets comply with brand guidelines and platform policies.
              </p>
            </div>
          </div>
        )}

        {/* Checklist */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {categories.map(cat => (
            <div key={cat.id} className="border border-foreground/10 bg-background p-4 space-y-3">
              <span className="text-xs font-mono text-foreground/50 tracking-widest uppercase block border-b border-foreground/5 pb-2">
                {cat.title}
              </span>
              <ul className="space-y-3">
                {cat.checks.map(check => (
                  <li key={check.id} className="space-y-1">
                    <div className="flex items-start gap-2">
                      {check.status === "pass" && qaState !== "checking" ? (
                        <CheckCircle2 className="h-3.5 w-3.5 text-[#35ea52] shrink-0 mt-0.5" />
                      ) : check.status === "fail" && qaState !== "checking" ? (
                        <XCircle className="h-3.5 w-3.5 text-red-500 shrink-0 mt-0.5" />
                      ) : (
                        <div className="h-3.5 w-3.5 border border-foreground/20 shrink-0 mt-0.5 rounded-full" />
                      )}
                      <span className={`text-sm font-mono ${check.status === 'fail' ? 'text-foreground font-bold' : 'text-foreground/60'}`}>
                        {check.text}
                      </span>
                    </div>
                    {check.error && qaState === "failed" && (
                      <p className="text-xs font-mono text-red-400 pl-5 leading-relaxed bg-red-500/5 p-2 border border-red-500/10 mt-1">
                        {check.error}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
};
