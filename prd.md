# PRD — ArogyaGrid
### A Federated AI Platform for National PHC Resource Intelligence & Patient Medicine Literacy
**GDG India Hackathon Submission | Version 1.0**

---

## 1. Problem Statement

India runs ~1.6 lakh Primary Health Centres (PHCs) and Sub-Centres, most reporting stock, bed, and staffing data manually, at weekly/monthly intervals, into disconnected state-level systems (HMIS, IHIP, e-Aushadhi). The result:

- **Stock-outs discovered too late** — by the time a district office sees a shortage, the PHC has already turned patients away.
- **No cross-district visibility** — a surplus of a medicine in District A and a shortage in District B (30 km away) can coexist for weeks, undetected.
- **No demand forecasting** — seasonal disease spikes (dengue, viral fever, flu) are not anticipated at the PHC level, so restocking is reactive, not predictive.
- **Patients are blind to their own treatment** — most PHC/rural patients receive a handwritten or printed prescription with zero context: what the medicine is, why *this* drug over an alternative, what side effects to expect, or how it connects to a wider outbreak in their area. This also means the health system loses a rich, real-time signal — prescription patterns — that could otherwise feed outbreak detection.

## 2. Solution Summary

ArogyaGrid is a **federated, multi-agent AI platform** with two tightly connected halves:

1. **Supply Chain Intelligence Layer** — near real-time visibility of medicine stock, bed occupancy, and staff attendance across every PHC, feeding demand forecasting, stock-out early warning, and automated cross-district redistribution recommendations. "Federated" here is architectural, not a buzzword: each state keeps its operational data in its own Google Cloud project/data boundary; only model weights/gradients and aggregated signals move to the national layer, respecting state data-sovereignty norms and the DPDP Act, 2023.
2. **Patient-Facing Prescription Intelligence Layer** — a multi-agent assistant that reads a prescription (photo/scan), and in the patient's own language explains: what the medicine is, its molecule/composition, manufacturer, why the doctor likely chose it, plausible alternatives, and side effects to watch for — in plain, non-alarming language, always paired with a "consult your doctor/pharmacist" guardrail. Anonymized, aggregated patterns from this layer (drug class × geography × time) become an **early epidemiological signal** feeding back into the forecasting layer, and automatically power localized disease-awareness posters (e.g., a dengue-prevention poster auto-triggered when antipyretic + platelet-test prescriptions spike in a block).

This closes the loop: **patients get clarity → the system gets a real-time signal → the signal improves forecasting and redistribution → the next patient is less likely to face a stock-out.**

## 3. Goals & Non-Goals

### Goals (Hackathon MVP)
- Demonstrate the full loop end-to-end on a seeded synthetic dataset for 2–3 states, several districts, and a realistic PHC medicine catalog.
- Show a working multi-agent pipeline built on Google AI (Gemini, ADK, Vertex AI) doing genuinely agentic reasoning — not a single prompt wrapper.
- Demonstrate the federated design pattern (even if simulated with 2 state "nodes" for the demo) — data isolation + central aggregation.
- Produce a forecast + a stock-out alert + a redistribution recommendation + a prescription explanation + an auto-generated awareness poster, all in one demo run.

### Non-Goals (explicitly out of scope for hackathon build)
- Replacing clinical decision-making or issuing prescriptions — the platform is informational, never diagnostic or prescriptive.
- Real integration with live government systems (ABDM, e-Aushadhi, IHIP) — we design the integration contract but demo against synthetic/mocked data.
- Full 28-state rollout — we design for it (see Depth & Reach) but demo 2–3 states.
- Payments, procurement/vendor management, or legal medicine e-commerce.

## 4. Personas

| Persona | Need |
|---|---|
| **PHC Pharmacist / Store Clerk** | Log stock in seconds via phone; get warned before running out |
| **Medical Officer at PHC** | See bed/staff status of self and nearby PHCs |
| **District Health Officer (DHO)** | District-wide dashboard; approve redistribution suggestions |
| **State Nodal Officer** | State-wide forecast, cross-district balancing, outbreak heatmap |
| **Ministry / National Health Mission analyst** | Cross-state (federated) aggregate view, national early-warning feed |
| **Patient / caregiver (rural, low health-literacy)** | Understand a prescription in their own language, in simple terms |
| **ASHA / Community Health Worker** | Distribute/display localized outbreak-awareness posters, help patients use the assistant |

## 5. Core User Stories

1. As a **pharmacist**, I scan/log dispensed stock via a lightweight PWA so central systems see near-real-time depletion.
2. As a **DHO**, I get an automatic alert 10–14 days before a PHC is projected to run out of an essential medicine, with a suggested source PHC/district to redistribute from.
3. As a **state officer**, I see a forecast of medicine demand for the next 2–4 weeks, adjusted for seasonal disease trends (e.g., monsoon → dengue → antipyretics + platelet kits).
4. As a **patient**, I photograph my prescription and receive, in Hindi/Bengali/Tamil/etc., a simple explanation of each medicine, its side effects, and why it was likely prescribed — with a clear "this does not replace your doctor" disclaimer.
5. As an **ASHA worker**, when prescription-signal data shows a localized spike consistent with dengue/viral fever, I receive an auto-generated, locally-worded awareness poster (PDF/image) I can print or share on WhatsApp.
6. As a **Ministry analyst**, I view a national dashboard built from federated aggregates — no state's raw operational data leaves its boundary, only model contributions and approved aggregate statistics.

## 6. Feature List (MVP scope, prioritized)

**P0 — must demo**
- PHC stock/bed/staff logging (mock PWA + seeded dataset)
- Demand Forecasting Agent (per medicine, per PHC/district)
- Stock-out Early Warning Agent + alert feed
- Cross-District Redistribution Recommendation Agent
- Prescription Reader & Explainer Agent (multimodal OCR → structured explanation)
- Disease Awareness Poster Generation Agent (Imagen-based, localized)
- Orchestrator tying all agents together with a shared context/state store
- Admin dashboard (state/district/national views)

**P1 — nice to demo if time allows**
- WhatsApp/SMS delivery channel for patients and ASHA workers (low-smartphone-penetration friendly)
- Multi-language voice output (Text-to-Speech) for low-literacy users
- Simulated 2-state federated training run showing model aggregation without raw data movement

**P2 — roadmap, described but not built**
- Real ABDM/e-Aushadhi/IHIP integration
- IoT/RFID-based automatic stock sensing
- Full 28-state, district-level rollout with per-state Google Cloud projects

## 7. Success Metrics

| Metric | Target signal for demo |
|---|---|
| Forecast usefulness | Forecast tracks a seeded seasonal spike within a visible margin |
| Early-warning lead time | Alert fires ≥ 7–14 simulated days before simulated stock-out |
| Redistribution relevance | Suggested source PHC has genuine surplus of the exact SKU needed |
| Prescription explanation clarity | Explanation includes molecule, class, side effects, alternative, "why this drug," in ≤ 8th-grade reading level, in a regional language |
| Poster relevance | Poster topic matches the actual disease signal that triggered it (e.g., dengue signal → dengue poster, not generic) |
| Agentic depth | Each agent has distinct tools/reasoning and the orchestrator makes routing decisions — not a single hardcoded pipeline |

## 8. Mapping to Judging Criteria

| Criterion | Weight | How ArogyaGrid addresses it |
|---|---|---|
| Problem–Solution Fit | 20% | Directly targets the four named pain points: stock/bed/personnel visibility, forecasting, early warning, cross-district redistribution |
| AI/Technical Execution | 25% | Multi-agent system on Gemini + Vertex AI Agent Builder/ADK, Vertex AI Forecasting, Document AI, Imagen — each agent does distinct, visible reasoning; end-to-end working demo |
| Depth & Reach Across India | 20% | Federated-by-design architecture (per-state data boundary + central model aggregation), multilingual via Cloud Translation, built on interoperable FHIR-ready data model to plug into ABDM |
| Impact Potential | 15% | Reduces stock-outs at PHC scale (potential reach: 1.6L+ PHCs, hundreds of millions of rural patients); patient literacy layer improves treatment adherence and enables outbreak detection from everyday prescriptions |
| Deployability & Scalability | 20% | Built entirely on managed Google Cloud services (serverless/Cloud Run, BigQuery, Vertex AI) — no bespoke infra; state onboarding = provisioning a new Cloud project + connecting existing HMIS export, pilotable within weeks |

## 9. Risks & Guardrails

- **Medical safety**: the Prescription Explainer never diagnoses, never recommends dosage changes, and always appends "This is educational information, not medical advice — consult your doctor or pharmacist." Alternative-medicine suggestions are informational only, sourced from a vetted drug database, and flagged as "ask your doctor about this option," never a direct substitution instruction.
- **Data privacy**: patient prescription data is processed for the explanation session and, only with consent, contributes de-identified, aggregated (drug-class + geography + time-bucket) signals to the forecasting layer — never raw patient identity.
- **Federation integrity**: states retain operational data ownership; only model artifacts/aggregates cross the boundary, mirroring how National Health Stack federation is expected to work.
- **Poster misinformation risk**: poster content is generated from a vetted disease-fact template + Gemini phrasing, not free-form generation, and is reviewed against a fixed fact-sheet per disease before rendering.

## 10. Assumptions
- "Federated" is implemented for the hackathon as an architectural pattern demonstrated across 2 simulated state nodes, given time constraints — full federated learning infrastructure across 28 states is described in `architecture.md` as the production target, not built live.
- Real prescription/medicine data is unavailable for a hackathon; a synthetic but realistic dataset (drug names, molecules, PHC stock levels) is used, structured to be a drop-in replacement for real ABDM/e-Aushadhi feeds.
