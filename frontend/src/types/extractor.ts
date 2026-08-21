export interface ExtractRequest {
  url: string;
  render?: boolean;
  model?: string;
}

export interface TikTokProductBrief {
  product_name: string;
  category: string;
  key_selling_points: string[];
  price_or_promotion: {
    price?: number;
    currency: string;
    promotion?: string;
  };
  target_market: string;
  required_claims: string[];
  restricted_or_forbidden_claims: string[];
}

export interface TikTokBrandKit {
  logo: { path?: string };
  brand_colors: {
    primary?: string;
    secondary?: string;
    accent: string[];
    palette: string[];
  };
  tone_of_voice: {
    description: string;
    attributes: string[];
    do: string[];
    dont: string[];
  };
  product_photos: string[];
  existing_product_visuals: string[];
}

export interface TikTokAudienceBrief {
  target_customer: string;
  language: string;
  platform: string;
  market: string;
}

export interface TikTokMarketSignal {
  trend?: string;
  seasonal_moment?: string;
  consumer_pain_point?: string;
  search_keyword: string[];
  competitor_angle?: string;
  campaign_objective: string;
}

export interface TikTokPastCampaignData {
  enabled: boolean;
  ctr?: number;
  cvr?: number;
  roas?: number;
  watch_time: { value?: number; unit: string };
  add_to_cart_rate?: number;
  comments: string[];
  sales_results: { units_sold?: number; revenue?: number; currency: string };
}

export interface TikTokExtractionData {
  product_brief: TikTokProductBrief;
  brand_kit: TikTokBrandKit;
  audience_brief: TikTokAudienceBrief;
  market_signal: TikTokMarketSignal;
  past_campaign_data: TikTokPastCampaignData;
}

export interface ExtractResponse {
  url: string;
  data: TikTokExtractionData;
}
