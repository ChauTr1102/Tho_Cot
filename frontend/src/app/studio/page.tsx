"use client";

/**
 * `/studio` — the Asset Studio on its own route.
 *
 * The screen itself lives in `components/studio/AssetStudio`, because the same
 * flow is also stage 03 of the campaign pipeline and the two must not drift
 * apart. All this route adds is the entry point: which campaign, read from
 * `?campaign=`, which is how the pipeline deep-links here.
 *
 * Read from `location.search` rather than `useSearchParams` so the page renders
 * without a Suspense boundary.
 */

import { useEffect, useState } from "react";

import { AssetStudio } from "@/components/studio/AssetStudio";

export default function StudioPage() {
  const [campaignId, setCampaignId] = useState<string | null>(null);

  useEffect(() => {
    setCampaignId(new URLSearchParams(window.location.search).get("campaign"));
  }, []);

  return <AssetStudio campaignId={campaignId} />;
}
