export interface Transaction {
  id: string
  product_id: string
  buyer_id: string
  quantity: number
  amount: number
  payment_method: string
  shipping_region: string
  billing_region: string
  buyer_account_age_days: number
  created_at: string
  // Ground-truth label from the synthetic dataset generator, not a model
  // output — see datasets/transactions/DATASET_CARD.md.
  is_fraud_synthetic: boolean
}

export interface FraudScore {
  transaction_id: string
  fraud_score: number
  likely_fraud: boolean
  indicators: {
    velocity: number
    region_risk: number
    new_account_high_value: number
  }
}

export interface FraudManifest {
  methodology: {
    velocity: string
    region_risk: string
    new_account_high_value: string
  }
  weights: Record<string, number>
  fraud_score_threshold: number
  num_transactions: number
  fraud_evaluation: {
    true_positives: number
    false_positives: number
    false_negatives: number
    true_negatives: number
    precision: number
    recall: number
    f1: number
    caveat: string
  }
  generated_at: string
  build_duration_seconds: number
}
