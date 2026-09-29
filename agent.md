# Agent Design — ArogyaGrid Multi-Agent System

Built on **Vertex AI Agent Builder / Agent Development Kit (ADK)** with **Gemini 2.x** as the reasoning core for every agent. Agents share a common session/context store (Firestore-backed) so the Orchestrator can pass state between them without re-fetching data.

## 0. Orchestrator Agent

**Role**: Routes requests to the right specialist agent(s), sequences multi-agent workflows, and merges outputs into a single response for the dashboard or patient channel.

- **Input**: any incoming event — a scheduled forecast run, a PHC stock update crossing a threshold, or a patient uploading a prescription.
- **Reasoning**: uses Gemini function-calling to decide which downstream agent(s) to invoke and in what order (e.g., a prescription upload triggers Prescription Explainer → Epidemiological Signal Agent → conditionally Poster Agent, while a nightly cron triggers Demand Forecast → Early Warning → Redistribution).
- **Tools**: agent-invocation tools for all six specialist agents below; a context-store read/write tool.
- **Output**: a routed workflow result plus an audit log entry (which agents ran, on what input, with what confidence).

---

## 1. Demand Forecast Agent

**Role**: Predicts medicine consumption per PHC (and rolled up per district/state) for the next 2–4 weeks.

- **Inputs**: historical dispensation from `InventoryItem`/`PrescriptionEvent`, seasonal/calendar features, local disease-signal features from the Epidemiological Signal Agent (e.g., "dengue signal rising in this block").
- **Tools**: BigQuery ML / Vertex AI Forecasting model-call tool; a "get seasonal context" tool (month, monsoon flag, regional disease calendar).
- **Reasoning pattern**: calls the forecasting model, then uses Gemini to sanity-check and annotate the output in plain language for the dashboard ("Paracetamol demand at PHC X projected to rise 40% over 3 weeks, consistent with rising local fever-case signal").
- **Output**: `ForecastResult` (drug_id, PHC_id, predicted_qty, confidence, explanation_text).

## 2. Stock-out Early Warning Agent

**Role**: Continuously compares live stock levels (Firestore) against the Demand Forecast Agent's projection and a rule-based safety-stock floor, and raises alerts before a stock-out actually happens.

- **Inputs**: `ForecastResult`, live `InventoryItem` levels, lead-time-to-restock per drug.
- **Tools**: threshold-check tool, alert-creation tool (writes to `Alert` table, pushes to Pub/Sub for the dashboard/DHO feed).
- **Reasoning**: combines ML forecast with a deterministic floor rule as fallback (never relies on ML alone for a safety-critical alert) — if either signal predicts a breach within the lead-time window, an alert fires.
- **Output**: `Alert` (drug_id, PHC_id, predicted_stockout_date, severity, recommended_lead_time_action).

## 3. Cross-District Redistribution Optimizer Agent

**Role**: Given an active stock-out alert, finds the best nearby PHC(s) with surplus of that exact drug and recommends a transfer.

- **Inputs**: active `Alert`, district/state-wide `InventoryItem` snapshot, PHC geo-coordinates, minimum-safety-stock-to-retain rule per drug.
- **Tools**: BigQuery query tool (find surplus candidates), Google Maps Platform distance/route tool, an optimization tool (simple constrained scoring: distance × surplus-quality × urgency; can be swapped for OR-Tools for a fuller solver).
- **Reasoning**: Gemini ranks and explains candidate source PHCs in natural language for the DHO to approve/reject with one tap — this keeps a human in the loop for the actual transfer decision.
- **Output**: `RedistributionRecommendation` (from_PHC, to_PHC, drug_id, qty, distance_km, rationale_text).

## 4. Prescription Explainer Agent (patient-facing)

**Role**: Reads a photographed/scanned prescription and explains it to the patient in simple language, in their preferred Indian language.

- **Inputs**: prescription image, patient's selected language, optional patient age/context for tone (never health data beyond what's on the prescription).
- **Tools**: Document AI OCR tool (extract drug names, dosage, doctor's notes), a vetted `Medicine` database lookup tool (molecule/composition, therapeutic class, manufacturer, common side effects, typical alternatives within the same class), Cloud Translation tool.
- **Reasoning pattern**:
  1. OCR + structure the prescription into discrete drug entries.
  2. For each drug, look up the vetted database (not free-generated facts) for molecule, class, manufacturer, side effects.
  3. Use Gemini to compose a plain-language explanation: what it is, why doctors commonly prescribe this class of drug for the likely indication implied by the prescription, what alternatives exist in the same class ("ask your doctor about X if Y doesn't suit you" — never "take X instead"), and side effects to watch for.
  4. Always appends a fixed safety disclaimer footer.
- **Guardrails**: never outputs a dosage change, never says "stop taking," never diagnoses; low-OCR-confidence drug names are flagged for patient/pharmacist confirmation instead of guessed.
- **Output**: `PrescriptionExplanation` (per drug: name, molecule, class, manufacturer, plain-language purpose, side_effects[], alternatives[], disclaimer) — delivered via web UI, WhatsApp, or Text-to-Speech.

## 5. Epidemiological Signal Agent

**Role**: Aggregates de-identified `PrescriptionExplanation` events (drug class + block-level geo + time) across many patients to detect early, localized disease-pattern spikes — e.g., a cluster of antipyretic + anti-emetic prescriptions in one block in a short window.

- **Inputs**: consented, de-identified prescription events (Cloud DLP-scrubbed before this agent ever sees them).
- **Tools**: BigQuery aggregation/query tool, a k-anonymity check tool (refuses to emit a signal for any cohort below a minimum size, to protect privacy at small geographies), a disease-pattern-matching tool (rule set mapping drug-class combinations to likely disease signals, e.g., "antipyretic + platelet test mention + NS1-relevant class → dengue-consistent pattern").
- **Reasoning**: statistical spike detection (rate-of-change vs. rolling baseline) plus pattern matching against known disease signatures; flags candidate outbreaks as *hypotheses for human public-health review*, never a confirmed diagnosis at population level.
- **Output**: `DiseaseSignal` (geo_block, disease_hypothesis, confidence, trend, contributing_case_count) — feeds both the Demand Forecast Agent (as a feature) and the Awareness Poster Agent (as a trigger).

## 6. Awareness Poster Agent

**Role**: When a `DiseaseSignal` crosses a threshold, auto-generates a localized public-awareness poster (e.g., dengue, viral fever, seasonal flu prevention) in the local language.

- **Inputs**: `DiseaseSignal`, target language/region, a fixed, health-authority-sourced fact template per disease (symptoms, prevention steps, when to seek care).
- **Tools**: Imagen 3 (image generation) tool for visual layout/graphics, Gemini for localized copywriting (using *only* the approved fact template as source — not free-generation of medical facts), Cloud Translation tool.
- **Guardrail**: the agent is explicitly restricted to rephrasing/localizing pre-approved fact sheets, not generating new medical claims — this prevents hallucinated health misinformation on a public-facing poster.
- **Output**: poster image (PDF/PNG) + short caption text, routed to ASHA workers and the relevant PHC's patient channel for printing/WhatsApp sharing.

---

## 7. Inter-Agent Data Contract (summary)

```
Prescription image ──▶ Prescription Explainer Agent ──▶ patient-facing explanation
                                     │
                                     ▼ (de-identified, consented)
                        Epidemiological Signal Agent ──▶ DiseaseSignal
                                     │                         │
                                     ▼                         ▼
                        Demand Forecast Agent          Awareness Poster Agent
                                     │
                                     ▼
                     Stock-out Early Warning Agent
                                     │
                                     ▼
                Redistribution Optimizer Agent ──▶ DHO approval queue
```

## 8. Why This Counts as "Meaningful Google AI Work" (Technical Execution criterion)

- Each agent has **distinct tools and a distinct reasoning job** — not one prompt reused six ways.
- The Orchestrator makes **genuine routing decisions** via Gemini function-calling, not a hardcoded if/else pipeline.
- Multimodal input (prescription images) is handled natively by Gemini/Document AI, not a separate bolt-on OCR service stitched together manually.
- Forecasting uses a real managed ML service (Vertex AI Forecasting/BigQuery ML), not a mocked number.
- Guardrails (fact-template restriction, k-anonymity checks, disclaimer injection) are built into the agent tool contracts themselves, showing responsible-AI design as part of the technical execution, not an afterthought.
