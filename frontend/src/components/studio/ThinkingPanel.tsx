"use client";

/**
 * What the director is doing while nothing is on screen yet.
 *
 * Proposing a campaign takes around ninety seconds — the model writes the whole
 * thing — and for that minute and a half the stage is empty. A spinner says
 * "wait"; this says what is being decided, which is the difference between a
 * wait that feels broken and one that feels like work.
 *
 * **The steps are real, the timings are estimated.** Each line below is a stage
 * `POST /studio/draft` genuinely runs, in the order it runs them. What is *not*
 * real is the schedule: the endpoint answers once, at the end, and streams
 * nothing in between, so the reveal is driven by a local clock calibrated
 * against measured draft times rather than by server events. That is why a step
 * is only ever marked "đang chạy" or "xong" — never given a duration it did not
 * report — and why the last step stays running until the response actually
 * lands. If the draft endpoint ever streams progress, delete the clock and read
 * the events; nothing else here needs to change.
 */

import { useEffect, useState } from "react";
import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

interface Step {
  /** Seconds into the draft when this stage typically begins. */
  at: number;
  label: string;
  detail: string;
}

/**
 * Calibrated against measured draft runs: 86s on the G7 campaign, 85s on the
 * demo briefs. The register is the expensive part — it is the one thing the
 * model writes from scratch — so it holds the longest slot by a wide margin.
 */
const STEPS: Step[] = [
  {
    at: 0,
    label: "Đọc campaign plan",
    detail: "positioning · benefit hierarchy · creative routes",
  },
  {
    at: 5,
    label: "Kiểm kê kho ảnh",
    detail: "độ phân giải · nền · tỉ lệ khung",
  },
  {
    at: 12,
    label: "Sinh visual register",
    detail: "ống kính · ánh sáng · bề mặt · tông màu",
  },
  {
    at: 44,
    label: "Phân bổ deliverable theo sàn",
    detail: "khung ảnh và video theo chuẩn từng sàn",
  },
  {
    at: 66,
    label: "Dựng dependency graph",
    detail: "thứ tự thực thi · nhánh chạy song song",
  },
];


interface ThinkingPanelProps {
  /** What the user asked for, shown back to them as the thing being served. */
  direction: string;
  campaignName: string | null;
}

export function ThinkingPanel({ direction, campaignName }: ThinkingPanelProps) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const started = Date.now();
    const id = window.setInterval(
      () => setElapsed(Math.floor((Date.now() - started) / 1000)),
      250
    );
    return () => window.clearInterval(id);
  }, []);

  // The last step that has started. Everything before it is done; it itself is
  // running, and stays running — the panel unmounts when the answer arrives.
  const active = STEPS.reduce(
    (last, step, index) => (elapsed >= step.at ? index : last),
    0
  );

  return (
    <div className="studio-panel relative flex h-[clamp(560px,72vh,900px)] flex-col overflow-hidden">
      {/* A slow sweep across the panel. Motion that is clearly not a progress
          bar: nothing here knows a percentage, and a bar that invents one is a
          lie the user catches at the ninety-second mark. */}
      <div
        aria-hidden
        className="studio-rail-sweep pointer-events-none absolute inset-x-0 top-0 h-px"
      />

      <div className="flex shrink-0 items-baseline justify-between gap-3 border-b border-border px-5 py-3.5">
        <div className="flex items-center gap-2.5">
          <span
            aria-hidden
            className="studio-live-dot relative size-2 rounded-full bg-primary"
          />
          <h2 className="font-display text-[15px] font-semibold tracking-tight">
            Đang phân tích chiến dịch
          </h2>
        </div>
        <span className="studio-nums font-mono text-[13px] tabular-nums text-muted-foreground">
          {String(Math.floor(elapsed / 60)).padStart(2, "0")}:
          {String(elapsed % 60).padStart(2, "0")}
        </span>
      </div>

      <div className="flex min-h-0 flex-1 flex-col justify-center gap-8 px-5 py-6 sm:px-10">
        <div>
          <p className="text-[11px] font-semibold tracking-[0.22em] text-primary uppercase">
            Chiến dịch
          </p>
          <p className="mt-1.5 font-display text-[22px] leading-tight font-semibold tracking-tight sm:text-[26px]">
            {campaignName ?? "Đang dựng đề xuất"}
          </p>
          {direction.trim() ? (
            <p className="mt-2 max-w-2xl text-[14px] leading-relaxed text-muted-foreground">
              Chỉ đạo:{" "}
              <span className="text-foreground/85">“{direction.trim()}”</span>
            </p>
          ) : (
            <p className="mt-2 max-w-2xl text-[14px] leading-relaxed text-muted-foreground">
              Không có chỉ đạo riêng — dùng mặc định suy ra từ brief.
            </p>
          )}
        </div>

        <ol className="flex flex-col gap-3.5">
          {STEPS.map((step, index) => {
            const done = index < active;
            const running = index === active;
            const waiting = index > active;
            return (
              <li
                key={step.label}
                className={cn(
                  "flex items-start gap-3.5 transition-opacity duration-500",
                  waiting && "opacity-35"
                )}
              >
                <span
                  aria-hidden
                  className={cn(
                    "mt-[3px] grid size-[18px] shrink-0 place-items-center rounded-none border transition-colors",
                    done && "border-primary bg-primary text-primary-foreground",
                    running && "border-primary text-primary",
                    waiting && "border-border"
                  )}
                >
                  {done ? (
                    <Check className="size-2.5" strokeWidth={3.5} />
                  ) : running ? (
                    <span className="studio-live-dot relative size-1.5 rounded-full bg-current" />
                  ) : null}
                </span>
                <span className="min-w-0 flex-1 leading-snug">
                  <span
                    className={cn(
                      "block text-[15px] font-medium",
                      running && "text-primary"
                    )}
                  >
                    {step.label}
                  </span>
                  <span className="mt-0.5 block text-[13px] text-muted-foreground">
                    {step.detail}
                  </span>
                </span>
                <span className="studio-nums shrink-0 font-mono text-[11px] text-muted-foreground/70">
                  {done ? "xong" : running ? "đang chạy" : "chờ"}
                </span>
              </li>
            );
          })}
        </ol>

      </div>

      <div className="shrink-0 border-t border-border px-5 py-3">
        <p className="text-center text-[12px] text-muted-foreground">
          Chưa render. Đề xuất sẽ chờ bạn duyệt.
        </p>
      </div>
    </div>
  );
}
