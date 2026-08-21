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
 * evaluate: when this stage's own generation output isn't available yet (the
 * studio's real output is not surfaced as a single DTO callback the way the
 * old mock's `onGenerated` was), callers fall back to
 * `buildMockCampaignOutput` (see @/types/campaign_output_mock) built from the
 * real research plan, so those downstream stages never see empty data.
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
      {/* No heading. The pipeline rail already names this stage, and a title
          plus a subtitle repeating it cost the graph the top of the fold. */}
      <div>
        <AssetStudio campaignId={campaignId} embedded />
      </div>
    </div>
  );
};
