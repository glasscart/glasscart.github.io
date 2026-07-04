export interface ProductForecast {
  product_id: string
  current_stock: number
  avg_daily_forecast: number
  forecast_horizon_days: number
  demand_std_dev: number
  reorder_point: number
  days_of_supply: number
  needs_reorder: boolean
  stockout_days_observed: number
}

export interface InventoryManifest {
  methodology: {
    forecast: string
    reorder_point: string
  }
  alpha: number
  beta: number
  forecast_horizon_days: number
  assumed_lead_time_days: number
  service_level_z: number
  num_products: number
  num_products_needing_reorder: number
  generated_at: string
  build_duration_seconds: number
}
