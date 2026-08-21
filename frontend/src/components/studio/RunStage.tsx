"use client";

/**
 * The right-hand column: everything the user watches while the studio works.
 *
 * A run is 6–12 minutes long, so the job of this region is to keep the wait
 * legible. Three surfaces, top to bottom:
 *
 *   1. The status bar — one line answering "is it moving, how far, how long".
 *   2. The canvas slot (`children`) — the graph. Task 13 swaps the placeholder
 *      for the React Flow canvas here; nothing else on this screen changes.
 *   3. The ledgers — the route mix accumulating live, and the last transitions
 *      as they land. Between them they turn a wait into something to read.
 *
 * There is no spinner anywhere in this file. That is the point.
 */

import { WifiOff } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { OriginBadge, ORIGIN_ORDER } from "@/components/studio/OriginBadge";
import { NODE_STATE_META, kindMeta } from "@/components/studio/state-styles";
import { formatClock, formatElapsed } from "@/lib/studio-events";
import type { StudioProgress } from "@/lib/studio-events";
import { cn } from "@/lib/utils";
import type {
  AssetOrigin,
  StudioActivityEntry,
  StudioNode,
  StudioStreamStatus,
} from "@/types/studio";

interface RunStageProps {
  status: StudioStreamStatus;
  progress: StudioProgress;
  elapsedSec: number;
  nodes: StudioNode[];
  activity: StudioActivityEntry[];
  error: string | null;
  /** Planned route mix, used before any node has reported one. */
  plannedOrigins: Record<AssetOrigin, number>;
  onRetry: () => void;
  children: ReactNode;
}

const STATUS_HEADLINE: Record<StudioStreamStatus, string> = {
  idle: "Sẵn sàng",
  connecting: "Đang kết nối",
  reconnecting: "Đang nối lại",
  streaming: "Đang dựng kit",
  done: "Hoàn tất",
  disconnected: "Mất kết nối",
};

export function RunStage({
  status,
  progress,
  elapsedSec,
  nodes,
  activity,
  error,
  plannedOrigins,
  onRetry,
  children,
}: RunStageProps) {
  const live = status === "streaming" || status === "connecting";
  const started = status !== "idle";

  return (
    <section className="flex min-w-0 flex-col gap-4">
      <RunStatusBar
        status={status}
        progress={progress}
        elapsedSec={elapsedSec}
        live={live}
        started={started}
      />

      {status === "disconnected" ? (
        <DisconnectedNotice message={error} onRetry={onRetry} />
      ) : null}

      {/* ══════════════════════════════════════════════════════════════════
          TASK 13 MOUNTS THE GRAPH CANVAS HERE.
          `page.tsx` passes <GraphCanvasPlaceholder /> as this child today.
          Replace that single JSX element with <GraphCanvas nodes={nodes} />;
          the status bar and the ledgers below need no changes.
          ══════════════════════════════════════════════════════════════════ */}
      {children}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]">
        <RouteLedger nodes={nodes} plannedOrigins={plannedOrigins} />
        <ActivityLedger activity={activity} started={started} />
      </div>
    </section>
  );
}

/* ──────────────────────────────────────────────────────────────────────────
 * Status bar
 * ────────────────────────────────────────────────────────────────────────── */

function RunStatusBar({
  status,
  progress,
  elapsedSec,
  live,
  started,
}: {
  status: StudioStreamStatus;
  progress: StudioProgress;
  elapsedSec: number;
  live: boolean;
  started: boolean;
}) {
  const failed = status === "disconnected" || progress.failed > 0;
  const tone = failed
    ? "text-destructive"
    : status === "done"
      ? "text-primary"
      : live
        ? "text-primary"
        : "text-muted-foreground";

  return (
    <div className="studio-panel px-4 py-3">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2.5">
        <div className="flex items-center gap-2.5">
          <span
            aria-hidden
            className={cn(
              "relative size-2 rounded-full",
              tone,
              live && "studio-live-dot",
              failed
                ? "bg-destructive"
                : status === "idle"
                  ? "bg-muted-foreground/50"
                  : "bg-primary"
            )}
          />
          <span className="font-display text-[15px] font-semibold tracking-tight">
            {STATUS_HEADLINE[status]}
          </span>
        </div>

        <div className="flex min-w-[180px] flex-1 items-center gap-3">
          <div className="studio-rail relative h-1 min-w-0 flex-1 overflow-hidden rounded-full">
            <div
              className="studio-rail-fill absolute inset-0"
              style={{ transform: `scaleX(${started ? progress.ratio : 0})` }}
            />
            {live ? (
              <div aria-hidden className="studio-rail-sweep absolute inset-0" />
            ) : null}
          </div>
          {/* Before a run there is no progress to report, so the rail states
              the cost instead of showing a meaningless "0/—". */}
          <span className="studio-nums shrink-0 font-mono text-[12px] text-muted-foreground">
            {started
              ? `${progress.finished}/${progress.total || "—"} bước`
              : "≈ 6–12 phút"}
          </span>
        </div>

        <div className="flex items-center gap-4">
          {progress.running > 0 ? (
            <span className="studio-nums font-mono text-[12px] text-primary">
              {progress.running} đang chạy
            </span>
          ) : null}
          {progress.failed > 0 ? (
            <span className="studio-nums font-mono text-[12px] text-destructive">
              {progress.failed} lỗi
            </span>
          ) : null}
          <span
            className="studio-nums font-display text-[19px] font-semibold tracking-tight"
            aria-label="Thời gian đã chạy"
          >
            {formatClock(elapsedSec)}
          </span>
        </div>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────────────────
 * Failure
 * ────────────────────────────────────────────────────────────────────────── */

function DisconnectedNotice({
  message,
  onRetry,
}: {
  message: string | null;
  onRetry: () => void;
}) {
  return (
    <div className="flex flex-wrap items-start gap-3 rounded-xl border border-destructive/35 bg-destructive/8 px-4 py-3">
      <WifiOff aria-hidden className="mt-0.5 size-4 shrink-0 text-destructive" />
      <div className="min-w-0 flex-1">
        <p className="text-[13.5px] font-medium text-foreground">
          Không giữ được kết nối tới studio
        </p>
        <p className="mt-0.5 text-[12.5px] leading-relaxed text-muted-foreground">
          {message ??
            "Luồng sự kiện đã đóng sau một lần thử nối lại."}{" "}
          Kiểm tra backend FastAPI đang chạy ở{" "}
          <span className="font-mono">NEXT_PUBLIC_API_URL</span>.
        </p>
      </div>
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={onRetry}
        className="shrink-0"
      >
        Thử lại
      </Button>
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────────────────
 * Route ledger — the studio's commercial judgement, counted
 * ────────────────────────────────────────────────────────────────────────── */

function RouteLedger({
  nodes,
  plannedOrigins,
}: {
  nodes: StudioNode[];
  plannedOrigins: Record<AssetOrigin, number>;
}) {
  const observed: Record<AssetOrigin, number> = {
    reuse: 0,
    remix: 0,
    generate: 0,
  };
  for (const node of nodes) {
    const origin = node.payload?.origin;
    if (origin && origin in observed) observed[origin] += 1;
  }

  const hasObserved = observed.reuse + observed.remix + observed.generate > 0;
  const counts = hasObserved ? observed : plannedOrigins;
  const total = counts.reuse + counts.remix + counts.generate;

  const barColor: Record<AssetOrigin, string> = {
    reuse: "bg-gold",
    remix: "bg-primary",
    generate: "bg-primary/45",
  };

  return (
    <div className="studio-panel px-4 py-3.5">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="font-display text-[14px] font-semibold tracking-tight">
          Nguồn của mỗi tấm
        </h3>
        <span className="text-[11.5px] text-muted-foreground">
          {hasObserved ? "thực tế" : "dự kiến"}
        </span>
      </div>

      <div className="mt-3 space-y-2.5">
        {ORIGIN_ORDER.map((origin) => {
          const value = counts[origin] ?? 0;
          const share = total > 0 ? value / total : 0;
          return (
            <div key={origin} className="flex items-center gap-3">
              <OriginBadge origin={origin} size="xs" className="w-[86px]" />
              <div className="studio-rail h-1 min-w-0 flex-1 overflow-hidden rounded-full">
                <div
                  className={cn("h-full rounded-full", barColor[origin])}
                  style={{ width: `${Math.round(share * 100)}%` }}
                />
              </div>
              <span className="studio-nums w-6 shrink-0 text-right font-mono text-[12px] text-foreground/85">
                {value}
              </span>
            </div>
          );
        })}
      </div>

      <p className="mt-3 border-t border-border pt-2.5 text-[11.5px] leading-relaxed text-muted-foreground">
        Ô nào khách soi kỹ sản phẩm thì dùng ảnh thật — một pixel bịa ra ở đó là
        một đơn hoàn.
      </p>
    </div>
  );
}

/* ──────────────────────────────────────────────────────────────────────────
 * Activity ledger — the transitions, as they land
 * ────────────────────────────────────────────────────────────────────────── */

function ActivityLedger({
  activity,
  started,
}: {
  activity: StudioActivityEntry[];
  started: boolean;
}) {
  return (
    <div className="studio-panel flex flex-col overflow-hidden">
      <div className="flex items-baseline justify-between gap-3 border-b border-border px-4 py-3">
        <h3 className="font-display text-[14px] font-semibold tracking-tight">
          Nhật ký chạy
        </h3>
        <span className="studio-nums font-mono text-[11.5px] text-muted-foreground">
          {activity.length > 0 ? `${activity.length} sự kiện` : "—"}
        </span>
      </div>

      {activity.length === 0 ? (
        <div className="grid flex-1 place-items-center px-6 py-8">
          <p className="max-w-[22rem] text-center text-[12.5px] leading-relaxed text-muted-foreground">
            {started
              ? "Đang chờ sự kiện đầu tiên từ graph…"
              : "Từng bước của graph sẽ hiện ở đây ngay khi studio chạy — node nào xong trước hiện trước."}
          </p>
        </div>
      ) : (
        <ul className="max-h-[260px] divide-y divide-border/60 overflow-y-auto">
          {activity.map((entry) => {
            const state = NODE_STATE_META[entry.state] ?? NODE_STATE_META.pending;
            const kind = kindMeta(entry.kind);
            const Icon = kind.icon;
            return (
              <li
                key={entry.key}
                className="studio-enter flex items-center gap-2.5 px-4 py-2"
              >
                <Icon
                  aria-hidden
                  className="size-3.5 shrink-0 text-muted-foreground"
                />
                <span className="min-w-0 flex-1 truncate font-mono text-[12px] text-foreground/90">
                  {entry.node_id}
                </span>
                {entry.origin ? (
                  <OriginBadge origin={entry.origin} size="xs" iconOnly />
                ) : null}
                <span
                  className={cn(
                    "shrink-0 text-[11.5px] font-medium",
                    state.text
                  )}
                >
                  {state.label}
                </span>
                <span className="studio-nums w-12 shrink-0 text-right font-mono text-[11.5px] text-muted-foreground">
                  {formatElapsed(entry.elapsed_sec)}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
