export interface PricingCurvePoint {
  price_multiplier: number
  price: number
  quantity: number
  revenue: number
  profit: number
}

export interface PricingRecommendation {
  product_id: string
  elasticity: number
  marginal_cost: number
  current_price: number
  current_quantity: number
  current_revenue: number
  current_profit: number
  optimal_price: number
  optimal_quantity: number
  optimal_revenue: number
  optimal_profit: number
  price_change_pct: number
  profit_uplift_pct: number
  recommendation: 'raise' | 'lower' | 'near-optimal'
  curve: PricingCurvePoint[]
}

export interface PricingManifest {
  methodology: string
  curve_multipliers: number[]
  raise_threshold_pct: number
  lower_threshold_pct: number
  num_products: number
  recommendation_counts: Record<string, number>
  generated_at: string
  build_duration_seconds: number
}
