"use client";

/**
 * Stage 03 — Sáng tạo chiến dịch.
 *
 * This used to be a mock: a three-and-a-half-second fake agent, then a hardcoded
 * list of creative routes and commerce copy that came from nowhere and went
 * nowhere. It is now the Asset Studio itself, reading the campaign the pipeline
 * has been walking through and producing real images and video against it.
 *
 * The studio is mounted, not linked to. Stage 03 *is* content generation, so
 * sending the user to another route in the middle of a pipeline would break the
 * one thing a pipeline is for. `AssetStudio` drops its own backdrop and masthead
 * when embedded and inherits this screen's theme.
 */

import * as React from "react";

import { AssetStudio } from "@/components/studio/AssetStudio";

interface StageContentGenerationProps {
  /** The campaign being walked through. Null falls back to the first campaign
      research has finished, which keeps the stage usable when opened directly. */
  campaignId?: string | null;
}

export const StageContentGeneration: React.FC<StageContentGenerationProps> = ({
  campaignId = null,
}) => {
  return (
    <div className="flex flex-col animate-in fade-in duration-500">
      <div className="shrink-0 space-y-2 border-b border-foreground/10 pb-4">
        <h2 className="font-mono text-lg font-bold tracking-wider text-foreground">
          SÁNG TẠO CHIẾN DỊCH
        </h2>
        <p className="font-mono text-sm text-foreground/40">
          Dựng ảnh và video theo chuẩn từng sàn, giữ nguyên sản phẩm thật.
        </p>
      </div>

      <div className="pt-4">
        <AssetStudio campaignId={campaignId} embedded />
      </div>
    </div>
  );
};
