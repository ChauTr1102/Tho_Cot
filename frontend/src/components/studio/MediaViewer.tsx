"use client";

/**
 * Full-size view of one node's output.
 *
 * The thumbnail on the node answers "did it work"; this answers "is it good".
 * A judge deciding whether a generated Shopee banner is actually shippable
 * needs to read the Vietnamese baked into it at full size, and a video needs
 * real transport controls rather than a poster frame.
 *
 * Everything shown here comes from the node's own event payload — there is no
 * second fetch. Opening a result cannot fail.
 */

import { Download } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { OriginBadge } from "@/components/studio/OriginBadge";
import { NODE_STATE_META, kindMeta } from "@/components/studio/state-styles";
import { formatElapsed, isVideoUrl, mediaUrl } from "@/lib/studio-events";
import { cn } from "@/lib/utils";
import type { StudioNode } from "@/types/studio";

interface MediaViewerProps {
  node: StudioNode | null;
  onClose: () => void;
}

export function MediaViewer({ node, onClose }: MediaViewerProps) {
  const url = node ? mediaUrl(node.payload.url ?? node.payload.path) : null;
  const state = node
    ? (NODE_STATE_META[node.state] ?? NODE_STATE_META.pending)
    : null;

  return (
    <Dialog
      open={node !== null && url !== null}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent className="max-w-[min(1100px,calc(100vw-3rem))] gap-3 sm:max-w-[min(1100px,calc(100vw-3rem))]">
        {node && url ? (
          <>
            <DialogHeader className="gap-1 pr-8">
              <DialogTitle className="font-display text-[15px] tracking-tight">
                {node.payload.slot ?? kindMeta(node.kind).label}
              </DialogTitle>
              <DialogDescription className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[12px]">
                <span className="font-mono text-[11.5px]">{node.id}</span>
                {node.payload.origin ? (
                  <OriginBadge origin={node.payload.origin} size="xs" />
                ) : null}
                {state ? (
                  <span className={cn("font-medium", state.text)}>
                    {state.label}
                  </span>
                ) : null}
                {node.elapsed_sec > 0 ? (
                  <span className="studio-nums font-mono text-[11.5px]">
                    {formatElapsed(node.elapsed_sec)}
                  </span>
                ) : null}
                {node.payload.ratio ? (
                  <span className="font-mono text-[11.5px]">
                    {node.payload.ratio}
                  </span>
                ) : null}
                <a
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-primary hover:underline"
                >
                  <Download aria-hidden className="size-3" />
                  Mở tệp gốc
                </a>
              </DialogDescription>
            </DialogHeader>

            <div className="grid max-h-[72vh] min-h-[min(60vh,420px)] place-items-center overflow-hidden rounded-lg bg-black/45">
              {isVideoUrl(url) ? (
                // Muted autoplay so the clip is *moving* the instant it opens —
                // a still frame behind a play button is what the node already
                // showed. Chrome blocks autoplay with sound, so the controls
                // carry the unmute; `loop` keeps a five-second cut watchable
                // while someone talks over it.
                // eslint-disable-next-line jsx-a11y/media-has-caption -- generated
                // marketing footage; the voiceover script is shown in the run log
                <video
                  src={url}
                  controls
                  autoPlay
                  muted
                  loop
                  playsInline
                  className="max-h-[72vh] max-w-full object-contain"
                />
              ) : (
                // eslint-disable-next-line @next/next/no-img-element -- backend
                // media of unknown intrinsic size on a separate origin
                <img
                  src={url}
                  alt={`Kết quả đầy đủ của node ${node.id}`}
                  className="max-h-[72vh] w-auto max-w-full object-contain"
                />
              )}
            </div>

            {Array.isArray(node.payload.qa_notes) &&
            node.payload.qa_notes.length > 0 ? (
              <p className="text-[12px] leading-relaxed text-muted-foreground">
                <span className="font-medium text-gold">Soi lỗi: </span>
                {node.payload.qa_notes.slice(0, 4).join(" · ")}
              </p>
            ) : null}

            {typeof node.payload.prompt === "string" &&
            node.payload.prompt.length > 0 ? (
              <p className="max-h-24 overflow-y-auto rounded-md border border-border bg-muted/40 px-3 py-2 text-[12px] leading-relaxed text-muted-foreground">
                {node.payload.prompt}
              </p>
            ) : null}
          </>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
