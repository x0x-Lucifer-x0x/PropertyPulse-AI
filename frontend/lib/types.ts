export interface PropertyData {
  id: number;
  name: string;
  builder: string;
  location: string;
  nearby_locations?: string | null;
  property_type: string;
  bedrooms: number;
  bathrooms?: number | null;
  area_sqft: number;
  price: number;
  price_per_sqft?: number | null;
  possession_date?: string | null;
  rera_number?: string | null;
  amenities?: string | null;
  description?: string | null;
  image_emoji?: string | null;
}

export interface MatchedProperty {
  property: PropertyData;
  match_score: number;
  match_reasons: string[];
}

export interface LeadQualification {
  score: number;
  factors: string[];
  next_action: string;
  intent: string;
}

export interface ChatResponse {
  reply: string;
  properties: MatchedProperty[];
  lead: LeadQualification | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  properties?: MatchedProperty[];
}
