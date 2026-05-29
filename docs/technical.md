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

---

## UPDATE 1 — Competitive Drug Intelligence & Analog Development

Technical additions required to implement the workflow defined in `product.md` UPDATE 1.

---

### New External API Services

#### `core/services/surechembl.py`

Primary patent data source. SureChEMBL (EMBL-EBI) is a free, structure-searchable patent chemistry database covering 17M+ patent compounds.

| Field | Detail |
|---|---|
| **Base URL** | `https://www.surechembl.org/api/v1` |
| **Authentication** | None (public) |
| **Cache TTL** | 30 days |
| **Source key** | `surechembl` |

Key functions:
```python
def search_compound(name: str) -> list          # name → SureChEMBL compound list
def get_compound_patents(schembl_id: str) -> list  # patents for a compound ID
def search_by_smiles(smiles: str) -> list        # structure search → matching patent compounds
```

Each patent document returned contains: `patent_number`, `title`, `abstract`, `filing_date`, `publication_date`, `assignee`, `ipc_classes`. Patent expiry is derived as `filing_date + 20 years` (standard term).

#### `core/services/espacenet.py` (supplementary)

EPO's Open Patent Services (OPS) REST API for full patent text and claim language when SureChEMBL surfaces a relevant patent number.

| Field | Detail |
|---|---|
| **Base URL** | `https://ops.epo.org/3.2/rest-services` |
| **Authentication** | OAuth2 client credentials (free registration at EPO) |
| **Cache TTL** | 30 days |
| **Source key** | `espacenet` |

Key functions:
```python
def get_patent(patent_number: str) -> dict   # full patent: title, abstract, claims, status
def search_patents(query: str) -> list       # keyword/name patent search
```

Used only to retrieve claim text after SureChEMBL identifies a patent number. Not used as a primary search surface.

---

### New Database Models

Add to `core/models.py`:

#### `DrugInvestigation`

Persists a scientist's intelligence-gathering session on a reference drug. Not linked to a project — this is discovery-mode work that precedes project creation.

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| chembl_id | VARCHAR(20) | e.g. `CHEMBL25` |
| name | VARCHAR(255) | Common name |
| smiles | TEXT | Reference drug SMILES |
| disease_name | VARCHAR(255) | Disease context for this investigation |
| notes | TEXT | Scientist's free-text notes |
| created_at | DATETIME | auto_now_add |
| updated_at | DATETIME | auto_now |

#### `AnalogCandidate`

A structural analog candidate identified during an investigation, with patent and ADMET assessment results.

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| investigation_id | INTEGER FK → drug_investigations | |
| smiles | TEXT | Candidate SMILES |
| pubchem_cid | INTEGER | nullable |
| chembl_id | VARCHAR(20) | nullable |
| similarity_score | FLOAT | 0–1 Tanimoto similarity to reference |
| patent_status | VARCHAR(20) | `free` / `covered` / `unknown` |
| patent_refs | JSON | List of patent numbers that cover this structure |
| admet_data | JSON | pkCSM prediction output |
| shortlisted | BOOLEAN | default False |
| notes | TEXT | |
| created_at | DATETIME | auto_now_add |

---

### New Backend Views

Create `core/views/drugs.py`:

| View | Method | Description |
|---|---|---|
| `DrugSearchView` | GET | ChEMBL molecule search by name → returns ChEMBL ID, SMILES, approval status |
| `DrugDetailView` | GET | Aggregate profile: ChEMBL (structure + mechanism) + DailyMed (formulation) |
| `DrugSynthesisView` | GET | PubMed search for published synthesis routes for the drug name |
| `DrugTrialsView` | GET | ClinicalTrials.gov search filtered by drug name as intervention |
| `DrugPatentsView` | GET | SureChEMBL compound search → patent list for the drug |

Create `core/views/patents.py`:

| View | Method | Description |
|---|---|---|
| `PatentSearchView` | GET | SureChEMBL search by drug name or SMILES |
| `PatentDetailView` | GET | Espacenet full patent text + claims by patent number |

Create `core/views/analogs.py`:

| View | Method | Description |
|---|---|---|
| `AnalogSearchView` | POST | PubChem fingerprint similarity from reference SMILES; returns CID list with scores |
| `AnalogPatentCheckView` | POST | For a list of SMILES, queries SureChEMBL to determine patent coverage; returns per-SMILES status |
| `AnalogADMETView` | POST | Batch pkCSM ADMET predictions for a list of SMILES; runs concurrently via `ThreadPoolExecutor` |
| `InvestigationListCreateView` | GET, POST | List and create `DrugInvestigation` records |
| `InvestigationDetailView` | GET, PUT | Retrieve or update an investigation |
| `AnalogCandidateView` | GET, POST | List and save `AnalogCandidate` records for an investigation |

---

### New URL Patterns

Add to `core/urls.py`:

```python
# Drug Intelligence
path('drugs/search/', DrugSearchView.as_view()),
path('drugs/<str:chembl_id>/', DrugDetailView.as_view()),
path('drugs/<str:chembl_id>/synthesis/', DrugSynthesisView.as_view()),
path('drugs/<str:chembl_id>/trials/', DrugTrialsView.as_view()),
path('drugs/<str:chembl_id>/patents/', DrugPatentsView.as_view()),

# Patents
path('patents/', PatentSearchView.as_view()),
path('patents/<str:patent_number>/', PatentDetailView.as_view()),

# Analogs
path('analogs/search/', AnalogSearchView.as_view()),
path('analogs/patent-check/', AnalogPatentCheckView.as_view()),
path('analogs/admet/', AnalogADMETView.as_view()),

# Investigations (persisted sessions)
path('investigations/', InvestigationListCreateView.as_view()),
path('investigations/<int:pk>/', InvestigationDetailView.as_view()),
path('investigations/<int:pk>/candidates/', AnalogCandidateView.as_view()),
```

---

### New Frontend Routes

Add to `frontend/src/router/index.js`:

```js
{ path: '/drugs',                  component: () => import('@/views/DrugIntelligencePage.vue') },
{ path: '/drugs/:chembl_id',       component: () => import('@/views/DrugProfilePage.vue') },
{ path: '/patents',                component: () => import('@/views/PatentExplorerPage.vue') },
{ path: '/analogs',                component: () => import('@/views/AnalogWorkspacePage.vue') },
{ path: '/investigations/:id',     component: () => import('@/views/AnalogWorkspacePage.vue') },
```

---

### New Frontend Pages

#### `DrugIntelligencePage.vue`
Entry point for the discovery workflow. Drug name search input → results list of matching ChEMBL entries → navigate to `DrugProfilePage` on selection.

#### `DrugProfilePage.vue`
Full reference drug profile, assembled from multiple API calls via `Promise.allSettled`:

| Section | Data source |
|---|---|
| Structure + identity | ChEMBL (SMILES, MW, formula, approval status) |
| Mechanism of action | ChEMBL mechanism + Open Targets target associations |
| Formulation details | DailyMed SPL (inactive ingredients, dosage form, route) |
| Clinical trial history | ClinicalTrials.gov filtered by drug name as intervention |
| Synthesis literature | PubMed search: `{drug_name} synthesis` |
| Patent landscape | SureChEMBL compound patents |

Action button: **"Start Analog Search"** → creates a `DrugInvestigation` record and navigates to `AnalogWorkspacePage` pre-loaded with this drug's SMILES.

#### `PatentExplorerPage.vue`
Two search modes: by drug name (text) and by SMILES structure. Results table shows patent number, title, assignee, filing date, derived expiry date, and a "View Claims" button that fetches full text from Espacenet.

#### `AnalogWorkspacePage.vue`
Three-panel layout, representing the three stages of the analog workflow:

**Panel 1 — Reference Drug**: Shows the reference SMILES, structure image, and key properties. Similarity threshold slider (default 0.7 Tanimoto).

**Panel 2 — Candidate Pool**: Runs `POST /api/analogs/search/` → shows CID list with structure thumbnails and similarity scores. A "Check Patents" button runs `POST /api/analogs/patent-check/` and overlays a `free` / `covered` / `unknown` badge on each candidate. A "Run ADMET" button runs `POST /api/analogs/admet/` on all free-to-operate candidates.

**Panel 3 — Shortlist**: Candidates the scientist has pinned. Side-by-side ADMET comparison table (rows = endpoints, columns = candidates + reference drug). "Save to Project" button creates a new project with the shortlisted compound.

---

### New Pinia Stores

#### `stores/drugs.js`

```js
state: {
  searchResults: [],      // ChEMBL drug search hits
  selectedDrug: null,     // { chembl_id, name, smiles }
  profile: {              // loaded asynchronously per section
    detail: null,
    mechanism: null,
    formulation: null,
    trials: [],
    synthesis: [],
    patents: [],
  },
  loading: {},
}
actions: searchDrugs(name), loadProfile(chembl_id)
```

#### `stores/analogs.js`

```js
state: {
  investigation: null,    // current DrugInvestigation record
  referenceDrug: null,    // { smiles, chembl_id, name }
  threshold: 0.7,
  candidates: [],         // [{ smiles, cid, score, patentStatus, admet }]
  shortlisted: [],
  loading: {},
}
actions: searchAnalogs(), checkPatents(), runADMET(), shortlist(candidate), saveToProject()
```

---

### Changes to Existing Components

#### `DiseaseExplorerPage.vue` / `KnownDrugsTable`
- Drug rows in the Known Drugs table become clickable.
- Open Targets returns `drug.id` which is already the ChEMBL ID (e.g. `CHEMBL25`).
- `@click="router.push('/drugs/' + row.drug.id)"` — no ID mapping step required.

#### `SideNav.vue`
Add a **Drug Discovery** section below the existing navigation groups:
```
Drug Discovery
  ├── Drug Intelligence   →  /drugs
  ├── Patent Explorer     →  /patents
  └── Analog Workspace    →  /analogs
```

#### `DocumentationPage.vue`
Add `analog_report` to the `docType` select options. The AI generation prompt for this type should receive: reference drug name, shortlisted analog SMILES, ADMET comparison data, and patent gap summary as context.

#### `claude_client.py` — new tool definitions
Add two tools to `TOOL_DEFINITIONS` so Claude can call patent and drug intelligence data during chat:

```python
{
  "name": "search_patents",
  "description": "Search SureChEMBL for patents covering a drug by name or SMILES structure",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": { "type": "string", "description": "Drug name or SMILES" },
      "mode": { "type": "string", "enum": ["name", "smiles"] }
    },
    "required": ["query", "mode"]
  }
},
{
  "name": "get_drug_profile",
  "description": "Retrieve full profile for an existing approved drug by ChEMBL ID: structure, mechanism, formulation, and clinical history",
  "input_schema": {
    "type": "object",
    "properties": {
      "chembl_id": { "type": "string" }
    },
    "required": ["chembl_id"]
  }
}
```

---

### Updated Caching Strategy

| Source | Default TTL | Notes |
|---|---|---|
| SureChEMBL | 30 days | Patent filings change slowly |
| Espacenet | 30 days | Patent status is stable once retrieved |

Add `surechembl` and `espacenet` to `TTL_MAP` in `core/services/cache.py`.

---

### New DB Migration

Run after adding the two new models:
```bash
python manage.py makemigrations core
python manage.py migrate
```

New tables: `core_druginvestigation`, `core_analogcandidate`.

---

### Implementation Order

1. `core/services/surechembl.py` — patent service (no dependencies)
2. `core/services/espacenet.py` — supplementary patent service
3. DB models + migration (`DrugInvestigation`, `AnalogCandidate`)
4. `core/views/drugs.py` — drug intelligence views
5. `core/views/patents.py` — patent search views
6. `core/views/analogs.py` — analog search, patent check, ADMET batch, investigation CRUD
7. URL patterns in `core/urls.py`
8. Frontend stores: `stores/drugs.js`, `stores/analogs.js`
9. Frontend pages: `DrugIntelligencePage`, `DrugProfilePage`, `PatentExplorerPage`, `AnalogWorkspacePage`
10. Existing component changes: `DiseaseExplorerPage`, `SideNav`, `DocumentationPage`, `claude_client.py`

---

## UPDATE 2 — Synthesis Planning ↔ Project Integration

Implements the data model and UI changes described in `product.md` UPDATE 2. Introduces a clean `Project → SynthesisPlan → Experiment` hierarchy and links `DrugInvestigation` / `AnalogCandidate` records back to the project that spawned them.

---

### New Database Model

#### `SynthesisPlan`

Persists a designed retrosynthetic route against a project. Created when the scientist clicks "Save Route to Project" on the Synthesis Planning page. Decoupled from `Experiment` so that the designed route and the lab execution remain distinct objects.

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | CASCADE delete |
| target_smiles | TEXT | Target molecule SMILES |
| plan_type | VARCHAR(10) | `retro` (single-step) / `tree` (multi-step) |
| route_data | JSON | Full ASKCOS API response (results array or tree) |
| status | VARCHAR(20) | `draft` / `active` / `completed` |
| created_at | DATETIME | auto_now_add |

---

### Schema Changes to Existing Models

| Model | Field added | Type | Notes |
|---|---|---|---|
| `Experiment` | `synthesis_plan` | FK → `SynthesisPlan` | nullable, SET_NULL on delete; populated when experiments are created from a plan |
| `DrugInvestigation` | `project` | FK → `Project` | nullable, SET_NULL; set when the investigation is linked to a project in the Analog Workspace |
| `AnalogCandidate` | `project` | FK → `Project` | nullable, SET_NULL; set for all shortlisted candidates when linked to a project |

Migration: `core/migrations/0003_synthesisplan_and_project_links.py`

---

### New Backend Views

**File:** `core/views/synthesis_plans.py`

| View | Method(s) | Endpoint | Description |
|---|---|---|---|
| `SynthesisPlanListCreateView` | GET, POST | `/api/synthesis-plans/` | List (filterable by `?project=ID`) or create a synthesis plan |
| `SynthesisPlanDetailView` | GET, PATCH, DELETE | `/api/synthesis-plans/{id}/` | Retrieve, update status, or delete a plan |
| `SynthesisPlanExperimentsView` | POST | `/api/synthesis-plans/{id}/plan-experiments/` | Creates `Experiment` records (type: synthesis) from the plan's `route_data.results`, links them via `synthesis_plan` FK, sets plan status to `active` |

**Added to** `core/views/analogs.py`:

| View | Method | Endpoint | Description |
|---|---|---|---|
| `InvestigationLinkProjectView` | POST | `/api/investigations/{id}/link-project/` | Sets `project` FK on the `DrugInvestigation` and, if `link_shortlisted=true` (default), bulk-updates all shortlisted `AnalogCandidate` records to the same project |

**Changed:** `CompoundDetailView` upgraded from `RetrieveAPIView` to `RetrieveDestroyAPIView` to support `DELETE /api/compounds/{id}/` (needed when replacing a compound in an existing project from the Analog Workspace).

---

### New / Updated Serializers

**File:** `core/serializers.py`

| Serializer | Notes |
|---|---|
| `SynthesisPlanSerializer` | Full serializer including `experiment_count` computed field |
| `SynthesisPlanMinimalSerializer` | Lightweight (no `route_data`) used inside `ProjectSerializer` |
| `ProjectSerializer` | Now includes `synthesis_plans` (list of minimal plans), `investigations` (list of linked investigations), `analog_candidates` (shortlisted candidates only) |
| `ExperimentSerializer` | `synthesis_plan` FK field exposed (nullable, not required) |

---

### New URL Patterns

Added to `core/urls.py`:

```python
# Synthesis Plans
path('synthesis-plans/',                              SynthesisPlanListCreateView.as_view()),
path('synthesis-plans/<int:pk>/',                     SynthesisPlanDetailView.as_view()),
path('synthesis-plans/<int:pk>/plan-experiments/',    SynthesisPlanExperimentsView.as_view()),

# Investigation → Project link
path('investigations/<int:pk>/link-project/',         InvestigationLinkProjectView.as_view()),
```

---

### Frontend Changes

#### `frontend/src/services/api.js`

| Addition | Description |
|---|---|
| `synthesisPlan` service | `list(projectId)`, `create(data)`, `get(id)`, `update(id, data)`, `delete(id)`, `planExperiments(id)` |
| `investigations.linkProject(id, projectId, linkShortlisted)` | Calls the new `link-project` endpoint |
| `compounds.delete(id)` | `DELETE /api/compounds/{id}/` — was missing |

#### `frontend/src/stores/analogs.js`

`saveToProject` refactored to accept `{ projectId, projectName, compoundAction }`:
- `projectId` — uses an existing project (null = create new)
- `compoundAction` — `'replace'` deletes existing compounds before adding; `'add'` leaves them in place
- After creating / selecting the project, calls `investigations.linkProject()` to wire the investigation and all shortlisted candidates

#### `frontend/src/views/SynthesisPlanningPage.vue`

| Change | Detail |
|---|---|
| Project picker | Shown at top when no `?project` query param; dropdown of all projects |
| "Save Route to Project" button | Appears after retrosynthesis results load, if a project is linked. Calls `synthesisPlanApi.create()`. Disabled (with tooltip) if no project selected |
| "Plan Experiments" button | Replaces the old direct experiment-creation flow. Only shown after a plan is saved (`savedPlan` ref is set). Calls `synthesisPlanApi.planExperiments(id)` |

#### `frontend/src/views/AnalogWorkspacePage.vue`

| Change | Detail |
|---|---|
| Project selector in Shortlist panel | Dropdown: existing projects + "Create new project" option |
| New project name input | Shown only when "Create new project" is selected |
| Compound conflict dialog | If the selected existing project already has compounds, a modal dialog asks "Replace existing" or "Add alongside" |
| Save logic | On confirm, calls `store.saveToProject()` then navigates to `/synthesis?smiles=X&project=Y` |

#### `frontend/src/views/ProjectSetupPage.vue`

In edit mode, three new sections are rendered below the form:

| Section | Shown when | Content |
|---|---|---|
| Reference Drug & Analogs | Project has a linked `DrugInvestigation` | Reference drug name, ChEMBL ID, SMILES; chip list of shortlisted analog candidates with similarity score and patent status badge |
| Synthesis Plans | Always in edit mode | Table: target SMILES, plan type, status, step count, date. Actions: "Browse" (→ `/synthesis?smiles=X&project=Y`) and "Plan Experiments" (calls `planExperiments`, only shown when `experiment_count === 0`) |
| Experiments | Always in edit mode | Table: title, type badge, status badge, date. "View" link to `/experiments/{id}` |

Data is loaded in `loadEditData()` via parallel `synthesisPlanApi.list(id)` and `experimentsApi.list(id)` calls, invoked after the project is fetched.

---

### Updated Database Schema Summary

The full `Project` detail response (`GET /api/projects/{id}/`) now includes:

```json
{
  "synthesis_plans": [
    { "id": 1, "target_smiles": "...", "plan_type": "retro", "status": "active", "created_at": "...", "experiment_count": 3 }
  ],
  "investigations": [
    { "id": 1, "name": "Aspirin", "chembl_id": "CHEMBL25", "smiles": "...", "disease_name": "Pain" }
  ],
  "analog_candidates": [
    { "id": 4, "smiles": "...", "pubchem_cid": 12345, "similarity_score": 0.82, "patent_status": "free", "shortlisted": true }
  ]
}
```

---

## UPDATE 3 — Synthesis Planning Page Redesign

### Overview of Changes

| Area | Change |
|---|---|
| `SynthesisPlanningPage.vue` | Auto-run + auto-save; inline conditions; SynthesisTreeNode fix; padding |
| `core/services/askcos.py` | `recommend_conditions` keyword matching |
| `core/views/synthesis.py` | `ConditionRecommendView` reads `reaction_type` from body |

---

### Backend Changes

#### `core/services/askcos.py` — `recommend_conditions`

Added a `keywords` list to each entry in `conditions_db`. When `reaction_type` is provided, the function checks whether any keyword appears in `reaction_type.lower()` (or the reaction type string appears in `entry['reaction_type'].lower()`). If a match is found it returns only that one entry (instead of the first 5). This allows the frontend to pass a transform name such as `"Amide bond formation"` and receive the exact amide coupling conditions.

```python
conditions_db = [
    {'reaction_type': 'Amide coupling', 'keywords': ['amide', 'amide bond', 'amide coupling'],
     'reagents': 'HATU, DIPEA', 'solvent': 'DMF', 'temp': 'RT', 'time': '2–4 h'},
    # … 11 more entries
]
if reaction_type:
    rt_lower = reaction_type.lower()
    for entry in conditions_db:
        if any(kw in rt_lower for kw in entry['keywords']) or rt_lower in entry['reaction_type'].lower():
            return {'reactants': reactants, 'products': products, 'conditions': [entry]}
return {'reactants': reactants, 'products': products, 'conditions': conditions_db[:n]}
```

#### `core/views/synthesis.py` — `ConditionRecommendView`

`reaction_type` is now read from `request.data` (POST body) and forwarded to `askcos.recommend_conditions()`. Previously it was ignored.

---

### Frontend Changes

#### `frontend/src/views/SynthesisPlanningPage.vue`

**SynthesisTreeNode — recursive component fix**

The component was previously defined in a separate `<script>` Options API block and registered via `export default { components: { SynthesisTreeNode } }`. In Vue 3, a component defined this way cannot reference itself in its own `template` string because its `components` option was empty — breaking recursive tree rendering.

Fix: the component is defined as a plain object inside `<script setup>` scope (making it accessible to the parent template automatically) and then patched to self-register:

```js
const SynthesisTreeNode = {
  name: 'SynthesisTreeNode',
  props: { node: Object, depth: { type: Number, default: 0 } },
  template: `...`, // uses <SynthesisTreeNode> recursively
}
SynthesisTreeNode.components = { SynthesisTreeNode }  // enables recursion in runtime-compiled template
```

The separate `<script>` block was removed entirely.

**Auto-run on mount**

```js
const fromAnalogWorkspace = computed(() => !!(route.query.smiles && route.query.project))

onMounted(async () => {
  if (route.query.smiles) smiles.value = route.query.smiles
  if (route.query.project) linkedProjectId.value = Number(route.query.project)
  // …
  if (fromAnalogWorkspace.value) await runRetro('retro')
})
```

**Auto-save on results load**

`runRetro` no longer takes an `autoSave` parameter. Saving is unconditional whenever a project is linked and results are valid:

```js
const runRetro = async (action) => {
  // …
  if (action === 'retro') {
    retroResult.value = await synthesisApi.retro({ smiles: smiles.value })
    steps.forEach((step, i) => fetchStepConditions(step, i))
    if (linkedProjectId.value && retroResult.value && !retroResult.value.error) {
      await saveRoute('retro', retroResult.value)
    }
  } else {
    treeResult.value = await synthesisApi.tree({ smiles: smiles.value })
    if (linkedProjectId.value && treeResult.value && !treeResult.value.error) {
      await saveRoute('tree', treeResult.value)
    }
  }
}
```

"Save Route to Project" buttons removed from both retro and tree result sections.

**Inline conditions**

`fetchStepConditions(step, index)` is called for each step immediately after results load. It calls `POST /api/synthesis/conditions/` with `reaction_type: step.transform`. The result is stored in `stepConditions[index]` (null = loading, false = not found, object = conditions). Each step card renders a conditions box:

```vue
<div v-if="stepConditions[i] === null" class="text-muted text-sm">Fetching conditions…</div>
<div v-else-if="stepConditions[i] === false" class="text-muted text-sm">Conditions not available…</div>
<div v-else class="flex gap-4 text-sm">
  <span><b>Reagents:</b> {{ stepConditions[i].reagents }}</span>
  <span><b>Solvent:</b> {{ stepConditions[i].solvent }}</span>
  <span><b>Temp:</b> {{ stepConditions[i].temp }}</span>
  <span><b>Time:</b> {{ stepConditions[i].time }}</span>
</div>
```

**Buyability check per precursor**

Each precursor has a "Check availability" button that calls `GET /api/synthesis/buyables/?smiles=X`. Result stored in `stepBuyability['step-{i}-{j}']`. Button shows "✓ Available" (green) or "✗ Custom" (red) after the check.

**Top padding**

Outer `<div>` changed to `<div style="padding-top:16px">` to prevent the page header from sitting flush against the viewport top.

**Forward Prediction**

Moved into a collapsible `<div id="advanced-section">` at the bottom. The collapse toggle sets `showAdvanced` ref. The "Use in Forward Prediction" button on each step card scrolls to this section and populates `reactant1`/`reactant2` from the step's precursors.

---

## UPDATE 4 — Analog-Centric Synthesis Planning & Plan Comparison

Implements the workflow redesign described in `product.md` UPDATE 4. Plans are now explicitly linked to analog candidates, plan creation flows through the Analogs table on the project page, and a comparison page lets scientists view multiple routes side by side.

---

### Database Changes

#### `SynthesisPlan` — new field + constraint

| Field | Type | Notes |
|---|---|---|
| `analog_candidate` | FK → `AnalogCandidate` | nullable, SET_NULL; links a plan to the specific analog it was designed for |

**Unique constraint** (partial): `UniqueConstraint(fields=['analog_candidate', 'plan_type'], condition=Q(analog_candidate__isnull=False), name='unique_plan_type_per_analog')` — enforces at most one single-step and one multi-step plan per analog candidate.

Migration: `core/migrations/0004_synthesisplan_analog_candidate.py`

---

### Backend Changes

#### `core/serializers.py`

| Change | Detail |
|---|---|
| `SynthesisPlanSerializer` | Added `analog_candidate` field (nullable, not required) |
| `SynthesisPlanMinimalSerializer` | Added `analog_candidate` field |
| `ProjectSerializer.get_analog_candidates` | Each candidate now includes `retro_plan_id` and `tree_plan_id` (the IDs of any single-step / multi-step plan linked to that candidate, or `null` if none exists) |

`get_analog_candidates` implementation:
```python
def get_analog_candidates(self, obj):
    result = []
    for c in obj.analog_candidates.filter(shortlisted=True):
        plans = {p.plan_type: p.id for p in c.synthesis_plans.all()}
        result.append({
            'id': c.id, 'smiles': c.smiles, 'pubchem_cid': c.pubchem_cid,
            'similarity_score': c.similarity_score, 'patent_status': c.patent_status,
            'shortlisted': c.shortlisted,
            'retro_plan_id': plans.get('retro'),
            'tree_plan_id': plans.get('tree'),
        })
    return result
```

#### `core/views/synthesis_plans.py`

| Change | Detail |
|---|---|
| `get_queryset` | Accepts `?analog=ID` query param in addition to `?project=ID` |
| `perform_create` | Returns HTTP 400 if a plan of the same `plan_type` already exists for the given `analog_candidate` (guards against race conditions beyond the DB constraint) |

#### `core/views/analogs.py` + `core/urls.py`

Added `AnalogCandidateDetailView` (`RetrieveUpdateAPIView`) at `PATCH /api/analog-candidates/{id}/` for immediate shortlist toggling in project mode.

---

### Frontend Changes

#### `frontend/src/services/api.js`

| Change | Detail |
|---|---|
| `synthesisPlan.list(params)` | Now accepts a plain object `{ project, analog }` or a legacy numeric project ID |
| `analogCandidates.update(id, data)` | New — `PATCH /api/analog-candidates/{id}/` |

#### `frontend/src/stores/analogs.js`

| Change | Detail |
|---|---|
| `toggleShortlistPersisted(candidate, projectId)` | New — immediately PATCHes the candidate's `shortlisted` field; used in project mode |
| `saveNewCandidatesToProject(projectId)` | New — bulk-creates candidates without a DB id, then calls `linkProject`; used by the "Done" button in project mode |
| `saveToProject` | If `this.investigation` is null (drug-search mode coming straight from DrugProfilePage), creates a `DrugInvestigation` on the fly, persists all shortlisted candidates into it, then links it to the project. Redirects to the project page — not to Synthesis Planning |

#### `frontend/src/views/AnalogWorkspacePage.vue`

**Project mode** (entered via `?project=ID`):
- On mount: fetches project detail → gets first investigation id → calls `store.loadInvestigation(invId)` to pre-populate candidates
- Candidate toggle calls `store.toggleShortlistPersisted` (immediate PATCH) instead of the local-only `toggleShortlist`
- Panel 3 shows a "Save & Return to Project" button instead of the project selector; button calls `store.saveNewCandidatesToProject(projectId)` then navigates to `/projects/{id}/edit`
- A blue banner identifies project mode

**Drug search mode** (no `?project`):
- Unchanged UX; after `saveToProject`, redirects to `/projects/{id}/edit` (was `/synthesis?...` in UPDATE 3)

#### `frontend/src/views/ProjectSetupPage.vue`

| Change | Detail |
|---|---|
| Analog chip list → Analog table | Columns: SMILES, Similarity, Patent, Single-Step, Multi-Step. Plan status cells show "✓ Done" badge or "Plan →" button |
| `planSynthesis(analogId, type)` | New — navigates to `/synthesis?project=ID&analog=ID&type=retro\|tree&autorun=1` |
| "Start New Plan" removed | Replaced with "Find Analog" button → `/analogs?project=ID` |
| `selectedPlanIds` ref | Array bound to plan row checkboxes via `v-model` |
| Compare button | Shown (disabled until ≥2 selected) when the project has ≥2 synthesis plans; navigates to `/synthesis/compare?plans=1,2,...` |
| `browseRoute(plan)` | Now passes `?plan=ID&type=TYPE&smiles=SMILES` so the exact plan is loaded |

#### `frontend/src/views/SynthesisPlanningPage.vue`

New URL parameters read on mount:

| Param | Ref set | Effect |
|---|---|---|
| `?plan=ID` | `linkedPlanId` | `loadExistingPlan` fetches by ID; hydrates results; locks type |
| `?analog=ID` | `linkedAnalogId` | `loadProjectDetail` resolves SMILES from `analog_candidates`; skips analog picker |
| `?type=retro\|tree` | `lockedType` | Non-matching analysis type button is disabled |
| `?autorun=1` | — | Stripped from URL immediately via `router.replace`; triggers auto-run + auto-save of `lockedType` |

**`loadExistingPlan` — updated logic:**
```js
if (linkedPlanId.value) {
  plan = await synthesisPlanApi.get(linkedPlanId.value)
} else {
  const params = { project: linkedProjectId.value }
  if (linkedAnalogId.value) params.analog = linkedAnalogId.value
  const plans = await synthesisPlanApi.list(params)
  const filtered = lockedType.value ? plans.filter(p => p.plan_type === lockedType.value) : plans
  plan = filtered[filtered.length - 1] || null
}
// Hydrate result refs and lock type
if (plan?.route_data) {
  plan.plan_type === 'retro'
    ? (retroResult.value = plan.route_data)
    : (treeResult.value = plan.route_data)
  activeAnalysisType.value = plan.plan_type
  lockedType.value = plan.plan_type
  resultSynced.value = true
}
```

**`smilesLocked` computed — simplified:**
```js
const smilesLocked = computed(() => !!(linkedProjectId.value && smiles.value))
```
Previously required `referenceInvestigation` — removed that dependency so the locked context panel renders even when the project has no investigation (e.g., when navigating via `?analog` without a full investigation chain).

The reference drug sub-panel inside the locked context panel is wrapped in `v-if="referenceInvestigation"` so it only renders when investigation context is available.

**`saveRoute`** — passes `analog_candidate` FK when `linkedAnalogId` is set:
```js
synthesisPlanApi.create({
  project: linkedProjectId.value,
  target_smiles: smiles.value,
  plan_type: planType,
  route_data: result,
  ...(linkedAnalogId.value ? { analog_candidate: linkedAnalogId.value } : {}),
})
```

#### `frontend/src/views/SynthesisPlanComparisonPage.vue` (new)

Route: `/synthesis/compare?plans=1,2,...`

- Reads `?plans` CSV on mount; fetches each plan in parallel via `synthesisPlanApi.get(id)`
- Header row: one card per plan showing type badge, status, target SMILES, structure image (depict.chembl.io), step count, experiment count, creation date
- Detail row: one column per plan showing full route — retro step cards (transform, precursors) or recursive synthesis tree via `SynthesisTreeNode`
- Layout: CSS grid with `grid-template-columns: repeat(N, 1fr)` where N is the number of selected plans

#### `frontend/src/router/index.js`

Added route: `{ path: '/synthesis/compare', name: 'SynthesisPlanComparison', component: () => import('@/views/SynthesisPlanComparisonPage.vue') }`
```
