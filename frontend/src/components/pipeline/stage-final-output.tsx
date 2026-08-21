"use client";

import * as React from "react";
import type { ResearchCampaignPlan, ResearchInput } from "@/types/research";
import type { VerifyChecklistResponseData } from "@/types/qa_checklist";
import { FinalOutputWorkspace } from "./final-output-workspace";

interface Props {
  plan?: ResearchCampaignPlan | null;
  input?: ResearchInput;
  campaignOutput?: Record<string, unknown> | null;
  qaResult?: VerifyChecklistResponseData | null;
}

export const StageFinalOutput: React.FC<Props> = (props) => (
  <FinalOutputWorkspace {...props} />
);
