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
    label: "Đọc brief và plan",
    detail: "positioning, benefit hierarchy, hai creative route từ bước nghiên cứu",
  },
  {
    at: 5,
    label: "Soát kho ảnh",
    detail: "đo từng tấm: kích thước, nền, độ nét — ô nào dùng được ảnh thật",
  },
  {
    at: 12,
    label: "Viết ngôn ngữ hình",
    detail: "ống kính, nguồn sáng, chất bề mặt, tông màu — theo đúng chỉ đạo của bạn",
  },
  {
    at: 44,
    label: "Chia deliverable theo sàn",
    detail: "mỗi sàn một bộ khung riêng, không phải resize từ một tấm",
  },
  {
    at: 66,
    label: "Dựng đồ thị phụ thuộc",
    detail: "ô nào chờ hero, ô nào chạy song song ngay",
  },
];

/** Lines that rotate under the steps, so the panel is never visually static. */
const MURMUR = [
  "Ảnh thật của thương hiệu luôn được ưu tiên hơn ảnh dựng mới.",
  "Bao bì không bao giờ được vẽ lại — nhãn sai một chữ là hỏng cả kit.",
  "Chữ trên ảnh phải được gọi tên chính xác trong prompt, không để model tự nghĩ.",
  "Mỗi sàn có luật riêng: Shopee cần nền trắng, TikTok cần hook trong 3 giây.",
  "Hero là mỏ neo phong cách — mọi tấm sau đều tham chiếu về nó.",
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
  const murmur = MURMUR[Math.floor(elapsed / 7) % MURMUR.length];

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
            Đạo diễn đang phân tích
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
              Theo yêu cầu:{" "}
              <span className="text-foreground/85">“{direction.trim()}”</span>
            </p>
          ) : (
            <p className="mt-2 max-w-2xl text-[14px] leading-relaxed text-muted-foreground">
              Không có chỉ đạo riêng — đạo diễn tự đọc brief và quyết định.
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
                    "mt-[3px] grid size-[18px] shrink-0 place-items-center rounded-full border transition-colors",
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

        <p
          key={murmur}
          className="studio-enter max-w-2xl border-l-2 border-primary/40 pl-3.5 text-[13px] leading-relaxed text-muted-foreground/85"
        >
          {murmur}
        </p>
      </div>

      <div className="shrink-0 border-t border-border px-5 py-3">
        <p className="text-center text-[12px] text-muted-foreground">
          Chưa có ảnh nào được dựng. Bạn sẽ duyệt đề xuất trước khi studio tiêu
          tốn một giây render nào.
        </p>
      </div>
    </div>
  );
}
