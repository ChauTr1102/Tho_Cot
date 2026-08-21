/**
 * The studio screen's shared visual vocabulary for graph state and node kind.
 *
 * Kept in one table so the shell, the activity ledger and Task 13's `NodeCard`
 * cannot drift apart: a node that reads gold on the canvas must read gold in
 * the ledger. Colour is never the only carrier — every state also has a
 * Vietnamese label and every kind has an icon.
 *
 * The state treatments follow the plan's table:
 *   pending  muted, dimmed        running  lime + glow + pulse
 *   done     solid lime           retry    gold + attempt counter
 *   degraded gold + fallback tag  failed   danger
 */

import {
  Camera,
  Clapperboard,
  Film,
  Image as ImageIcon,
  Layers,
  ListChecks,
  ScanEye,
  Scissors,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

import type { NodeKind, NodeState } from "@/types/studio";

export interface NodeStateMeta {
  /** Vietnamese label, sentence case. */
  label: string;
  /** Border + text classes for a chip or card in this state. */
  chip: string;
  /** Text-only colour, for ledger rows. */
  text: string;
  /** Background for the state dot. */
  dot: string;
  /** True while the node is doing work — drives the pulsing halo. */
  live: boolean;
}

export const NODE_STATE_META: Record<NodeState, NodeStateMeta> = {
  pending: {
    label: "Chờ",
    chip: "border-border/70 text-muted-foreground opacity-45",
    text: "text-muted-foreground",
    dot: "bg-muted-foreground/50",
    live: false,
  },
  running: {
    label: "Đang chạy",
    chip: "border-primary/70 text-foreground shadow-[0_0_28px_-10px_var(--primary)]",
    text: "text-primary",
    dot: "bg-primary",
    live: true,
  },
  done: {
    label: "Xong",
    chip: "border-primary/45 text-foreground",
    text: "text-primary",
    dot: "bg-primary",
    live: false,
  },
  retry: {
    label: "Thử lại",
    chip: "border-gold/60 text-foreground",
    text: "text-gold",
    dot: "bg-gold",
    live: true,
  },
  degraded: {
    label: "Dự phòng",
    chip: "border-gold/50 text-foreground",
    text: "text-gold",
    dot: "bg-gold",
    live: false,
  },
  failed: {
    label: "Lỗi",
    chip: "border-destructive/60 text-foreground",
    text: "text-destructive",
    dot: "bg-destructive",
    live: false,
  },
};

export interface NodeKindMeta {
  label: string;
  icon: LucideIcon;
}

const FALLBACK_KIND: NodeKindMeta = { label: "Bước", icon: Layers };

const KIND_TABLE: Record<string, NodeKindMeta> = {
  plan: { label: "Kế hoạch", icon: ListChecks },
  inventory: { label: "Kiểm kho ảnh", icon: Camera },
  worksheet: { label: "Phân tuyến", icon: ListChecks },
  image: { label: "Ảnh", icon: ImageIcon },
  keyframe: { label: "Khung hình", icon: Sparkles },
  video: { label: "Video", icon: Film },
  inspect: { label: "Soi lỗi", icon: ScanEye },
  compose: { label: "Ghép", icon: Clapperboard },
  cutdown: { label: "Bản cắt", icon: Scissors },
};

/** Never throws on an unrecognised kind — the backend may add more. */
export function kindMeta(kind: NodeKind): NodeKindMeta {
  return KIND_TABLE[kind] ?? FALLBACK_KIND;
}
