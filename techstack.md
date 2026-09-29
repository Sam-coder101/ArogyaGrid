# Tech Stack — ArogyaGrid

A consolidated reference of every technology used, why it was chosen, what it replaces/avoids, and which PRD feature or agent it powers. Built almost entirely on managed Google Cloud / Google AI services to maximize the "AI/Technical Execution" and "Deployability" judging criteria — minimal bespoke infrastructure, nothing a state IT cell has to operate.

---

## 1. AI / Agent Layer (Google AI Core)

| Technology | Purpose | Used By |
|---|---|---|
| **Gemini 2.x (via Vertex AI)** | Core reasoning model — multimodal (text + image), multilingual, function-calling for agent tool use | All 7 agents |
| **Vertex AI Agent Builder / Agent Development Kit (ADK)** | Multi-agent orchestration framework: shared session state, tool registration, agent-to-agent invocation | Orchestrator Agent; wires all specialist agents together |
| **Document AI** | Structured OCR for handwritten/printed prescriptions (drug name, dosage, doctor notes) | Prescription Explainer Agent |
| **Vertex AI Forecasting / BigQuery ML (ARIMA_PLUS, boosted trees)** | Managed time-series forecasting per PHC × drug | Demand Forecast Agent |
| **Imagen 3 (via Vertex AI)** | Text-to-image generation for localized awareness posters | Awareness Poster Agent |
| **Cloud Translation API** | Real-time translation across 22 scheduled Indian languages | Prescription Explainer Agent, Awareness Poster Agent |
| **Text-to-Speech API** | Voice output of prescription explanations for low-literacy patients | Prescription Explainer Agent (P1 feature) |
| **Cloud DLP (Data Loss Prevention)** | De-identifies/redacts patient identifiers before data crosses into aggregate signal pipeline | Epidemiological Signal Agent |

## 2. Data & Storage

| Technology | Purpose | Notes |
|---|---|---|
| **BigQuery** | State-level operational data warehouse (one dataset/project per state = the federation boundary); national aggregate warehouse | Region-pinned to `asia-south1`/`asia-south2` for data residency |
| **Firestore** | Real-time transactional store for live stock, bed, and staff-attendance state | Sub-second reads for the PHC app and Early Warning Agent |
| **Cloud Healthcare API (FHIR store)** | Standards-compliant clinical/administrative data model | Interoperability bridge to ABDM, e-Aushadhi, IHIP, HMIS |
| **Cloud SQL** *(optional, if a relational store is preferred over Firestore for structured reference data)* | Reference tables: `Medicine`, `PHC master`, drug-class taxonomy | Vetted-data source the Prescription Explainer Agent looks up instead of free-generating facts |

## 3. Messaging, Compute & Delivery

| Technology | Purpose | Notes |
|---|---|---|
| **Pub/Sub** | Event bus decoupling edge writes (PHC app) from downstream processing; buffers through connectivity gaps | Central to the offline-tolerant edge design |
| **Cloud Run** | Serverless hosting for the API gateway, PWA backend, and each agent's invocation endpoint | Scales to zero between sync bursts; zero infra ops for states |
| **Vertex AI Pipelines** | Schedules/orchestrates the state→national federated model aggregation jobs | The literal mechanism of "federated" in this architecture |
| **Vertex AI Model Registry** | Versions and distributes the aggregated national model back down to each state | Keeps state and national models in sync without moving raw data |
| **WhatsApp Business API (or Twilio) / Firebase Cloud Messaging** | Patient- and ASHA-facing delivery channel for explanations, alerts, and posters | Meets rural users on a channel they already use; no app install required |
| **Google Maps Platform (Distance Matrix/Directions)** | Real inter-PHC distance/route data | Redistribution Optimizer Agent's feasibility scoring |

## 4. Application & Presentation

| Technology | Purpose | Notes |
|---|---|---|
| **Progressive Web App (PWA)** | PHC pharmacist stock/bed/staff logging; works offline via local IndexedDB queue | No native app distribution needed across fragmented device landscape |
| **Looker Studio** (connected to BigQuery) | State/district/national dashboards for officers and ministry analysts | Free-tier, fast to stand up, familiar to government reporting workflows |
| **Firebase Hosting/Auth** | Hosts the patient/ASHA web UI; role-based auth for pharmacists, DHOs, state officers | Simple identity layer without a custom auth service |

## 5. Security, Privacy & Governance

| Technology | Purpose |
|---|---|
| **IAM (role-scoped per persona)** | Pharmacist writes only their PHC; DHO reads only their district; national analyst reads only approved aggregates |
| **VPC Service Controls** | Technically enforces the federation boundary — prevents raw data exfiltration between state and national projects, not just policy-level restriction |
| **Cloud DLP** | De-identification before any cross-boundary data movement |
| **Cloud Audit Logs** | Full traceability of every agent action (alert raised, redistribution suggested, poster generated) with input context and model version |

## 6. What We Deliberately Did *Not* Build Custom

| Instead of building... | We use... | Why |
|---|---|---|
| A custom OCR pipeline | Document AI | Purpose-built for structured document extraction, handles handwriting better than generic OCR |
| A custom multi-agent framework | Vertex AI Agent Builder / ADK | Managed session state, tool routing, and agent lifecycle out of the box |
| A custom forecasting model from scratch | BigQuery ML / Vertex AI Forecasting | Production-grade time-series models without training infra to maintain |
| A custom federated-learning framework | Vertex AI Pipelines + Model Registry | Achieves the same state-boundary + aggregation pattern using managed orchestration, deployable by a state IT cell in weeks, not months |
| A bespoke image-generation service | Imagen 3 | Directly available inside the same Vertex AI project as every other agent — one platform, one IAM boundary |

## 7. Hackathon Demo Footprint vs. Production Target

| | Hackathon Demo | Production Target |
|---|---|---|
| States | 2–3 simulated | All 28 states + UTs, each own GCP project |
| Data | Synthetic, schema-matched to ABDM/e-Aushadhi | Live batch export, then real-time Pub/Sub feed |
| Federated aggregation | Single simulated aggregation run | Scheduled nightly Vertex AI Pipelines job per state |
| Delivery channel | Web UI | Web UI + WhatsApp/SMS + voice (Text-to-Speech) |
| Hosting | Single Cloud Run service set | Per-state Cloud Run deployments behind one national API gateway |

This stack is intentionally 100% Google Cloud / Google AI end-to-end — every judging criterion tied to "Google AI doing meaningful work" is satisfied by the agent layer (Gemini, ADK, Document AI, Vertex AI Forecasting, Imagen), while every "deployable within weeks" claim is backed by the fact that nothing here requires custom infrastructure a ministry or state IT cell would need to build or operate.
