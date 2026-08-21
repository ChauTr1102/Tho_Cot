"use client";

/**
 * The approval gate.
 *
 * Between reading the campaign plan and rendering anything, the director puts
 * a proposal on screen: what it intends to make, for which marketplaces, and —
 * the part worth reading — the visual register it wrote for this brief.
 *
 * The register is the reason this screen exists. It is not a preset chosen from
 * six; it is a lighting setup, a set, a lens and a grade authored for this
 * campaign and for whatever the user asked for. Showing it before rendering is
 * what turns "the AI made some pictures" into a decision a person made, and it
 * is the last cheap moment to change course — after approval every adjustment
 * costs a minute of rendering.
 *
 * So the four register fields are editable here, and only here.
 */

import { useState } from "react";
import { Check, PanelLeftClose, Pencil, RotateCcw, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Draft } from "@/lib/studio-draft";

interface DraftPanelProps {
  draft: Draft;
  nodeCount: number;
  approving: boolean;
  onApprove: (edited: Partial<Draft> | undefined) => void;
  onDiscard: () => void;
  onClose?: () => void;
}

export function DraftPanel({
  draft,
  nodeCount,
  approving,
  onApprove,
  onDiscard,
  onClose,
}: DraftPanelProps) {
  const [editing, setEditing] = useState(false);
  const [light, setLight] = useState(draft.register.light);
  const [surface, setSurface] = useState(draft.register.surface);
  const [grade, setGrade] = useState(draft.register.grade);
  const [lens, setLens] = useState(draft.register.lens);

  const dirty =
    light !== draft.register.light ||
    surface !== draft.register.surface ||
    grade !== draft.register.grade ||
    lens !== draft.register.lens;

  const handleApprove = () => {
    onApprove(
      dirty
        ? { register: { ...draft.register, light, surface, grade, lens } }
        : undefined
    );
  };

  return (
    <section
      className="border-border border-r bg-background flex flex-col gap-4 p-4 lg:sticky lg:top-[4.5rem] lg:max-h-[calc(100vh-5.5rem)] overflow-y-auto"
      aria-label="Đề xuất chiến dịch"
    >
      <header className="flex items-start justify-between gap-3 border-b border-border pb-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full bg-primary animate-pulse" />
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-primary">
              Proposing Strategy
            </span>
          </div>
          <h2 className="mt-1 font-display text-[15px] font-semibold tracking-tight text-foreground truncate">
            {draft.register.name}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="shrink-0 font-mono text-[11px] rounded-none">
            {nodeCount} bước
          </Badge>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              title="Thu gọn sidebar"
              className="grid size-6 place-items-center rounded-none text-muted-foreground hover:bg-foreground/5 hover:text-foreground transition-colors"
            >
              <PanelLeftClose className="size-3.5" />
            </button>
          )}
        </div>
      </header>

      {draft.summary ? (
        <p className="text-muted-foreground text-[13.5px] leading-relaxed text-pretty">
          {draft.summary}
        </p>
      ) : null}

      {/* The register. The one thing on this screen that repays reading closely,
          so it gets the most room and the only edit affordance. */}
      <div className="border-border/60 bg-muted/30 rounded-none border p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Sparkles className="text-primary size-3.5" aria-hidden />
            <span className="text-[13px] font-medium">Ngôn ngữ hình</span>
            <code className="text-muted-foreground font-mono text-[11px]">
              {draft.register.name}
            </code>
          </div>
          <div className="flex items-center gap-2">
            {draft.register.source === "preset" ? (
              <Badge
                variant="outline"
                className="border-gold/40 text-gold text-[10px]"
                title="Director không trả về register đủ dùng — đây là preset gần nhất"
              >
                preset
              </Badge>
            ) : null}
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-[12px]"
              onClick={() => setEditing((value) => !value)}
            >
              <Pencil className="size-3" aria-hidden />
              {editing ? "Xong" : "Sửa"}
            </Button>
          </div>
        </div>

        {editing ? (
          <div className="flex flex-col gap-2.5">
            <RegisterField label="Ống kính" value={lens} onChange={setLens} />
            <RegisterField label="Ánh sáng" value={light} onChange={setLight} rows={2} />
            <RegisterField label="Bối cảnh" value={surface} onChange={setSurface} rows={2} />
            <RegisterField label="Màu" value={grade} onChange={setGrade} />
          </div>
        ) : (
          <dl className="flex flex-col gap-2 text-[12.5px] leading-relaxed">
            <RegisterRow label="Ống kính" value={lens} />
            <RegisterRow label="Ánh sáng" value={light} />
            <RegisterRow label="Bối cảnh" value={surface} />
            <RegisterRow label="Màu" value={grade} />
          </dl>
        )}

        {draft.register.why && !editing ? (
          <p className="text-muted-foreground/80 mt-3 text-[12px] leading-relaxed italic">
            {draft.register.why}
          </p>
        ) : null}
      </div>

      {/* The deliverables used to be listed here. They are nodes on the canvas
          now — that is where the shape of the work belongs, and a rail that
          repeats it is the same information twice, in the longer form. What
          stays is the count and the one thing the canvas cannot show: why. */}
      <p className="text-muted-foreground text-[12.5px]">
        <span className="text-foreground font-medium">
          {draft.deliverables.length} asset
        </span>
        {draft.video_shots > 0
          ? ` · 1 video ${draft.video_seconds}s (${draft.video_shots} shot)`
          : ""}{" "}
        — xem sơ đồ bên phải.
      </p>

      {draft.notes.length > 0 ? (
        <ul className="text-muted-foreground flex flex-col gap-1 text-[12px]">
          {draft.notes.slice(0, 2).map((note) => (
            <li key={note} className="flex gap-2">
              <span className="text-primary mt-[7px] size-1 shrink-0 rounded-full bg-current" />
              <span className="leading-relaxed">{note}</span>
            </li>
          ))}
        </ul>
      ) : null}

      <div className="flex items-center gap-2 pt-1">
        <Button
          onClick={handleApprove}
          disabled={approving}
          className="bg-primary hover:bg-primary/90 text-primary-foreground h-10 flex-1 rounded-none font-semibold text-[13.5px]"
        >
          {approving ? (
            <>
              <span className="size-1.5 animate-pulse rounded-none bg-current" />
              Đang bắt đầu…
            </>
          ) : (
            <>
              <Check className="size-4" aria-hidden />
              Duyệt và dựng
            </>
          )}
        </Button>
        <Button
          variant="ghost"
          onClick={onDiscard}
          disabled={approving}
          className="h-10 rounded-none px-3"
          title="Bỏ đề xuất này và mô tả lại"
        >
          <RotateCcw className="size-4" aria-hidden />
        </Button>
      </div>

      {dirty ? (
        <p className="text-gold -mt-2 text-[11.5px]">
          Đã sửa ngôn ngữ hình — bản sửa sẽ được dùng khi dựng.
        </p>
      ) : null}
    </section>
  );
}

function RegisterRow({ label, value }: { label: string; value: string }) {
  if (!value) return null;
  return (
    <div className="grid grid-cols-[62px_minmax(0,1fr)] gap-2">
      <dt className="text-muted-foreground/70 text-[11.5px]">{label}</dt>
      <dd className="text-foreground/90 text-pretty">{value}</dd>
    </div>
  );
}

function RegisterField({
  label,
  value,
  onChange,
  rows = 1,
}: {
  label: string;
  value: string;
  onChange: (next: string) => void;
  rows?: number;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-muted-foreground/70 text-[11px]">{label}</span>
      <textarea
        value={value}
        rows={rows}
        onChange={(event) => onChange(event.target.value)}
        className="border-border/70 bg-background/60 focus:border-primary/60 focus:ring-primary/20 resize-none rounded-none border px-2.5 py-1.5 text-[12.5px] leading-relaxed outline-none focus:ring-2"
      />
    </label>
  );
}

