# GlassCart

> **AI-First. AI-Transparent.**
>
> *An open-source, educational, AI-native commerce platform where every AI-assisted decision is explainable, inspectable, reproducible, and replaceable.*

---

# Your Role

You are a team of senior software engineers, AI/ML engineers, MLOps engineers, UX designers, DevOps engineers, technical writers, security engineers, and educators.

Your goal is to build **GlassCart**, an open-source educational marketplace inspired by the architecture and user experience of modern large-scale e-commerce platforms.

This project is **NOT** intended to copy or reproduce Amazon's branding, assets, trademarks, colors, copyrighted content, proprietary designs, or proprietary implementation details.

Instead, it should recreate the *concepts*, *architecture*, *workflows*, *scale*, and *technical challenges* involved in building a modern AI-native commerce platform.

The finished project should feel like:

- the React documentation
- Kubernetes documentation
- VS Code
- PyTorch
- LangChain
- TensorFlow

combined into one large educational project.

It should become **the definitive open-source reference implementation of an AI-transparent commerce platform.**

---

# Before Writing Any Code

Do not immediately start implementing.

First perform extensive research.

Research should include:

- modern e-commerce architecture
- recommendation systems
- retrieval systems
- semantic search
- learning-to-rank
- product search
- fraud detection
- demand forecasting
- dynamic pricing
- customer support AI
- seller tooling
- inventory optimization
- experimentation platforms
- MLOps
- Explainable AI (XAI)
- Responsible AI
- AI transparency
- model cards
- dataset cards
- ML observability
- AI governance
- feature stores
- vector databases
- embeddings
- RAG
- LLM integrations
- synthetic data generation
- GitHub Pages limitations
- static-first architectures
- offline-first applications
- browser ML
- WebAssembly ML
- ONNX Runtime Web
- TensorFlow.js
- transformers.js
- accessibility
- privacy
- security
- modern frontend architecture
- CI/CD
- GitHub Actions
- reproducible research
- experiment tracking

Research both:

- academic literature
- engineering blogs
- conference talks
- open-source projects
- architecture case studies
- official documentation
- RFCs
- standards
- production best practices

Whenever possible, prefer:

- official documentation
- peer-reviewed papers
- engineering blogs from reputable companies
- open-source implementations

Avoid relying solely on tutorials.

---

# Build a Research Library

Create a documentation section called:

```
docs/research/
```

Include:

- summaries
- citations
- links
- implementation notes
- why each resource matters
- where it is used in GlassCart

Every major subsystem should include a bibliography.

Do NOT simply dump links.

Explain how each reference influenced the implementation.

---

# Core Philosophy

Everything should be:

- AI-first
- AI-transparent
- educational
- modular
- reproducible
- inspectable
- offline-first
- deterministic where possible
- well documented
- extensively tested
- easily replaceable

Nothing should feel like a black box.

---

# AI Transparency

This is the defining feature of GlassCart.

Every AI-assisted decision must expose:

- why AI was used
- why this model was selected
- model version
- model architecture
- training dataset
- dataset version
- training date
- evaluation metrics
- confidence
- uncertainty
- latency
- hardware used
- inference pipeline
- preprocessing
- postprocessing
- feature importance
- explanation
- limitations
- known failure cases
- ethical considerations
- privacy considerations
- reproducibility instructions

Every AI component must have an inspectable interface.

---

# Glass Mode

Create a global toggle called:

```
Glass Mode
```

When enabled, every AI-assisted UI element should expose diagnostics.

Examples:

- recommendations
- search
- ranking
- pricing
- chatbot
- forecasts
- fraud scores
- moderation
- review summaries

The UI should make it obvious:

- what is AI
- what is deterministic
- what is simulated

---

# Scale

This should be an extensive project.

Do not intentionally limit scope.

Cover as many realistic commerce use cases as reasonably possible.

If there is a meaningful AI application in commerce, consider implementing it.

Think like you're building a learning platform for several years, not a weekend demo.

---

# Project Structure

Design a clean monorepo.

Example:

```
glasscart/

apps/
packages/
services/
training/
inference/
models/
datasets/
embeddings/
experiments/
benchmarks/
docs/
scripts/
.github/
```

Improve this if needed.

---

# Technology

Prefer modern open-source tooling.

Frontend

- React
- TypeScript
- Vite
- Tailwind
- React Router
- Zustand
- TanStack Query

Documentation

- MkDocs
- Storybook

Python

- Python 3.13+

Machine Learning

Research current best tooling before deciding.

Potential examples:

- scikit-learn
- LightGBM
- XGBoost
- sentence-transformers
- transformers
- ONNX Runtime
- TensorFlow
- PyTorch

Only use tools when they make sense.

Do not include unnecessary dependencies.

---

# AI Systems

Research modern implementations before designing.

Potential areas include (but are not limited to):

## Search

- keyword search
- semantic search
- hybrid search
- autocomplete
- spelling correction
- query understanding
- multilingual search
- visual search
- voice search

---

## Recommendation

Research every major recommendation family.

Potential examples:

- popularity
- collaborative filtering
- content-based
- hybrid
- embeddings
- graph-based
- session-based
- sequence models
- LLM-assisted
- knowledge graph
- two-tower retrieval

Do not limit yourself to these.

---

## Ranking

Research production ranking systems.

Potential topics:

- candidate generation
- learning-to-rank
- diversification
- personalization
- business rules
- reranking

---

## Pricing

Research pricing systems.

Potential examples:

- elasticity
- demand
- inventory
- promotions
- coupons
- markdowns
- simulations

---

## Inventory

Research:

- forecasting
- replenishment
- warehouse optimization
- demand planning

---

## Fraud

Research:

- account fraud
- payment fraud
- fake reviews
- return abuse
- seller fraud
- bots

---

## Reviews

Research:

- summarization
- spam detection
- sentiment
- toxicity
- aspect extraction
- fake review detection

---

## Vision

Research:

- OCR
- tagging
- categorization
- duplicate detection
- quality assessment
- image embeddings

---

## NLP

Research:

- assistants
- RAG
- retrieval
- summarization
- intent classification
- entity extraction

---

## Analytics

Research:

- experimentation
- A/B testing
- causal inference
- feature importance
- drift detection
- calibration
- observability

---

# Documentation

Documentation should be exceptional.

Every subsystem should include:

- overview
- architecture
- implementation
- diagrams
- algorithms
- tradeoffs
- references
- glossary
- further reading

The documentation should teach.

Do not assume prior knowledge.

---

# Educational Focus

Every algorithm should answer:

- What problem does this solve?
- Why does it exist?
- How does it work?
- Why was this implementation chosen?
- What are the alternatives?
- What are its strengths?
- What are its weaknesses?
- How can it fail?
- How can it be improved?

---

# Visualizations

Where appropriate, build interactive visualizations for:

- recommendation graphs
- embeddings
- ranking pipeline
- search pipeline
- feature importance
- confusion matrices
- ROC curves
- SHAP
- LIME
- training metrics
- experiment comparisons
- inference pipeline
- vector search
- attention
- clustering

The project should help users understand the algorithms.

---

# Datasets

Generate realistic synthetic datasets.

Include generation scripts.

Datasets should cover:

- products
- users
- sellers
- orders
- reviews
- inventory
- sessions
- searches
- clicks
- carts
- warehouses
- pricing history

Everything should be reproducible.

---

# Model Cards

Every model should include:

- purpose
- architecture
- dataset
- metrics
- limitations
- ethical considerations
- intended use
- non-intended use
- reproducibility

---

# Dataset Cards

Every dataset should include:

- schema
- provenance
- generation process
- intended use
- limitations
- bias discussion
- regeneration instructions

---

# Reproducibility

Anyone should be able to clone the repository and:

- install dependencies
- regenerate datasets
- retrain every model
- evaluate every model
- rebuild documentation
- run the site locally

using documented commands.

No paid APIs should be required.

---

# Model Training

Support multiple workflows.

## Workflow A

Ship lightweight pretrained models with the repository.

The site should work immediately after cloning.

---

## Workflow B

Allow local retraining.

Example:

```
npm run train
```

or

```
uv run train.py
```

---

## Workflow C

GitHub Actions should automatically:

- retrain models
- evaluate models
- compare metrics
- version artifacts
- regenerate documentation
- deploy GitHub Pages

where practical.

---

# GitHub Pages

The project must be deployable on GitHub Pages.

Research GitHub Pages limitations.

Design around them.

If optional backend services are useful, make them optional.

The static site should remain functional.

---

# Offline First

Everything that reasonably can work offline should work offline.

Optional cloud integrations should remain optional.

Support providers like:

- Ollama
- LM Studio
- OpenAI
- Anthropic

through pluggable adapters.

Never require them.

---

# Code Quality

Follow industry best practices.

- modular architecture
- reusable components
- dependency inversion
- clean APIs
- strict typing
- comprehensive tests
- linting
- formatting
- accessibility
- security
- maintainability

Favor readability over cleverness.

---

# CI/CD

Implement professional CI/CD.

Research modern best practices.

Potential pipeline stages:

- lint
- test
- type check
- build
- documentation
- model evaluation
- benchmark
- deployment

---

# Benchmarks

Create benchmarking tools.

Compare:

- algorithms
- models
- ranking quality
- latency
- memory
- inference cost

Visualize results.

---

# Extensibility

Design GlassCart as a platform.

Developers should be able to add:

- datasets
- models
- recommenders
- search engines
- ranking algorithms
- LLM providers
- dashboards
- visualizations

without modifying core code.

---

# Deliverables

Produce:

- production-quality code
- extensive documentation
- architecture diagrams
- API documentation
- developer guides
- contributor guides
- research summaries
- benchmarking tools
- testing infrastructure
- synthetic datasets
- training pipelines
- evaluation pipelines
- CI/CD
- GitHub Pages deployment
- interactive educational visualizations

---

# Guiding Principle

Whenever faced with a design decision, ask:

> "Would this help someone understand how modern AI-powered commerce systems actually work?"

If the answer is yes, implement it.

If there are multiple valid approaches, research them, document the tradeoffs, explain why one was chosen, and cite the relevant sources.

The final result should be the most comprehensive, educational, transparent, and extensible open-source AI-commerce reference implementation possible.