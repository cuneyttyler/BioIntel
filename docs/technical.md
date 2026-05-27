# Technical Blueprint — BioIntel Drug Development AI Assistant

## Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | Vue 3, Vite, Vue Router 4, Pinia, Axios |
| **Backend** | Django 5, Django REST Framework |
| **Database** | SQLite (development) → PostgreSQL (production) |
| **AI** | Claude API (Anthropic) — claude-sonnet-4-6 |
| **Caching** | `external_data_cache` DB table (dev) → Redis (production) |
| **Package management** | pip + venv (backend), npm (frontend) |

---

## Application Overview

BioIntel is an AI-powered assistant for drug development scientists that accelerates decisions across the full pre-clinical and development pipeline. A scientist starts by opening or creating a **project** tied to a specific compound and development phase. They define a process objective — such as a scalable synthesis route, a stable formulation, or a validated analytical method — and the application captures all relevant context: compound properties, prior experimental outcomes, formulation history, and regulatory constraints. BioIntel then integrates live data from public databases (ChEMBL, PubChem, Open Targets, UniProt, EPA CompTox, ClinicalTrials.gov, PubMed, OpenFDA, DailyMed, NIST, ASKCOS, and pkCSM) to populate a risk heat map, surface relevant literature, and propose concrete next-step experiments. Scientists design and log experiments within the app, and after results are available, a Claude-powered AI assistant interprets findings, suggests process refinements, and generates regulatory-ready process summaries. The entire workflow — from objective definition through experimentation, risk analysis, synthesis planning, literature review, and documentation — is accessible through a single integrated web interface, reducing context switching and accelerating time-to-decision.

---

## Database Schema

All tables are managed by Django ORM migrations. JSON fields use `django.db.models.JSONField`.

### `projects`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto |
| name | VARCHAR(255) | |
| description | TEXT | |
| phase | VARCHAR(20) | preclinical / phase1 / phase2 / phase3 |
| status | VARCHAR(20) | active / on_hold / completed / archived |
| created_at | DATETIME | auto_now_add |
| updated_at | DATETIME | auto_now |

### `compounds`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | |
| name | VARCHAR(255) | Common/IUPAC name |
| chembl_id | VARCHAR(20) | e.g. CHEMBL25 |
| pubchem_cid | INTEGER | |
| smiles | TEXT | Isomeric SMILES |
| inchi_key | VARCHAR(27) | |
| molecular_formula | VARCHAR(100) | |
| molecular_weight | FLOAT | Da |
| created_at | DATETIME | auto_now_add |

### `compound_properties`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| compound_id | INTEGER FK → compounds | |
| property_type | VARCHAR(30) | physicochemical / admet / toxicity |
| source | VARCHAR(30) | pubchem / pkcsm / comptox / chembl |
| data | JSON | Full API response subset |
| fetched_at | DATETIME | |

### `experiments`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | |
| compound_id | INTEGER FK → compounds | nullable |
| title | VARCHAR(255) | |
| experiment_type | VARCHAR(30) | formulation / synthesis / analytical / stability |
| objective | TEXT | |
| variables | JSON | `[{"name": "pH", "range": [4, 7], "unit": ""}]` |
| success_criteria | TEXT | |
| status | VARCHAR(20) | planned / in_progress / completed / failed |
| created_at | DATETIME | auto_now_add |

### `experiment_results`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| experiment_id | INTEGER FK → experiments | |
| result_data | JSON | Key metrics and observations |
| interpretation | TEXT | AI or scientist-written |
| decision | VARCHAR(20) | optimize / scale / transition / abort |
| recorded_at | DATETIME | auto_now_add |
| notes | TEXT | |

### `risk_assessments`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | |
| risk_factors | JSON | `[{"category": "scale-up", "level": "high", "rationale": "..."}]` |
| risk_heat_map | JSON | 2D matrix data for rendering |
| created_at | DATETIME | auto_now_add |
| updated_at | DATETIME | auto_now |

### `documents`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | |
| doc_type | VARCHAR(30) | process_summary / risk_report / handoff |
| title | VARCHAR(255) | |
| content | TEXT | Markdown |
| created_at | DATETIME | auto_now_add |

### `chat_sessions`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | nullable (global session) |
| title | VARCHAR(255) | |
| created_at | DATETIME | auto_now_add |
| updated_at | DATETIME | auto_now |

### `chat_messages`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| session_id | INTEGER FK → chat_sessions | |
| role | VARCHAR(10) | user / assistant |
| content | TEXT | |
| sources | JSON | `[{"api": "pubmed", "url": "...", "title": "..."}]` |
| created_at | DATETIME | auto_now_add |

### `external_data_cache`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| source | VARCHAR(30) | chembl / pubchem / opentargets / pkcsm / comptox / uniprot / dailymed / clinicaltrials / pubmed / openfda / nist / askcos |
| query_key | VARCHAR(512) | Hash of endpoint + params |
| response_data | JSON | |
| fetched_at | DATETIME | |
| expires_at | DATETIME | TTL-based invalidation |

---

## App Pages

---

### 1. Dashboard

**Description:** The landing page after login. Displays all active projects as cards with phase and status badges, a recent-experiments feed, a pending AI recommendations queue, and quick-action buttons to create a new project or start a chat session. Gives scientists a high-level view of their portfolio and surfaces any items needing attention.

**External APIs used:** None (all data is local)

**Vue Components:**
- `DashboardPage` (page root)
- `ProjectCard` — project name, phase badge, status, compound count, link to project
- `RecentActivityFeed` — chronological list of recent experiments and results across all projects
- `QuickActionPanel` — CTA buttons: New Project, Open Chat, New Experiment
- `StatsBadge` — numeric chip (e.g. "3 active projects", "12 experiments this week")

**Backend APIs:**
- `GET /api/projects/` — list all projects with summary stats
- `GET /api/experiments/recent/` — last 10 experiments across all projects

**Database Tables:** `projects`, `experiments`

---

### 2. Project Setup

**Description:** A wizard-style page for creating or editing a project. The scientist enters the project name, selects the development phase, and writes a high-level process objective. They also search for and attach the target compound, pulling its identity data from PubChem or ChEMBL. Existing projects can be edited from this page.

**External APIs used:**
- **PubChem PUG REST** — compound name → CID lookup and identity data
- **ChEMBL REST** — compound details by ChEMBL ID, mechanism of action, approval status

**Vue Components:**
- `ProjectSetupPage` (page root)
- `ProjectForm` — name, description, phase selector, status selector
- `CompoundSearch` — debounced search input that queries PubChem; shows name, formula, CID
- `CompoundPreviewCard` — shows selected compound: SMILES, MW, formula, InChI key
- `ObjectiveWizard` — guided textarea with phase-specific prompts for the process objective

**Backend APIs:**
- `POST /api/projects/` — create project
- `PUT /api/projects/{id}/` — update project
- `GET /api/compounds/search/?q={name}` — proxy to PubChem + ChEMBL, returns compound identity
- `POST /api/compounds/` — save compound record to project

**Database Tables:** `projects`, `compounds`

---

### 3. Compound Profile

**Description:** A detailed read-only view of a single compound. Displays the 2D structure image, physicochemical properties (MW, LogP, TPSA, HBD/HBA), ADMET predictions, safety/toxicity endpoints, pharmacological targets, and known drug status. Data is fetched from multiple external APIs and cached locally. The scientist can trigger a refresh of cached property data.

**External APIs used:**
- **PubChem PUG REST** — 2D structure PNG, SMILES, molecular properties (MolecularWeight, XLogP, TPSA)
- **pkCSM REST** — ADMET profile from SMILES (solubility, Caco-2, BBB, CYP, hERG, AMES, hepatotoxicity)
- **EPA CompTox Dashboard** — experimental + predicted toxicity endpoints, Tox21/ToxCast bioassay summary
- **ChEMBL REST** — mechanism of action, approval status, bioactivity data
- **UniProt REST** — protein targets linked from ChEMBL: function, disease association, tissue expression

**Vue Components:**
- `CompoundProfilePage` (page root)
- `CompoundHeader` — name, ChEMBL ID, PubChem CID, approval badge
- `MoleculeViewer` — renders 2D structure PNG from PubChem
- `PropertyTable` — key physicochemical values in a two-column table
- `ADMETCard` — color-coded ADMET profile (green/yellow/red per endpoint)
- `SafetyPanel` — toxicity flags from EPA CompTox; Tox21 active assay count
- `TargetList` — table of pharmacological targets with UniProt links
- `SimilarCompoundsList` — CIDs from PubChem fastsimilarity, shown as mini cards

**Backend APIs:**
- `GET /api/compounds/{id}/` — compound record from DB
- `GET /api/compounds/{id}/properties/` — physicochemical props (PubChem, cached)
- `GET /api/compounds/{id}/admet/` — ADMET profile (pkCSM, cached)
- `GET /api/compounds/{id}/safety/` — toxicity data (EPA CompTox, cached)
- `GET /api/compounds/{id}/targets/` — pharmacological targets (ChEMBL + UniProt, cached)
- `GET /api/compounds/{id}/structure/` — proxied PNG from PubChem
- `GET /api/compounds/{id}/similar/` — similar compound CIDs (PubChem)

**Database Tables:** `compounds`, `compound_properties`, `external_data_cache`

---

### 4. Disease & Target Explorer

**Description:** A search and browse page for diseases and their associated drug targets. Scientists can search for a disease by name (e.g. "type 2 diabetes"), see a ranked list of associated protein targets with evidence scores, and view the known drugs in clinical development for that indication. Selecting a target shows a UniProt-sourced protein card with function, tissue expression, and links to PDB structures.

**External APIs used:**
- **Open Targets Platform GraphQL** — disease summary, target–disease associations with scores, known drugs per indication
- **UniProt REST** — protein function, disease associations, tissue specificity, PDB/ChEMBL cross-references

**Vue Components:**
- `DiseaseExplorerPage` (page root)
- `DiseaseSearch` — autocomplete search input; queries Open Targets
- `DiseaseOverviewCard` — disease name, EFO ID, description from Open Targets
- `TargetAssociationTable` — ranked target list with score bars and gene symbols
- `KnownDrugsTable` — drugs in clinical development for the disease: name, phase, status
- `TargetDetailCard` — slide-in panel: UniProt accession, function, disease links, tissue expression, PDB count

**Backend APIs:**
- `GET /api/diseases/search/?q={term}` — Open Targets disease search (cached)
- `GET /api/diseases/{efo_id}/targets/` — associated targets with scores (Open Targets, cached)
- `GET /api/diseases/{efo_id}/drugs/` — known drugs for indication (Open Targets, cached)
- `GET /api/targets/{uniprot_id}/` — protein detail (UniProt, cached)

**Database Tables:** `external_data_cache`

---

### 5. Experiment Planner

**Description:** A structured form for designing a new experiment. The scientist selects the experiment type (formulation, synthesis, analytical, stability), states the objective, defines the variable parameters with ranges and units, sets success criteria, and links the experiment to a project and optional compound. For synthesis experiments, a retrosynthesis preview from ASKCOS is shown inline.

**External APIs used:**
- **ASKCOS REST** — single-step retrosynthesis preview for synthesis-type experiments
- **OpenFDA REST** — inactive ingredient lookup for formulation-type experiments (excipient suggestions)

**Vue Components:**
- `ExperimentPlannerPage` (page root)
- `ExperimentForm` — type selector, objective textarea, project/compound pickers
- `VariableBuilder` — dynamic row list: variable name, unit, range (min/max), control value
- `SuccessCriteriaPanel` — free-text and guided structured criteria input
- `RetrosynPreview` — compact tree showing top ASKCOS precursor candidates (synthesis experiments only)
- `ExcipientSuggestion` — list of common inactive ingredients matching the dosage form (formulation only)

**Backend APIs:**
- `POST /api/experiments/` — create experiment record
- `GET /api/experiments/{id}/` — retrieve experiment
- `PUT /api/experiments/{id}/` — update experiment
- `POST /api/synthesis/retro/` — single-step retrosynthesis (ASKCOS, cached)
- `GET /api/regulatory/excipients/?form={dosage_form}` — inactive ingredient list (OpenFDA)

**Database Tables:** `experiments`, `external_data_cache`

---

### 6. Experiment Results

**Description:** A data-entry and review page for logging results against a planned experiment. Scientists enter key metric values, observations, and anomalies. On submission, the Claude AI generates an interpretation comparing results to success criteria and recommends a decision: optimize further, reproduce, scale up, or abort. Historical results for the same experiment are shown in a timeline with trend charts.

**External APIs used:**
- **Claude API** — AI interpretation of results in the context of the experiment objective and success criteria

**Vue Components:**
- `ExperimentResultsPage` (page root)
- `ResultsForm` — dynamic fields matching the experiment's variables + free-text observations
- `AIInterpretation` — streamed Claude response shown below submitted results
- `DecisionPanel` — four-button decision selector: Optimize / Reproduce / Scale / Abort
- `ResultsTimeline` — chronological list of prior result submissions for this experiment
- `ResultsChart` — line or bar chart of key metric values across submissions

**Backend APIs:**
- `GET /api/experiments/{id}/` — experiment metadata and success criteria
- `GET /api/experiments/{id}/results/` — all results for this experiment
- `POST /api/experiments/{id}/results/` — log a new result set
- `POST /api/experiments/{id}/interpret/` — trigger Claude AI interpretation

**Database Tables:** `experiments`, `experiment_results`

---

### 7. Risk Analysis

**Description:** A project-level risk dashboard. Displays a 2D risk heat map (probability vs. impact) with color-coded risk factors such as reagent availability, scale-up feasibility, regulatory expectations, and batch variability. Risk assessments can be generated automatically by the AI (which pulls context from compound properties, clinical precedent, and regulatory guidance) or edited manually by the scientist.

**External APIs used:**
- **ClinicalTrials.gov API v2** — clinical precedent for the compound/indication (similar compound trial history)
- **PubMed E-utilities** — safety and scale-up literature for the compound
- **FDA Guidance Documents (OpenFDA)** — relevant process validation and CMC guidances
- **Claude API** — AI-generated risk factor list and heat map from project context

**Vue Components:**
- `RiskAnalysisPage` (page root)
- `RiskHeatMap` — SVG/Canvas 5×5 probability–impact grid with draggable risk markers
- `RiskFactorList` — editable list of risk factors with category, level (low/medium/high/critical), and rationale
- `RegulatorySummary` — matched FDA guidance documents with title and PDF link
- `ClinicalPrecedentCard` — count and phase breakdown of clinical trials for the indication
- `GenerateRiskBtn` — triggers AI risk assessment generation

**Backend APIs:**
- `GET /api/projects/{id}/risk-assessment/` — current risk assessment
- `POST /api/projects/{id}/risk-assessment/` — save manual assessment
- `POST /api/projects/{id}/risk-assessment/generate/` — AI-generated assessment (Claude)
- `GET /api/trials/search/?condition={cond}&intervention={drug}` — clinical precedent (ClinicalTrials.gov)
- `GET /api/literature/search/?q={query}` — safety literature (PubMed)
- `GET /api/regulatory/guidance/?q={topic}` — FDA guidance docs (OpenFDA)

**Database Tables:** `risk_assessments`, `projects`, `compounds`, `external_data_cache`

---

### 8. Synthesis Planning

**Description:** A dedicated page for computer-aided synthesis planning. The scientist enters a target SMILES and can run single-step or multi-step retrosynthesis (ASKCOS), forward reaction prediction, and reaction condition recommendations. Results are shown as an interactive retrosynthesis tree. Leaf nodes can be checked for commercial availability. Spectroscopic reference data (IR, MS) for known compounds can be fetched from NIST WebBook.

**External APIs used:**
- **ASKCOS REST** — single-step retrosynthesis, multi-step tree builder, forward prediction, condition recommendation, buyability check
- **NIST WebBook** — IR/MS reference spectra for starting materials and intermediates
- **Open Reaction Database (ORD)** — reaction precedents via BigQuery (batch, not live query; presented as pre-indexed suggestions)

**Vue Components:**
- `SynthesisPlanningPage` (page root)
- `SynthesisInput` — SMILES text input with structure validation indicator
- `RetrosynTree` — interactive D3 or Canvas tree of precursor nodes and reaction arrows
- `ReactionStepCard` — single retrosynthesis step: reactants, reagents, conditions, confidence score
- `ForwardPredictionPanel` — input reactants SMILES, show predicted product with probability
- `ConditionRecommender` — solvent, reagent, temperature suggestions for a given reaction
- `BuyableCheck` — badge per leaf node showing commercial availability status
- `SpectraViewer` — NIST IR/MS spectrum plot (JCAMP-DX parsed client-side)

**Backend APIs:**
- `POST /api/synthesis/retro/` — single-step retrosynthesis (ASKCOS)
- `POST /api/synthesis/tree/` — multi-step tree (ASKCOS)
- `POST /api/synthesis/forward/` — forward prediction (ASKCOS)
- `POST /api/synthesis/conditions/` — reaction condition recommendation (ASKCOS)
- `GET /api/synthesis/buyables/?smiles={smiles}` — buyability check (ASKCOS)
- `GET /api/compounds/spectra/?cas={cas}&type={ir|ms}` — spectral data (NIST WebBook)

**Database Tables:** `external_data_cache`

---

### 9. Literature & Clinical Trials

**Description:** A unified search page for biomedical literature and clinical trial data. Scientists can search PubMed for articles relevant to a compound, target, or process topic and view article abstracts and metadata. A second tab allows searching ClinicalTrials.gov by condition and intervention, showing trial phase, status, enrollment, and outcome summaries. Results can be saved as project references.

**External APIs used:**
- **PubMed E-utilities (NCBI)** — ESearch for PMIDs, EFetch for abstracts, ESummary for metadata
- **ClinicalTrials.gov API v2** — search by condition + intervention, study detail by NCT ID, phase/status filters

**Vue Components:**
- `LiteraturePage` (page root)
- `LiteratureSearch` — query input with PubMed-style field selectors (title, abstract, author)
- `ArticleCard` — title, authors, journal, date, abstract excerpt, PubMed link
- `TrialSearch` — condition + intervention inputs with phase and status filter dropdowns
- `TrialCard` — NCT ID, title, phase, status, enrollment count, primary outcome
- `FilterPanel` — shared faceted filter sidebar (date range, phase, study type)
- `SaveReferenceBtn` — saves article/trial as a note linked to the current project

**Backend APIs:**
- `GET /api/literature/search/?q={query}&max={n}` — PubMed ESearch + ESummary (cached)
- `GET /api/literature/{pmid}/` — PubMed EFetch abstract (cached)
- `GET /api/trials/search/?condition={cond}&intervention={drug}&phase={p}` — ClinicalTrials.gov search (cached)
- `GET /api/trials/{nct_id}/` — trial detail (ClinicalTrials.gov, cached)

**Database Tables:** `external_data_cache`

---

### 10. AI Chat Assistant

**Description:** A persistent, context-aware chat interface where scientists can ask questions about their compound, experiment history, regulatory requirements, or any drug development topic. The assistant is backed by Claude and has access (via function calling) to all integrated external APIs. Every AI response cites the data sources it used. Chat sessions are saved per project and can be resumed at any time.

**External APIs used:**
- **Claude API** — multi-turn conversation with tool use for all integrated APIs
- **All 13 external APIs** — invoked dynamically by Claude as tool calls (PubChem, ChEMBL, Open Targets, UniProt, pkCSM, EPA CompTox, OpenFDA, DailyMed, ASKCOS, NIST, ClinicalTrials.gov, PubMed, FDA Guidance)

**Vue Components:**
- `ChatPage` (page root)
- `SessionList` — sidebar list of saved sessions for the current project
- `ChatInterface` — scrollable message history + input box
- `MessageBubble` — user or assistant message with role indicator and timestamp
- `SourceCitation` — collapsible list of API sources cited in an assistant message
- `MarkdownRenderer` — renders Claude's markdown-formatted responses
- `SuggestedQueries` — clickable example questions shown on empty session
- `StreamingIndicator` — animated typing indicator while Claude is responding

**Backend APIs:**
- `GET /api/chat/sessions/` — list sessions (optionally filtered by project)
- `POST /api/chat/sessions/` — create a new session
- `GET /api/chat/sessions/{id}/` — get session with full message history
- `POST /api/chat/sessions/{id}/messages/` — send user message; streams Claude response with tool calls
- `DELETE /api/chat/sessions/{id}/` — delete session

**Database Tables:** `chat_sessions`, `chat_messages`, `external_data_cache`

---

### 11. Process Documentation

**Description:** A document generation and editing page for producing regulatory-ready process summaries, risk reports, and development handoff notes. The scientist selects a document type, and the AI pre-populates a structured Markdown draft using data from the project's experiments, risk assessment, and compound profile. The scientist can edit inline before exporting as PDF or DOCX.

**External APIs used:**
- **Claude API** — document drafting from project context
- **DailyMed REST** — authoritative drug labeling language for the indication or compound (referenced in regulatory sections)
- **FDA Guidance Documents (OpenFDA)** — cited ICH/CMC guidance sections included in the document

**Vue Components:**
- `DocumentationPage` (page root)
- `DocumentList` — list of saved documents for the project with type badge and date
- `DocumentEditor` — rich Markdown editor (e.g. CodeMirror or ProseMirror) for inline editing
- `SectionBuilder` — collapsible section panels: Process Rationale, Decision Points, Risk Summary, Next Milestones
- `GenerateDocBtn` — triggers AI draft generation for the selected document type
- `ExportPanel` — export as PDF or DOCX; format selector and download button

**Backend APIs:**
- `GET /api/projects/{id}/documents/` — list documents for a project
- `POST /api/projects/{id}/documents/generate/` — AI-generated draft (Claude)
- `POST /api/projects/{id}/documents/` — save a manually created document
- `GET /api/documents/{id}/` — retrieve a document
- `PUT /api/documents/{id}/` — update document content
- `POST /api/documents/{id}/export/` — render and return PDF or DOCX
- `GET /api/regulatory/labels/?drug={name}` — drug labeling reference (DailyMed)
- `GET /api/regulatory/guidance/?q={topic}` — FDA guidance citations (OpenFDA)

**Database Tables:** `documents`, `projects`, `experiments`, `risk_assessments`, `external_data_cache`

---

## Backend API List

### Authentication
| Method | Endpoint | Description | DB Tables | External APIs |
|---|---|---|---|---|
| POST | `/api/auth/login/` | Obtain session token | — | — |
| POST | `/api/auth/logout/` | Invalidate session | — | — |
| GET | `/api/auth/me/` | Current user info | — | — |

### Projects
| Method | Endpoint | Description | DB Tables | External APIs |
|---|---|---|---|---|
| GET | `/api/projects/` | List all projects with stats | projects, experiments | — |
| POST | `/api/projects/` | Create new project | projects | — |
| GET | `/api/projects/{id}/` | Project detail | projects | — |
| PUT | `/api/projects/{id}/` | Update project | projects | — |
| DELETE | `/api/projects/{id}/` | Delete project and related data | projects, compounds, experiments, … | — |

### Compounds
| Method | Endpoint | Description | DB Tables | External APIs |
|---|---|---|---|---|
| GET | `/api/compounds/search/?q={name}` | Search compound by name | external_data_cache | PubChem, ChEMBL |
| POST | `/api/compounds/` | Save compound to project | compounds | — |
| GET | `/api/compounds/{id}/` | Compound record | compounds | — |
| GET | `/api/compounds/{id}/properties/` | Physicochemical properties | compound_properties, external_data_cache | PubChem |
| GET | `/api/compounds/{id}/admet/` | ADMET profile | compound_properties, external_data_cache | pkCSM |
| GET | `/api/compounds/{id}/safety/` | Toxicity/hazard data | compound_properties, external_data_cache | EPA CompTox |
| GET | `/api/compounds/{id}/targets/` | Pharmacological targets | external_data_cache | ChEMBL, UniProt |
| GET | `/api/compounds/{id}/structure/` | 2D structure PNG (proxy) | external_data_cache | PubChem |
| GET | `/api/compounds/{id}/similar/` | Fingerprint-similar CIDs | external_data_cache | PubChem |
| GET | `/api/compounds/spectra/?cas={cas}&type={type}` | IR/MS spectra (JCAMP-DX) | external_data_cache | NIST WebBook |

### Diseases & Targets
| Method | Endpoint | Description | DB Tables | External APIs |
|---|---|---|---|---|
| GET | `/api/diseases/search/?q={term}` | Disease search | external_data_cache | Open Targets |
| GET | `/api/diseases/{efo_id}/targets/` | Associated targets | external_data_cache | Open Targets |
| GET | `/api/diseases/{efo_id}/drugs/` | Known drugs for indication | external_data_cache | Open Targets |
| GET | `/api/targets/{uniprot_id}/` | Protein/target detail | external_data_cache | UniProt |

### Experiments
| Method | Endpoint | Description | DB Tables | External APIs |
|---|---|---|---|---|
| GET | `/api/experiments/recent/` | Last 10 experiments (all projects) | experiments | — |
| POST | `/api/experiments/` | Create experiment | experiments | — |
| GET | `/api/experiments/{id}/` | Experiment detail | experiments | — |
| PUT | `/api/experiments/{id}/` | Update experiment | experiments | — |
| GET | `/api/experiments/{id}/results/` | All results for experiment | experiment_results | — |
| POST | `/api/experiments/{id}/results/` | Log a result set | experiment_results | — |
| POST | `/api/experiments/{id}/interpret/` | AI interpretation of latest results | experiment_results | Claude API |

### Risk Assessment
| Method | Endpoint | Description | DB Tables | External APIs |
|---|---|---|---|---|
| GET | `/api/projects/{id}/risk-assessment/` | Current risk assessment | risk_assessments | — |
| POST | `/api/projects/{id}/risk-assessment/` | Save manual assessment | risk_assessments | — |
| POST | `/api/projects/{id}/risk-assessment/generate/` | AI-generated risk assessment | risk_assessments, compounds, experiments | Claude API, ClinicalTrials.gov, PubMed, OpenFDA |

### Synthesis Planning
| Method | Endpoint | Description | DB Tables | External APIs |
|---|---|---|---|---|
| POST | `/api/synthesis/retro/` | Single-step retrosynthesis | external_data_cache | ASKCOS |
| POST | `/api/synthesis/tree/` | Multi-step retrosynthesis tree | external_data_cache | ASKCOS |
| POST | `/api/synthesis/forward/` | Forward reaction prediction | external_data_cache | ASKCOS |
| POST | `/api/synthesis/conditions/` | Reaction condition recommendation | external_data_cache | ASKCOS |
| GET | `/api/synthesis/buyables/?smiles={smiles}` | Commercial availability check | external_data_cache | ASKCOS |

### Literature & Clinical Trials
| Method | Endpoint | Description | DB Tables | External APIs |
|---|---|---|---|---|
| GET | `/api/literature/search/?q={query}&max={n}` | PubMed article search | external_data_cache | PubMed E-utilities |
| GET | `/api/literature/{pmid}/` | Article abstract + metadata | external_data_cache | PubMed E-utilities |
| GET | `/api/trials/search/?condition={c}&intervention={i}&phase={p}` | Clinical trial search | external_data_cache | ClinicalTrials.gov |
| GET | `/api/trials/{nct_id}/` | Trial detail | external_data_cache | ClinicalTrials.gov |

### Regulatory
| Method | Endpoint | Description | DB Tables | External APIs |
|---|---|---|---|---|
| GET | `/api/regulatory/guidance/?q={topic}` | FDA guidance document search | external_data_cache | OpenFDA (guidance) |
| GET | `/api/regulatory/labels/?drug={name}` | Drug label (SPL) | external_data_cache | DailyMed |
| GET | `/api/regulatory/ndc/?drug={name}` | NDC / formulation data | external_data_cache | OpenFDA (NDC) |
| GET | `/api/regulatory/excipients/?form={dosage_form}` | Inactive ingredient list | external_data_cache | OpenFDA (label) |

### AI Chat
| Method | Endpoint | Description | DB Tables | External APIs |
|---|---|---|---|---|
| GET | `/api/chat/sessions/` | List sessions | chat_sessions | — |
| POST | `/api/chat/sessions/` | Create session | chat_sessions | — |
| GET | `/api/chat/sessions/{id}/` | Session with full history | chat_sessions, chat_messages | — |
| POST | `/api/chat/sessions/{id}/messages/` | Send message; stream Claude response | chat_sessions, chat_messages, external_data_cache | Claude API + all external APIs (tool calls) |
| DELETE | `/api/chat/sessions/{id}/` | Delete session | chat_sessions, chat_messages | — |

### Documents
| Method | Endpoint | Description | DB Tables | External APIs |
|---|---|---|---|---|
| GET | `/api/projects/{id}/documents/` | List project documents | documents | — |
| POST | `/api/projects/{id}/documents/generate/` | AI-generated document draft | documents, experiments, risk_assessments | Claude API, DailyMed, OpenFDA |
| POST | `/api/projects/{id}/documents/` | Save manual document | documents | — |
| GET | `/api/documents/{id}/` | Document content | documents | — |
| PUT | `/api/documents/{id}/` | Update document | documents | — |
| POST | `/api/documents/{id}/export/` | Export as PDF or DOCX | documents | — |

---

## Vue Component List

### Layout
| Component | Description |
|---|---|
| `AppShell` | Root layout: side nav + main content area |
| `SideNav` | Navigation sidebar with page links and project switcher |
| `TopBar` | Header: current project name, user menu, global search |
| `PageHeader` | Per-page title row with action buttons slot |

### Shared / Common
| Component | Description |
|---|---|
| `LoadingSpinner` | Centered spinner for async states |
| `ErrorBanner` | Red banner with error message and retry action |
| `EmptyState` | Illustrated empty-state with CTA |
| `DataTable` | Sortable, paginated table with slot-based columns |
| `SearchInput` | Debounced input with loading indicator |
| `FilterPanel` | Faceted filter sidebar (checkboxes, date range, selects) |
| `ConfirmDialog` | Modal confirmation dialog |
| `ToastNotification` | Transient success/error/info toasts |
| `MarkdownRenderer` | Renders Markdown to HTML safely |
| `ExportButton` | Format selector (PDF/DOCX) + download trigger |
| `StreamingIndicator` | Animated dots while AI is generating |
| `StatsBadge` | Numeric chip label |
| `SaveReferenceBtn` | Saves an external item as a project reference |

### Dashboard
| Component | Description |
|---|---|
| `DashboardPage` | Page root |
| `ProjectCard` | Project summary: name, phase badge, status, compound count |
| `RecentActivityFeed` | Chronological experiment + result activity list |
| `QuickActionPanel` | CTA buttons: New Project, Open Chat, New Experiment |

### Project Setup
| Component | Description |
|---|---|
| `ProjectSetupPage` | Page root (wizard layout) |
| `ProjectForm` | Project name, description, phase, status fields |
| `CompoundSearch` | Debounced compound name search against PubChem/ChEMBL |
| `CompoundPreviewCard` | Selected compound summary: SMILES, MW, formula |
| `ObjectiveWizard` | Phase-specific guided objective input |

### Compound Profile
| Component | Description |
|---|---|
| `CompoundProfilePage` | Page root |
| `CompoundHeader` | Name, IDs, approval badge |
| `MoleculeViewer` | 2D structure PNG display |
| `PropertyTable` | Physicochemical key-value table |
| `ADMETCard` | Color-coded ADMET endpoint grid |
| `SafetyPanel` | Toxicity flags and Tox21 assay summary |
| `TargetList` | Pharmacological target table with UniProt links |
| `SimilarCompoundsList` | Fingerprint-similar compound mini cards |

### Disease & Target Explorer
| Component | Description |
|---|---|
| `DiseaseExplorerPage` | Page root |
| `DiseaseSearch` | Autocomplete disease name input |
| `DiseaseOverviewCard` | Disease name, EFO ID, description |
| `TargetAssociationTable` | Ranked target list with association score bars |
| `KnownDrugsTable` | Clinical drugs for the indication: name, phase, status |
| `TargetDetailCard` | Slide-in panel with UniProt protein details |

### Experiment Planner
| Component | Description |
|---|---|
| `ExperimentPlannerPage` | Page root |
| `ExperimentForm` | Type selector, objective, project/compound pickers |
| `VariableBuilder` | Dynamic variable row editor (name, unit, range) |
| `SuccessCriteriaPanel` | Structured + free-text success criteria input |
| `RetrosynPreview` | Inline top-3 ASKCOS precursor candidates |
| `ExcipientSuggestion` | Suggested inactive ingredients for dosage form |

### Experiment Results
| Component | Description |
|---|---|
| `ExperimentResultsPage` | Page root |
| `ResultsForm` | Dynamic metric entry fields matching experiment variables |
| `AIInterpretation` | Streamed Claude result interpretation |
| `DecisionPanel` | Optimize / Reproduce / Scale / Abort decision buttons |
| `ResultsTimeline` | Chronological prior submissions list |
| `ResultsChart` | Line/bar chart of metric values over submissions |

### Risk Analysis
| Component | Description |
|---|---|
| `RiskAnalysisPage` | Page root |
| `RiskHeatMap` | 5×5 probability–impact grid with draggable risk markers |
| `RiskFactorList` | Editable risk factor rows with category and level |
| `RegulatorySummary` | Matched FDA guidance document cards |
| `ClinicalPrecedentCard` | Trial count and phase breakdown for the indication |
| `GenerateRiskBtn` | Triggers AI risk assessment generation |

### Synthesis Planning
| Component | Description |
|---|---|
| `SynthesisPlanningPage` | Page root |
| `SynthesisInput` | SMILES input with structure validation |
| `RetrosynTree` | Interactive D3 retrosynthesis tree |
| `ReactionStepCard` | Single step: reactants, reagents, conditions, confidence |
| `ForwardPredictionPanel` | Reactant input → predicted product display |
| `ConditionRecommender` | Solvent, reagent, temperature suggestion list |
| `BuyableCheck` | Commercial availability badge per leaf node |
| `SpectraViewer` | NIST IR/MS spectrum plot |

### Literature & Clinical Trials
| Component | Description |
|---|---|
| `LiteraturePage` | Page root (tabbed: Literature / Clinical Trials) |
| `LiteratureSearch` | PubMed query input with field selectors |
| `ArticleCard` | Title, authors, journal, date, abstract excerpt |
| `TrialSearch` | Condition + intervention inputs with phase/status filters |
| `TrialCard` | NCT ID, title, phase, status, enrollment, primary outcome |

### AI Chat Assistant
| Component | Description |
|---|---|
| `ChatPage` | Page root |
| `SessionList` | Sidebar of saved sessions for the project |
| `ChatInterface` | Scrollable message history + input bar |
| `MessageBubble` | Single message with role and timestamp |
| `SourceCitation` | Collapsible API source list on assistant messages |
| `SuggestedQueries` | Example questions on empty session state |

### Process Documentation
| Component | Description |
|---|---|
| `DocumentationPage` | Page root |
| `DocumentList` | Saved documents with type badge and date |
| `DocumentEditor` | Markdown editor (CodeMirror / ProseMirror) |
| `SectionBuilder` | Collapsible section panels for document structure |
| `GenerateDocBtn` | Triggers Claude document draft generation |

---

## AI Integration

All AI features use the **Claude API** (`claude-sonnet-4-6`) via the Anthropic Python SDK with prompt caching enabled on system prompts. The three integration patterns are:

1. **Tool-use chat** (`/api/chat/sessions/{id}/messages/`) — Claude is given a system prompt with project context and a tool definition for each of the 13 external API categories. It decides which APIs to call during a turn and streams the final answer with source citations.

2. **Targeted generation** — One-shot Claude calls for specific tasks: experiment result interpretation (`/api/experiments/{id}/interpret/`), risk assessment generation (`/api/projects/{id}/risk-assessment/generate/`), and document drafting (`/api/projects/{id}/documents/generate/`). These use a structured system prompt and the relevant project data as user message context.

3. **Response streaming** — All Claude calls use the streaming API; the Django backend forwards Server-Sent Events (SSE) to the Vue frontend so text appears incrementally.

---

## Caching Strategy

External API calls are expensive in latency and subject to rate limits. All responses are cached in `external_data_cache` keyed by `(source, sha256(endpoint + params))`:

| Source | Default TTL |
|---|---|
| PubChem, ChEMBL, UniProt, Open Targets | 7 days |
| EPA CompTox, pkCSM | 7 days |
| PubMed, ClinicalTrials.gov | 1 day |
| OpenFDA, DailyMed | 3 days |
| ASKCOS | 24 hours |
| NIST WebBook | 30 days |

In production, replace the DB cache table with **Redis** and use `django-redis` as the cache backend. Compound structure images are stored as static files rather than re-fetched on every request.
