export interface Review {
  id: string
  product_id: string
  author: string
  rating: number
  title: string
  body: string
  verified_purchase: boolean
  helpful_votes: number
  created_at: string
  // Ground-truth label from the synthetic dataset generator, not a model
  // output — used only to let Glass Mode show whether the fake-review
  // heuristic's guess actually matches the (synthetic) truth. See
  // datasets/reviews/DATASET_CARD.md.
  is_fake_synthetic: boolean
}

export interface ReviewAnalysis {
  review_id: string
  product_id: string
  sentiment_score: number
  aspects: Record<string, number>
  fake_score: number
  likely_fake: boolean
}

export interface AspectSummary {
  aspect: string
  avg_sentiment: number
  mentions: number
}

export interface ProductReviewSummary {
  product_id: string
  review_count: number
  avg_sentiment: number
  aspects: AspectSummary[]
  likely_fake_count: number
}

export interface ReviewsManifest {
  methodology: {
    sentiment: string
    aspect_extraction: string
    fake_review_heuristic: string
  }
  lexicon_size: number
  fake_score_threshold: number
  fake_heuristic_weights: Record<string, number>
  num_reviews: number
  num_products: number
  fake_heuristic_evaluation: {
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
