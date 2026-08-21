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
 *
 * The QA gate / final report still need a CampaignOutputDTO-shaped object to
 * evaluate: `onAssetsReady` surfaces the studio's real output (real generated
 * images/video, as `/media/...` paths — see @/types/studio's
 * StudioAssetDTOResponse) once a run finishes. Until a run has finished (or
 * for the fields the studio doesn't own — positioning, creative routes,
 * A/B plan), callers fall back to `buildMockCampaignOutput` (see
 * @/types/campaign_output_mock) built from the real research plan, so those
 * downstream stages never see empty data.
 */

import * as React from "react";
import { AssetStudio } from "@/components/studio/AssetStudio";
import type { StudioAssetDTOResponse } from "@/types/studio";

interface StageContentGenerationProps {
  /** The campaign being walked through. Null falls back to the first campaign
      research has finished, which keeps the stage usable when opened directly. */
  campaignId?: string | null;
  /** Called with the real generated assets once the studio run underneath
      this stage finishes, so the pipeline can feed real data into the QA
      gate / final report instead of always falling back to the mock. */
  onAssetsReady?: (assets: StudioAssetDTOResponse) => void;
}

export const StageContentGeneration: React.FC<StageContentGenerationProps> = ({
  campaignId = null,
  onAssetsReady,
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
        <AssetStudio campaignId={campaignId} embedded onAssetsReady={onAssetsReady} />
      </div>
    </div>
  );
};
