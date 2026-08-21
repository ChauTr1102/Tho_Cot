// ---------------------------------------------------------
// INPUT DTO (Updated JSON Format)
// ---------------------------------------------------------

export interface PriceOrPromotion {
  price?: number | null;
  currency: string;
  promotion?: string | null;
}

export interface ProductBrief {
  productName: string;
  category: string;
  keySellingPoints: string[];
  priceOrPromotion: PriceOrPromotion;
  targetMarket: string;
  requiredClaims: string[];
  restrictedOrForbiddenClaims: string[];
}

export interface Logo {
  path?: string | null;
}

export interface BrandColors {
  primary?: string | null;
  secondary?: string | null;
  accent: string[];
  palette: string[];
}

export interface ToneOfVoice {
  description: string;
  attributes: string[];
  do: string[];
  dont: string[];
}

export interface BrandKit {
  logo: Logo;
  brandColors: BrandColors;
  toneOfVoice: ToneOfVoice;
  productPhotos: string[];
  existingProductVisuals: string[];
}

export interface AudienceBrief {
  targetCustomer: string;
  language: string;
  platform: string;
  market: string;
}

export interface MarketSignal {
  trend?: string | null;
  seasonalMoment?: string | null;
  consumerPainPoint?: string | null;
  searchKeyword: string[];
  competitorAngle?: string | null;
  campaignObjective: string;
}

export interface WatchTime {
  value?: number | null;
  unit: string;
}

export interface SalesResults {
  unitsSold?: number | null;
  revenue?: number | null;
  currency: string;
}

export interface PastCampaignData {
  enabled: boolean;
  ctr?: number | null;
  cvr?: number | null;
  roas?: number | null;
  watchTime: WatchTime;
  addToCartRate?: number | null;
  comments: string[];
  salesResults: SalesResults;
}

export interface CampaignInputDTO {
  productBrief: ProductBrief;
  brandKit: BrandKit;
  audienceBrief: AudienceBrief;
  marketSignal: MarketSignal;
  pastCampaignData: PastCampaignData;
}

// ---------------------------------------------------------
// OUTPUT DTO
// ---------------------------------------------------------

export interface ProductPositioning {
  mainCampaignAngle: string;
  targetAudience: string;
  keySellingMessage: string;
  productBenefitHierarchy: string[];
}

export interface CreativeRoute {
  name: string;
  hookIdea: string;
  visualDirection: string;
  messageAngle: string;
  suggestedPlatformUsage: string[];
}

export interface ShortFormVideoAsset {
  generatedVideoUrls: string[];
  format: string; // default "9:16"
  duration: string; // default "15-30s"
  additionalCuts: string[];
}

export interface ProductCollectionImageSet {
  productHeroImage: string;
  skuDetailImage: string;
  campaignCollectionImage: string;
  marketplaceThumbnail: string;
  promotionBanner?: string;
  bundleImage?: string;
  seasonalSaleImage?: string;
}

export interface CommerceCopy {
  productTitle: string;
  productDescription: string;
  listingBulletPoints: string[];
  adCaption: string;
  promotionCopy: string;
  shortHookLines: string[];
}

export interface ABTestingPlan {
  whatToTest: string;
  routeADescription: string;
  routeBDescription: string;
  suggestedSuccessMetrics: string[];
  expectedLearning: string;
}

export interface PerformanceLearning {
  whatToKeep: string[];
  whatToChange: string[];
  whatToStop: string[];
  whatToTestNext: string[];
}

export interface CampaignOutputDTO {
  productPositioning: ProductPositioning;
  creativeRoutes: CreativeRoute[];
  shortFormVideoAsset: ShortFormVideoAsset;
  productCollectionImageSet: ProductCollectionImageSet;
  commerceCopy: CommerceCopy;
  abTestingPlan: ABTestingPlan;
  performanceLearning?: PerformanceLearning;
}
