# Project #31: The Compute Oracle
## WeaveHacks 3 — Front-Runner Project

**Status:** FRONT-RUNNER. Build this first.
**Solo build target:** ~16 hours (Saturday 10:30 AM → Sunday 1:15 PM)
**Score:** 42/50 (Impressiveness: 9, Uniqueness: 10, Completion: 6, Demo: 8, Sponsors: 9)

---

## One-Liner

A self-improving agent that predicts compute cost fluctuations by tracking real-world causal factors (energy prices, weather, geopolitics, supply chain) and learns to schedule workloads during predicted price dips.

## Why This Wins

1. **Zero prior art found.** No hackathon project, no startup, no research paper treats compute cost as a predictable signal driven by exogenous real-world factors. Tools like Cast AI, nOps, and Revefi do reactive cost optimization — they detect waste after the fact. This *predicts the future*.
2. **Hits the 2026 narrative.** Every trend report (IBM, Google, Microsoft, Oracle) flags AI compute cost as the defining constraint of 2026. MIT Sloan: "Power shortages, grid congestion, and energy cost inflation are directly impacting feasibility and profitability."
3. **Four sponsors used meaningfully:**
   - **Redis** ($500 credits): Time-series price signal cache + causal factor graph store
   - **Browserbase/Stagehand**: Scraping energy prices, news, spot market data in real-time
   - **W&B Weave** (required): Prediction accuracy tracking over time, learning loop observability
   - **Vercel**: Dashboard showing predictions, causal graph, savings tracker
4. **Clear self-improvement loop:** Agent makes price predictions → ground truth arrives → agent evaluates its accuracy → updates its causal model → next predictions are better. Measurable: prediction error decreasing over iterations.
5. **Relevant background:** You built `excost` (Rust CLI for real-time ML experiment cost tracking). You understand the compute cost domain. This is credible.

## Judging Criteria Alignment

| Criterion | How This Scores |
|-----------|----------------|
| **Creativity** | Nobody has done this. Novel problem AND novel approach. |
| **Self-improving-ness** | Causal model evolves with each prediction cycle. Accuracy measurably improves. |
| **Utility** | Solves a real, expensive problem. "Saved 40% on compute by predicting a price dip" is immediately understandable. |
| **Technical execution** | Clean architecture: scraper → causal model → predictor → scheduler → evaluator → learner |
| **Sponsor usage** | Redis, Browserbase, Weave, Vercel — all meaningful, not bolted on |

## WeaveHacks 2 Context

- **Grand Prize (Daydreamer)** won by applying a known concept (pretraining) to a novel domain (robotics). This applies a known concept (predictive modeling) to a novel domain (compute cost from exogenous signals).
- **Your Orch** had strong metrics (100% success, zero hallucinations) but was a pipeline orchestrator — a pattern judges had seen many times. This is something judges have never seen.

---

## Data Sources (Addressing the "enough verifiable data" concern)

| Source | What It Provides | API/Access | Update Freq |
|--------|-----------------|------------|-------------|
| **AWS Spot Instance Pricing** | Per-instance-type, per-AZ price history | `DescribeSpotPriceHistory` API (free, no auth needed for public data) | Every 5 min |
| **EIA Electricity Prices** | US electricity spot prices by region | `api.eia.gov` (free API key) | Hourly |
| **OpenWeatherMap** | Temperature, extreme weather events (heatwaves spike cooling costs) | Free tier, 1000 calls/day | Real-time |
| **GPU Cloud Pricing** | Spot/on-demand prices across providers | CloudPrice.net scrape via Browserbase, or Lambda Labs API | Hourly |
| **News/Events** | Tariff announcements, chip sanctions, supply chain disruptions | Browserbase scraping of Reuters/Bloomberg headlines | Real-time |

**Minimum viable:** AWS Spot + EIA Electricity = 2 solid quantitative sources with historical data for backtesting.
**Full version:** All 5 sources with Browserbase for news/GPU pricing.

### Backtesting Strategy (Critical for Demo)

Instead of waiting for real price changes during the hackathon, use **historical replay**:
1. Load 3-6 months of historical spot pricing + electricity prices + weather data
2. Agent "trains" on first 2 months, predicts the rest
3. Show prediction accuracy improving as it processes more data
4. Highlight specific events: "Texas grid stress in July → my agent learned to predict AWS us-east-1 price spikes from temperature forecasts"

This makes the demo work without needing live price fluctuations during the hackathon.

---

## Architecture

```
                    +------------------+
                    |   Browserbase    |
                    |  News Scraper    |
                    +--------+---------+
                             |
+---------------+   +--------v---------+   +----------------+
| EIA Energy API|-->|                  |-->| Redis          |
+---------------+   |  Signal Ingester |   | Time-Series    |
+---------------+   |                  |   | + Causal Graph |
| AWS Spot API  |-->|                  |   +-------+--------+
+---------------+   +------------------+           |
+---------------+            |              +------v--------+
| Weather API   |-->---------+              |               |
+---------------+                           | Causal Model  |
                                            | (LLM-based)   |
                                            |               |
                                            +------+--------+
                                                   |
                                            +------v--------+
                                            |               |
                                            |  Predictor    |
                                            |  (forecasts)  |
                                            +------+--------+
                                                   |
                                      +------------+------------+
                                      |                         |
                               +------v--------+     +---------v-------+
                               |  Scheduler    |     |  Evaluator      |
                               |  (when to run |     |  (prediction vs |
                               |   workloads)  |     |   ground truth) |
                               +---------------+     +--------+--------+
                                                              |
                                                     +--------v--------+
                                                     |  Learner        |
                                                     |  (update causal |
                                                     |   model weights)|
                                                     +-----------------+
                                                              |
                                                     +--------v--------+
                                                     |  W&B Weave      |
                                                     |  (trace all     |
                                                     |   predictions   |
                                                     |   + learning)   |
                                                     +-----------------+
```

## Component Breakdown

### 1. Signal Ingester
- Pulls data from all sources on a schedule (or replays historical data for demo)
- Normalizes into a common time-series format
- Stores in Redis with TTL for sliding windows

### 2. Causal Model (The Brain)
- LLM-based reasoning over signals: "Given these factors, predict compute price direction"
- Maintains a **causal factor graph** in Redis: nodes = factors (temperature, electricity price, news events), edges = learned correlations with compute pricing
- Key self-improvement: edge weights in the causal graph update based on prediction accuracy

### 3. Predictor
- Takes current signals + causal model → outputs price forecast for next N hours
- Confidence score for each prediction
- Logs every prediction to Weave for tracking

### 4. Scheduler
- Given predictions, decides optimal time windows for compute tasks
- Compares "scheduled cost" vs "naive cost" (run immediately) to show savings

### 5. Evaluator
- When ground truth arrives, compares prediction vs actual
- Calculates prediction error metrics (MAE, directional accuracy)
- Identifies which causal factors were most/least predictive

### 6. Learner
- Updates causal model based on evaluator feedback
- Strengthens edges for factors that predicted correctly
- Weakens/prunes edges for noise factors
- This is the self-improvement loop — runs after each evaluation cycle

### 7. Dashboard (Vercel)
- Real-time view of: current signals, causal graph, predictions, actual prices, accuracy over time
- The "savings tracker": cumulative $ saved by scheduling optimally
- Learning curve: prediction accuracy improving over iterations

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Backend | Python + FastAPI | Fast to build, good async support |
| LLM | W&B Weave inference credits ($50) or OpenAI | Causal reasoning + prediction |
| Cache/Store | Redis Cloud ($500 credits) | Time-series, causal graph, prediction cache |
| Web Scraping | Browserbase/Stagehand | News, GPU pricing |
| Observability | W&B Weave | Trace every prediction + learning cycle |
| Frontend | Next.js on Vercel ($10 v0 credits) | Dashboard |
| Data APIs | AWS Spot API, EIA API, OpenWeatherMap | Signal sources |

---

## Build Sequence (16 hours)

### Phase 1: Core Loop (Hours 0-5)
1. Set up project skeleton + Redis connection + Weave integration
2. Build Signal Ingester with AWS Spot + EIA electricity data (historical replay mode)
3. Build Causal Model v1 (simple LLM prompt: "given these signals, predict price direction")
4. Build Evaluator (compare prediction vs ground truth from historical data)
5. Build Learner v1 (update prompt/weights based on evaluator feedback)
6. **Checkpoint:** Core self-improvement loop working end-to-end

### Phase 2: Expand + Polish (Hours 5-10)
7. Add weather data source
8. Add Browserbase news scraping
9. Build Scheduler (optimal time window selection)
10. Build causal graph structure in Redis (not just flat signals)
11. **Checkpoint:** Full pipeline with 4+ data sources, scheduling, and learning

### Phase 3: Demo Layer (Hours 10-14)
12. Build Vercel dashboard (causal graph viz, prediction timeline, savings tracker, accuracy curve)
13. Run full backtest over 3-6 months of data, generate compelling Weave traces
14. Identify 2-3 "wow moments" in the data (specific events where the agent learned a causal pattern)
15. **Checkpoint:** Demo-ready

### Phase 4: Polish (Hours 14-16)
16. Record demo video (< 2 min)
17. Clean up GitHub repo, write README
18. Prepare 3-minute live presentation (heavy on live demo, max 1-2 slides)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Correlations aren't real/visible | Use historical backtesting where known events (Texas grid crisis, tariff announcements) had documented price impacts. Cherry-pick compelling examples for demo. |
| AWS Spot API is hard to access | CloudPrice.net has public historical data scrapable via Browserbase. Fallback: synthetic but realistic price data based on documented patterns. |
| LLM causal reasoning is too noisy | Use structured prompts with explicit factor listing. The self-improvement loop should improve signal-to-noise over iterations. |
| Dashboard takes too long | Use Vercel v0 credits to generate Next.js dashboard quickly. Alternatively, Marimo notebook as backup visualization. |
| Too ambitious for 16h solo | Phase 1 alone (core loop + 2 data sources + learning) is a viable submission. Each subsequent phase adds polish. |

---

## Demo Script (3 minutes)

**Slide 1** (15 sec): "Every company running ML is bleeding money on compute. Spot prices fluctuate based on real-world factors nobody is tracking. I built an agent that predicts price dips and schedules workloads to exploit them."

**Live demo** (2 min):
1. Show the dashboard — current signals coming in (energy prices, weather, news)
2. Show the causal graph — "The agent learned that temperature in Virginia correlates with us-east-1 spot pricing"
3. Show the prediction timeline — "It predicted a dip here, scheduled a training job, saved 37%"
4. Show the accuracy curve — "Over 100 prediction cycles, accuracy went from 52% to 78%"
5. Show a Weave trace — "Here's the self-improvement loop in action"

**Close** (30 sec): "This is the first agent that treats compute cost as a predictable, tradeable signal. It gets better every cycle. Built with Redis for the signal cache, Browserbase for real-world data, Weave for observability, and deployed on Vercel."

---

## Key Differentiators to Emphasize

1. **Not cloud cost optimization** (reactive). This is **cloud cost prediction** (proactive).
2. **Exogenous factors** — weather, politics, supply chain — not just historical pricing patterns.
3. **Self-improving causal model** — the agent learns WHICH factors matter, not just how to use pre-defined features.
4. **Practical savings** — show a dollar amount saved in the demo.

---

## Relevant Previous Work

- **excost** (`/Users/bledden/Documents/excost/`): Rust CLI for real-time ML experiment cost tracking. You understand compute cost measurement. This project extends from "tracking costs" to "predicting and optimizing costs."
- **Anomaly Hunter** (`/Users/bledden/Documents/anomaly-hunter/`): Multi-agent consensus with adaptive weighting, real-time streaming data. The signal ingestion and anomaly pattern detection architecture is transferable.
- **Corch/Facilitair** (`/Users/bledden/Documents/Corch_by_Fac/`): Foundation model trace→retrain loop. The self-improvement architecture (collect data → evaluate → retrain → deploy) maps directly to this project's learning loop.
