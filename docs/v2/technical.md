# Technical Blueprint — BioIntel v2

## Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | Vue 3, Vite, Vue Router 4, Pinia, Axios |
| **Backend** | Django 5, Django REST Framework |
| **Database** | SQLite (development) → PostgreSQL (production) |
| **AI** | Claude API (Anthropic) — claude-sonnet-4-6 |
| **Caching** | `external_data_cache` DB table (dev) → Redis (production) |
| **Cheminformatics** | RDKit (retrosynthesis transforms, SMILES validation, buyability heuristic) |
| **Molecular Docking** | AutoDock Vina (subprocess via RDKit + Open Babel for PDBQT preparation) |
| **Virtual Screening Libraries** | ZINC20 REST API (FDA-approved and clinical candidate subsets) |
| **Crystal Structure Data** | CCDC public REST API (salt/polymorph screening) |
| **Package management** | pip + venv (backend), npm (frontend) |

---

## Application Overview

BioIntel v2 is a full-spectrum pharmaceutical R&D platform serving medicinal chemists, process/formulation scientists, analytical scientists, and drug development managers. It covers the entire pre-IND drug development pipeline across nine sequential phases: Target Biology, Drug Discovery, Lead Optimization, Drug Substance Development, Drug Product Development, Analytical Development, Preclinical Development, Regulatory Documentation, and AI-Assisted Planning. Scientists can enter at any phase — the platform supports both analog-based development (starting from a known reference drug) and novel drug design (starting from a biological target). Every project tracks its current phase status with explicit go/no-go decision gates. All pages are structured with a per-page context API so that a collapsible AI window (planned for a future release) can receive the full page data and answer questions inline. The automated drug design agent — where a scientist describes a problem in natural language and the system generates a complete development plan — is also planned for a future release. In v2, all workflows are manually executable by scientists, backed by integrations with 20+ public data sources and a per-project Claude AI chat assistant.

---

## Database Schema

All tables are managed by Django ORM migrations. JSON fields use `django.db.models.JSONField`.

### Existing Tables — v2 Changes Only

#### `projects` (modified)
Added fields:
| Column | Type | Notes |
|---|---|---|
| pathway | VARCHAR(20) | `analog_based` / `novel_design` — controls discovery section visibility; default `analog_based` |

The existing `phase` field (preclinical / phase1 / phase2 / phase3) is kept for backward compatibility but superseded by the new `project_phases` table for v2 phase tracking.

#### `documents` (modified)
`doc_type` enum extended with: `formulation_report`, `stability_summary`, `admet_summary`, `ind_cmc`, `handoff`

#### `experiments` (modified)
Added fields:
| Column | Type | Notes |
|---|---|---|
| formulation_plan | INTEGER FK → formulation_plans | nullable, SET_NULL |
| preclinical_study | INTEGER FK → preclinical_studies | nullable, SET_NULL |

`experiment_type` enum extended with: `preclinical`

#### `external_data_cache` (modified)
`source` enum extended with: `pdb`, `zinc`, `ccdc`

---

### New Tables (v2)

#### `project_phases`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | CASCADE |
| phase | VARCHAR(30) | discovery / lead_optimization / drug_substance / drug_product / analytical / preclinical / regulatory |
| status | VARCHAR(20) | not_started / in_progress / complete / on_hold |
| decision | VARCHAR(10) | go / no_go / null |
| decision_rationale | TEXT | |
| decided_at | DATETIME | nullable |
| created_at | DATETIME | auto_now_add |

#### `target_profiles`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| uniprot_id | VARCHAR(20) | |
| gene_symbol | VARCHAR(50) | |
| protein_name | VARCHAR(255) | |
| organism | VARCHAR(100) | |
| pdb_ids | JSON | list of PDB IDs fetched from RCSB |
| selected_pdb_id | VARCHAR(10) | nullable; chosen for docking |
| binding_site_definition | JSON | `{"center": [x,y,z], "size": [sx,sy,sz]}` docking box |
| notes | TEXT | |
| created_at | DATETIME | auto_now_add |

#### `virtual_screening_runs`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| target_profile_id | INTEGER FK → target_profiles | CASCADE |
| library | VARCHAR(30) | fda_approved / clinical_candidates / fragments / custom |
| custom_smiles | JSON | nullable; list of SMILES for custom library |
| status | VARCHAR(20) | pending / running / complete / failed |
| result_count | INTEGER | nullable |
| error_message | TEXT | nullable; populated on failure |
| created_at | DATETIME | auto_now_add |
| completed_at | DATETIME | nullable |

#### `virtual_screening_hits`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| run_id | INTEGER FK → virtual_screening_runs | CASCADE |
| smiles | TEXT | |
| pubchem_cid | INTEGER | nullable |
| chembl_id | VARCHAR(20) | nullable |
| compound_name | VARCHAR(255) | nullable |
| docking_score | FLOAT | kcal/mol; more negative = better binding |
| lipinski_compliant | BOOLEAN | |
| patent_status | VARCHAR(20) | free / covered / unknown |
| admet_data | JSON | nullable; pkCSM predictions |
| shortlisted | BOOLEAN | default False |

#### `sar_entries`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | CASCADE |
| compound_id | INTEGER FK → compounds | SET_NULL; the modified compound |
| parent_compound_id | INTEGER FK → compounds | nullable, SET_NULL; the parent structure |
| structural_modification | TEXT | free-text description of the change made |
| property | VARCHAR(30) | potency / selectivity / solubility / permeability / metabolic_stability / herg / toxicity / other |
| observed_value | FLOAT | |
| unit | VARCHAR(30) | e.g. µM, mg/mL, % |
| assay_method | TEXT | |
| verdict | VARCHAR(20) | improved / worsened / no_change / mixed |
| rationale | TEXT | |
| experiment_id | INTEGER FK → experiments | nullable, SET_NULL |
| created_at | DATETIME | auto_now_add |

#### `formulation_plans`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | CASCADE |
| dosage_form | VARCHAR(30) | tablet / capsule / oral_solution / injectable / topical / patch / inhaled |
| route_of_administration | VARCHAR(30) | oral / parenteral / topical / inhalation / transdermal |
| target_dose_mg | FLOAT | mg of API per dosage unit |
| release_type | VARCHAR(30) | immediate / modified / extended / delayed |
| manufacturing_process | TEXT | granulation method, coating notes, fill/finish for injectables |
| rationale | TEXT | scientific rationale for formulation approach |
| status | VARCHAR(20) | draft / active / locked |
| created_at | DATETIME | auto_now_add |
| updated_at | DATETIME | auto_now |

#### `formulation_components`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| formulation_plan_id | INTEGER FK → formulation_plans | CASCADE |
| excipient_name | VARCHAR(255) | free-text name; resolved to excipient_id on save |
| excipient_id | INTEGER FK → excipients | nullable; FK to seeded excipient library |
| function | VARCHAR(50) | diluent / binder / disintegrant / lubricant / glidant / coating / stabilizer / surfactant / preservative / solubilizer / other |
| quantity_mg | FLOAT | mg per dosage unit |
| quantity_pct | FLOAT | %w/w |
| iig_max_mg | FLOAT | nullable; from IIG lookup for this route |
| iig_compliant | BOOLEAN | nullable; null = not yet checked |
| rationale | TEXT | |

#### `compatibility_flags`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| formulation_plan_id | INTEGER FK → formulation_plans | CASCADE |
| excipient_name | VARCHAR(255) | |
| risk_level | VARCHAR(10) | low / medium / high / critical |
| mechanism | TEXT | reason for the incompatibility |
| rationale | TEXT | scientist override rationale if accepted despite risk |

#### `excipients`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| name | VARCHAR(255) | canonical common name |
| synonyms | JSON | list of alternative names and brand names |
| cas_number | VARCHAR(20) | |
| formula | VARCHAR(100) | nullable |
| functions | JSON | list of functional categories |
| routes | JSON | list of approved administration routes |
| iig_limits | JSON | `{"oral": 500, "parenteral": 50}` max mg per route |
| gras | BOOLEAN | |
| known_incompatibilities | JSON | list of functional groups or compound class strings |
| usp_monograph | VARCHAR(100) | nullable |
| ph_eur_monograph | VARCHAR(100) | nullable |

*Populated at deploy time via management command from a bundled CSV (FDA IIG + common pharma excipients). Not user-created.*

#### `salt_polymorph_screens`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | CASCADE |
| objective | TEXT | |
| baseline_pka | FLOAT | nullable |
| baseline_melting_point | FLOAT | nullable |
| selected_form | VARCHAR(255) | nullable; the chosen solid form name |
| selection_rationale | TEXT | |
| status | VARCHAR(20) | planned / in_progress / complete |
| created_at | DATETIME | auto_now_add |

#### `salt_screen_candidates`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| screen_id | INTEGER FK → salt_polymorph_screens | CASCADE |
| counterion_name | VARCHAR(255) | |
| cas_number | VARCHAR(20) | nullable |
| pka_delta | FLOAT | nullable; theoretical pKa difference |
| theoretical_solubility_impact | VARCHAR(30) | improved / neutral / decreased / unknown |

#### `salt_screen_experiments`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| candidate_id | INTEGER FK → salt_screen_candidates | CASCADE |
| prep_method | VARCHAR(30) | slurry / evaporation / grinding / spray_dry |
| solvent | VARCHAR(100) | |
| ratio | VARCHAR(50) | e.g. "1:1 API:counterion (molar)" |
| temperature_c | FLOAT | |
| results_xrpd | TEXT | XRPD pattern description or file reference |
| results_dsc | TEXT | DSC melting point and enthalpy observations |
| results_tga | TEXT | TGA weight loss observations |
| observed_form | VARCHAR(30) | crystalline / amorphous / unchanged / mixed |
| notes | TEXT | |
| created_at | DATETIME | auto_now_add |

#### `stability_plans`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | CASCADE |
| material_type | VARCHAR(20) | drug_substance / drug_product |
| intended_storage_condition | VARCHAR(100) | e.g. "Store below 25°C" |
| status | VARCHAR(20) | planned / in_progress / complete |
| created_at | DATETIME | auto_now_add |

#### `stability_conditions`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| stability_plan_id | INTEGER FK → stability_plans | CASCADE |
| condition_name | VARCHAR(50) | long_term / intermediate / accelerated / refrigerated / frozen / photostability |
| temperature_c | FLOAT | |
| humidity_rh | FLOAT | nullable |
| timepoints | JSON | list of months, e.g. `[0, 1, 3, 6, 12, 24]` |
| tests | JSON | list of test names to run at each timepoint |

#### `stability_results`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| condition_id | INTEGER FK → stability_conditions | CASCADE |
| timepoint_months | FLOAT | |
| test_results | JSON | `{"assay": 99.2, "impurity_total": 0.3, "appearance": "white powder", "dissolution": 87}` |
| oos_flags | JSON | list of test names that failed acceptance criteria |
| oot_flags | JSON | list of test names showing out-of-trend results |
| recorded_at | DATETIME | auto_now_add |
| notes | TEXT | |

#### `analytical_methods`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | CASCADE |
| name | VARCHAR(255) | |
| method_type | VARCHAR(30) | hplc / nmr / ms / kf / dissolution / particle_size / appearance / ph / osmolality |
| purpose | VARCHAR(30) | identification / assay / purity / impurity / dissolution / water |
| analytes | JSON | list of analyte names detected |
| instrument_type | VARCHAR(100) | |
| reference_standards | TEXT | |
| final_parameters | JSON | column, mobile phase, gradient, flow_rate, wavelength, runtime, LOD, LOQ |
| status | VARCHAR(20) | in_development / developed / validated |
| created_at | DATETIME | auto_now_add |

#### `specifications`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | CASCADE |
| material_type | VARCHAR(20) | drug_substance / drug_product |
| tests | JSON | list of `{test, method_id, criteria_type, criteria_value, stage, regulatory_basis}` objects |
| version | VARCHAR(10) | e.g. "1.0", "1.1" |
| status | VARCHAR(20) | draft / approved |
| created_at | DATETIME | auto_now_add |

#### `preclinical_studies`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | CASCADE |
| title | VARCHAR(255) | |
| study_type | VARCHAR(30) | in_vitro_mechanistic / in_vitro_admet / in_vivo_pk / in_vivo_efficacy / in_vivo_tox |
| objective | TEXT | |
| species | VARCHAR(50) | nullable; for in vivo studies |
| strain | VARCHAR(100) | nullable |
| dose_levels | JSON | nullable; list of dose values with units |
| route_of_administration | VARCHAR(50) | nullable |
| animals_per_group | INTEGER | nullable |
| primary_endpoints | JSON | list of endpoint names |
| secondary_endpoints | JSON | nullable |
| success_criteria | TEXT | go/no-go thresholds |
| status | VARCHAR(20) | planned / in_progress / completed |
| results_summary | TEXT | |
| conclusion | VARCHAR(20) | go / no_go / inconclusive / null |
| created_at | DATETIME | auto_now_add |

---

## App Pages

---

### 1. Dashboard

**Description:** The landing page. Displays all active projects as cards with phase pipeline indicator and status badge, a recent-experiments feed, pending go/no-go decisions, and quick-action buttons for new project, chat, and compound search.

**External APIs used:** None (local data only)

**Vue Components:**
- `DashboardPage` (page root)
- `ProjectCard` — project name, pathway badge, phase progress dots, status badge, compound count
- `RecentActivityFeed` — chronological experiments, results, and phase decisions across all projects
- `QuickActionPanel` — CTA buttons: New Project, Open Chat, Search Compounds
- `StatsBadge` — numeric chip (active projects, experiments this week)
- `PendingDecisionsList` — projects awaiting a go/no-go gate decision

**Backend APIs:**
- `GET /api/projects/` — list all projects with stats
- `GET /api/experiments/recent/` — last 10 experiments across all projects
- `GET /api/projects/pending-decisions/` — projects where a phase is complete with no recorded decision

**Database Tables:** `projects`, `experiments`, `project_phases`

---

### 2. Project Page

**Description:** Central hub for a single project. Replaces the v1 "Project Setup" page as the primary project view. Shows all content organized by development phase. In edit mode, the scientist can update metadata. Includes a visual phase tracker pipeline at the top showing each phase status. Sections expand per phase: Drug Discovery (analog candidates table), Drug Substance (synthesis plans), Drug Product (formulation summary), Analytical (methods list), Preclinical (ADMET dashboard link, study list), plus all experiments and documents.

**External APIs used:** None (local data only)

**Vue Components:**
- `ProjectPage` (page root, replaces `ProjectSetupPage`)
- `ProjectForm` — project name, description, pathway selector, status selector
- `CompoundSearch` — debounced PubChem/ChEMBL compound name search
- `CompoundPreviewCard` — selected compound: SMILES, MW, formula
- `PhaseTracker` — visual horizontal pipeline; each phase chip is color-coded by status; click opens decision dialog
- `GoNoGoButton` — opens modal to record phase decision (go/no-go + rationale)
- `AnalogCandidateTable` — SMILES, similarity, patent, single-step plan status, multi-step plan status columns
- `SynthesisPlanTable` — plan type, analog, status, step count, actions (Browse, Plan Experiments, Compare)
- `PhaseSectionPanel` — collapsible section wrapper per development phase
- `ExperimentTable` — all experiments with type badge, status, date, view link
- `DocumentList` — documents with type badge and date

**Backend APIs:**
- `POST /api/projects/` — create project
- `GET /api/projects/{id}/` — project detail with nested synthesis plans, analog candidates, investigations
- `PUT /api/projects/{id}/` — update project
- `DELETE /api/projects/{id}/` — delete project and cascade
- `GET /api/projects/{id}/phases/` — list phase records
- `POST /api/projects/{id}/phases/` — create/update phase record
- `GET /api/compounds/search/?q={name}` — compound name search (PubChem + ChEMBL)
- `POST /api/compounds/` — save compound to project
- `GET /api/synthesis-plans/?project={id}` — synthesis plans for project
- `GET /api/experiments/?project_id={id}` — experiments for project
- `GET /api/projects/{id}/documents/` — documents for project

**Database Tables:** `projects`, `project_phases`, `compounds`, `synthesis_plans`, `analog_candidates`, `drug_investigations`, `experiments`, `documents`

---

### 3. Compound Profile

**Description:** Detailed read-only view of a single compound. Displays structure image, physicochemical properties, ADMET predictions, safety/toxicity endpoints, pharmacological targets, and similar compounds. In v2, includes links to the SAR Tracker and ADMET Dashboard for the compound's project.

**External APIs used:**
- **PubChem PUG REST** — 2D structure PNG, SMILES, molecular properties (MW, XLogP, TPSA)
- **pkCSM REST** — ADMET profile from SMILES
- **EPA CompTox Dashboard** — experimental toxicity, Tox21/ToxCast bioassay results
- **ChEMBL REST** — mechanism of action, bioactivity, approval status
- **UniProt REST** — protein targets linked from ChEMBL

**Vue Components:**
- `CompoundProfilePage` (page root)
- `CompoundHeader` — name, ChEMBL ID, PubChem CID, approval badge, pathway to project link
- `MoleculeViewer` — renders 2D structure PNG from PubChem
- `PropertyTable` — key physicochemical values (MW, LogP, TPSA, HBD, HBA, rotatable bonds, Lipinski pass/fail)
- `ADMETCard` — color-coded (green/yellow/red) ADMET endpoint grid (pkCSM)
- `SafetyPanel` — Tox21 active assay count, regulatory flags, GHS hazard codes (EPA CompTox)
- `TargetList` — pharmacological target table with UniProt links and IC50/Ki values
- `SimilarCompoundsList` — fingerprint-similar CIDs as structure mini cards

**Backend APIs:**
- `GET /api/compounds/{id}/` — compound record
- `GET /api/compounds/{id}/properties/` — physicochemical properties (PubChem, cached)
- `GET /api/compounds/{id}/admet/` — ADMET profile (pkCSM, cached)
- `GET /api/compounds/{id}/safety/` — toxicity data (EPA CompTox, cached)
- `GET /api/compounds/{id}/targets/` — pharmacological targets (ChEMBL + UniProt, cached)
- `GET /api/compounds/{id}/structure/` — proxied PNG from PubChem
- `GET /api/compounds/{id}/similar/` — similar compound CIDs (PubChem)
- `GET /api/compounds/{id}/context/` — aggregated context JSON for AI window

**Database Tables:** `compounds`, `compound_properties`, `external_data_cache`

---

### 4. Disease & Target Explorer

**Description:** Disease search and target association page. Scientists search for a disease, see associated protein targets ranked by evidence score, and view known drugs in clinical development. Selecting a target navigates to the full Target Profile page (new in v2). Selecting a known drug navigates to the Drug Profile page.

**External APIs used:**
- **Open Targets Platform GraphQL** — disease summary, target–disease associations, known drugs per indication
- **UniProt REST** — quick protein identity data for the target list

**Vue Components:**
- `DiseaseExplorerPage` (page root)
- `DiseaseSearch` — autocomplete disease name input
- `DiseaseOverviewCard` — disease name, EFO ID, description
- `TargetAssociationTable` — ranked target list with score bars, gene symbols, known drug counts; rows are clickable → `/targets/:uniprot_id`
- `KnownDrugsTable` — drugs in development: name, phase, status; rows are clickable → `/drugs/:chembl_id`

**Backend APIs:**
- `GET /api/diseases/search/?q={term}` — Open Targets disease search (cached)
- `GET /api/diseases/{efo_id}/targets/` — associated targets with evidence scores (cached)
- `GET /api/diseases/{efo_id}/drugs/` — known drugs for indication (cached)

**Database Tables:** `external_data_cache`

---

### 5. Target Profile (NEW)

**Description:** Full biological target detail page. Reached by clicking a target in the Disease Explorer. Displays protein identity, function annotation, tissue expression, PDB structure list, known binding sites, and ChEMBL inhibitors/activators. Two CTA buttons lead to the two development pathways: "Explore Known Drugs" → Drug Intelligence, "Start Virtual Screening" → Virtual Screening.

**External APIs used:**
- **UniProt REST** — protein function, disease associations, tissue expression, sequence length, GO terms
- **RCSB PDB REST** — PDB structure list (resolution, method, deposit date, chain coverage)
- **ChEMBL REST** — known binders with IC50/Ki values, activity types

**Vue Components:**
- `TargetProfilePage` (page root)
- `TargetHeader` — gene symbol, UniProt accession, full protein name, organism, sequence length
- `TargetFunctionCard` — function annotation, GO biological process terms, disease association evidence types
- `TissueExpressionChart` — bar chart of expression levels by tissue (UniProt data)
- `PDBStructureTable` — PDB ID, resolution, experimental method, deposit date; "Use for Screening" action
- `BindingSiteList` — known active sites / allosteric sites from PDB annotations
- `KnownBindersList` — ChEMBL inhibitors with compound name, IC50/Ki, assay type, activity badge
- `PathwayChoicePanel` — two prominent CTAs: "Explore Known Drugs" and "Start Virtual Screening"

**Backend APIs:**
- `GET /api/targets/{uniprot_id}/` — UniProt protein detail (cached)
- `GET /api/targets/{uniprot_id}/structures/` — PDB structure list for this target (cached)
- `GET /api/targets/{uniprot_id}/binding-sites/` — binding site annotations (cached)
- `GET /api/targets/{uniprot_id}/binders/` — ChEMBL known binders (cached)

**Database Tables:** `external_data_cache`

---

### 6. Drug Intelligence

**Description:** Entry point for analog-based development. Scientists search for a known drug by name and land on the Drug Profile page. Standalone search page — the search bar and results list only.

**External APIs used:**
- **ChEMBL REST** — drug name search, approval status

**Vue Components:**
- `DrugIntelligencePage` (page root)
- `DrugSearchInput` — debounced name search with autocomplete
- `DrugSearchResultsList` — result rows: name, approval status, indication, ChEMBL ID; click → `/drugs/:chembl_id`

**Backend APIs:**
- `GET /api/drugs/search/?q={name}` — ChEMBL molecule search (cached)

**Database Tables:** `external_data_cache`

---

### 7. Drug Profile

**Description:** Full reference drug profile assembled from multiple data sources in parallel sections. Used as the intelligence-gathering step before starting an analog search. Contains structure & identity, mechanism of action, formulation details, clinical trial history, synthesis literature, and patent landscape. "Start Analog Search" creates a DrugInvestigation and opens the Analog Workspace.

**External APIs used:**
- **ChEMBL REST** — structure, MW, formula, stereochemistry, mechanism of action
- **Open Targets GraphQL** — target associations, pathway annotation
- **DailyMed REST** — formulation details, inactive ingredients, dosage form, route
- **ClinicalTrials.gov API v2** — trials filtered by drug name as intervention
- **PubMed E-utilities** — synthesis literature (`{drug_name} synthesis route`)
- **SureChEMBL REST** — patents covering the molecule, formulation, or process
- **Espacenet OPS REST** — full patent claim text on demand

**Vue Components:**
- `DrugProfilePage` (page root)
- `DrugIdentityCard` — structure image, SMILES, InChI key, formula, MW, approval badge
- `MechanismOfActionCard` — target name, pathway, mechanism description
- `FormulationDetailsCard` — inactive ingredients, dosage form, route, excipients (DailyMed)
- `ClinicalTrialsList` — trials table: phase, status, enrollment, primary outcome
- `SynthesisLiteratureList` — PubMed articles: title, authors, journal, abstract excerpt
- `PatentLandscapeTable` — patent number, title, assignee, filing date, expiry (derived), jurisdiction; "View Claims" action

**Backend APIs:**
- `GET /api/drugs/{chembl_id}/` — aggregated drug profile (ChEMBL + DailyMed, cached)
- `GET /api/drugs/{chembl_id}/synthesis/` — PubMed synthesis articles (cached)
- `GET /api/drugs/{chembl_id}/trials/` — ClinicalTrials.gov filtered by drug (cached)
- `GET /api/drugs/{chembl_id}/patents/` — SureChEMBL patent list (cached)
- `GET /api/patents/{patent_number}/` — Espacenet full patent (cached)
- `POST /api/investigations/` — create DrugInvestigation record

**Database Tables:** `drug_investigations`, `external_data_cache`

---

### 8. Patent Explorer

**Description:** Standalone patent search page. Supports search by drug name or SMILES structure. Results show patent number, title, assignee, filing date, derived expiry, and jurisdiction. "View Claims" fetches full text. "Flag for Project" links a patent as a risk factor.

**External APIs used:**
- **SureChEMBL REST** — structure-searchable patent compound registry
- **Espacenet OPS REST** — full patent text and claims

**Vue Components:**
- `PatentExplorerPage` (page root)
- `PatentSearchForm` — toggle: name search vs SMILES paste; search button
- `PatentResultsTable` — patent number, title, assignee, filing date, expiry, jurisdiction; "View Claims" and "Flag" actions
- `PatentClaimsDrawer` — slide-in panel showing full claim text from Espacenet

**Backend APIs:**
- `GET /api/patents/?q={name_or_smiles}&mode={name|smiles}` — SureChEMBL search (cached)
- `GET /api/patents/{patent_number}/` — Espacenet full patent (cached)

**Database Tables:** `external_data_cache`

---

### 9. Virtual Screening (NEW)

**Description:** Enables hit identification for novel drug design. The scientist configures a protein target (PDB structure + binding site), selects a compound library, submits a docking run, then reviews and shortlists top hits. Docking runs are asynchronous — the page polls status until complete. Shortlisted hits can be saved to a project or passed to the Analog Workspace.

**External APIs used:**
- **RCSB PDB REST** — protein structure retrieval by PDB ID
- **AutoDock Vina** (local subprocess) — molecular docking engine
- **ZINC20 REST** — FDA-approved and clinical candidate compound library subsets
- **pkCSM REST** — ADMET predictions for shortlisted hits
- **SureChEMBL REST** — patent coverage check for hits

**Vue Components:**
- `VirtualScreeningPage` (page root)
- `TargetSetupPanel` — PDB ID input or selector from Target Profile; binding site definition (center + size box or residue range)
- `LibrarySelector` — radio: FDA Approved / Clinical Candidates / Fragments / Custom SMILES upload
- `DockingJobStatus` — polling progress indicator: pending → running (with elapsed time) → complete → failed
- `HitResultsTable` — sorted by docking score; columns: SMILES thumbnail, compound name, docking score, Lipinski badge, patent badge; per-row "Check ADMET" and shortlist toggle
- `HitDetailCard` — slide-in panel: 3D pose image (if available), SMILES, docking score, ADMET summary
- `ScreeningShortlistPanel` — pinned hits with bulk "Save to Project" CTA

**Backend APIs:**
- `POST /api/virtual-screening/runs/` — create screening run record; triggers async docking job
- `GET /api/virtual-screening/runs/{id}/` — poll run status and metadata
- `GET /api/virtual-screening/runs/{id}/hits/` — paginated hit list sorted by docking score
- `PATCH /api/virtual-screening/hits/{id}/` — shortlist / unshortlist a hit; trigger ADMET or patent check

**Database Tables:** `target_profiles`, `virtual_screening_runs`, `virtual_screening_hits`, `external_data_cache`

---

### 10. Analog Workspace

**Description:** Starting from a reference drug's SMILES, finds structurally similar compounds that avoid the drug's patents. Three-panel layout: Reference Drug → Candidate Pool → Shortlist. Operates in two modes: drug-search mode (full workflow) and project mode (pre-loaded analogs for an existing project).

**External APIs used:**
- **PubChem PUG REST** — fingerprint similarity search, structure thumbnails
- **SureChEMBL REST** — parallel patent coverage check per candidate
- **pkCSM REST** — batch ADMET predictions

**Vue Components:**
- `AnalogWorkspacePage` (page root)
- `ReferenceDrugPanel` — reference SMILES, 2D structure image, key properties, similarity threshold slider
- `CandidatePoolPanel` — grid of candidates: structure thumbnail, PubChem CID, similarity score, patent badge, ADMET traffic light
- `ShortlistPanel` — pinned candidates, side-by-side ADMET comparison table (rows = endpoints, columns = candidates + reference), project selector, "Save to Project" CTA
- `PatentCheckProgress` — bulk patent check progress bar
- `ADMETRunProgress` — bulk ADMET prediction progress bar
- `ProjectModeModeBanner` — blue banner identifying project mode; shows current project name

**Backend APIs:**
- `POST /api/analogs/search/` — PubChem similarity search from reference SMILES
- `POST /api/analogs/patent-check/` — parallel SureChEMBL patent check for candidate list
- `POST /api/analogs/admet/` — parallel pkCSM ADMET predictions for SMILES list
- `GET /api/investigations/` — list existing investigations
- `POST /api/investigations/` — create DrugInvestigation record
- `GET /api/investigations/{id}/` — load investigation with candidates
- `POST /api/investigations/{id}/candidates/` — add candidate to investigation
- `PATCH /api/analog-candidates/{id}/` — shortlist toggle (immediate PATCH in project mode)
- `POST /api/investigations/{id}/link-project/` — link investigation + shortlisted candidates to project

**Database Tables:** `drug_investigations`, `analog_candidates`, `external_data_cache`

---

### 11. SAR Tracker (NEW)

**Description:** Structure-Activity Relationship log for a project. Scientists record which structural modifications to analog candidates improved or worsened specific properties. Entries are shown in a sortable table and a heatmap matrix. The SAR log builds a structured evidence base that the AI will later query to summarize what drives potency, selectivity, or ADMET.

**External APIs used:** None (local data only)

**Vue Components:**
- `SARTrackerPage` (page root)
- `SAREntryForm` — compound picker (project candidates), parent compound picker, property selector dropdown, value + unit inputs, assay method textarea, verdict selector, rationale
- `SARDataTable` — all entries sortable/filterable by property, verdict, compound; columns: compound, modification, property, value, verdict badge, date
- `SARHeatmap` — compounds (rows) × properties (columns) matrix; cells colored green/yellow/red/grey by verdict

**Backend APIs:**
- `GET /api/projects/{id}/sar/` — list SAR entries for project
- `POST /api/projects/{id}/sar/` — create SAR entry
- `GET /api/sar-entries/{id}/` — detail
- `DELETE /api/sar-entries/{id}/` — delete entry

**Database Tables:** `sar_entries`, `compounds`, `experiments`

---

### 12. Candidate Selection (NEW)

**Description:** Go/no-go gate page before Drug Substance Development. Shows all shortlisted analog candidates side by side with ADMET flags, SAR verdict counts, patent status, and buyability. The scientist selects one compound as the development candidate, records a rationale, and clicks "Select" — which locks the compound to the project and advances the Lead Optimization phase to "complete."

**External APIs used:** None (local data only)

**Vue Components:**
- `CandidateSelectionPage` (page root)
- `CandidateComparisonTable` — one column per candidate: structure image, SMILES, similarity, patent badge, ADMET flag count, SAR verdict summary, buyability badge
- `SelectionForm` — rationale textarea + "Select as Development Candidate" confirm button
- `SelectedCompoundBadge` — shown if a candidate has already been selected; includes "Change Selection" action

**Backend APIs:**
- `GET /api/projects/{id}/` — project detail with analog candidates and SAR entries
- `POST /api/projects/{id}/phases/` — update Lead Optimization phase to complete with go decision
- `POST /api/compounds/` — lock selected compound as project's primary compound

**Database Tables:** `projects`, `project_phases`, `analog_candidates`, `sar_entries`, `compounds`

---

### 13. Synthesis Planning

**Description:** Computer-aided synthesis planning. The scientist enters a target SMILES and runs single-step or multi-step retrosynthesis. Results appear as an interactive retrosynthesis tree with inline reaction conditions per step. Each starting material has a buyability check. Auto-runs and auto-saves when redirected from the project page. Forward Prediction is available in a collapsed Advanced Tools section.

**External APIs used:**
- **ASKCOS** (local RDKit service) — single-step retrosynthesis, multi-step tree, forward prediction, condition recommendation, buyability heuristic
- **NIST WebBook** — IR/MS reference spectra for starting materials (by CAS)

**Vue Components:**
- `SynthesisPlanningPage` (page root)
- `SynthesisInput` — SMILES input with structure validation indicator; locked display when analog is pre-loaded
- `LockedContextPanel` — shown when navigating from project: analog SMILES, reference drug, project name
- `AnalysisTypeToggle` — Single-Step / Multi-Step selector; individual button disabled when `?type` is locked
- `ReactionStepCard` — transform name, forward description, precursor SMILES structure image, reaction conditions box (reagents, solvent, temp, time), "Check Availability" button per precursor
- `SynthesisTreeNode` — recursive component for multi-step tree rendering
- `BuyableCheck` — inline badge: ✓ Available (green) / ✗ Custom synthesis (red)
- `ConditionBox` — reagents, solvent, temperature, time inline below each step card
- `ForwardPredictionPanel` — collapsed in Advanced Tools; reactant SMILES inputs, predicted product display
- `SpectraViewer` — NIST IR/MS spectrum plot (JCAMP-DX parsed client-side)
- `ProjectPicker` — dropdown shown when no `?project` param; lists all projects

**Backend APIs:**
- `POST /api/synthesis/retro/` — single-step retrosynthesis (ASKCOS)
- `POST /api/synthesis/tree/` — multi-step tree (ASKCOS)
- `POST /api/synthesis/forward/` — forward reaction prediction (ASKCOS)
- `POST /api/synthesis/conditions/` — reaction condition recommendation (ASKCOS)
- `GET /api/synthesis/buyables/?smiles={smiles}` — buyability check
- `GET /api/compounds/spectra/?cas={cas}&type={ir|ms}` — spectral reference (NIST WebBook)
- `GET /api/synthesis-plans/?project={id}&analog={id}` — load existing plans
- `POST /api/synthesis-plans/` — create synthesis plan record
- `GET /api/synthesis-plans/{id}/` — load existing plan by ID

**Database Tables:** `synthesis_plans`, `analog_candidates`, `external_data_cache`

---

### 14. Synthesis Plan Comparison

**Description:** Side-by-side comparison of two or more synthesis plans. Accessed from the project page by selecting multiple plan rows and clicking Compare. Shows structure image, plan type, status, step count, and full route detail in parallel columns.

**External APIs used:** None (local data only)

**Vue Components:**
- `SynthesisPlanComparisonPage` (page root)
- `PlanComparisonHeader` — one card per plan: type badge, status, target SMILES, structure image, step count, creation date
- `PlanRouteColumn` — full route detail per plan: retro step cards or recursive tree via `SynthesisTreeNode`

**Backend APIs:**
- `GET /api/synthesis-plans/{id}/` — fetch each plan by ID (parallel)

**Database Tables:** `synthesis_plans`

---

### 15. Salt & Polymorph Screening (NEW)

**Description:** Plans and tracks a solid-form screening campaign. The scientist defines the objective, selects counterions or coformers, auto-generates the experiment matrix, logs characterization results (XRPD, DSC, TGA), and selects the preferred solid form. One screen per project.

**External APIs used:**
- **PubChem PUG REST** — pKa data for the API
- **OpenFDA** — approved pharmaceutical salt former and excipient list

**Vue Components:**
- `SaltPolymorphScreeningPage` (page root)
- `ScreenObjectiveForm` — objective textarea, baseline pKa, baseline melting point inputs
- `SaltFormerSearch` — searchable counterion list from OpenFDA; shows pKa delta and expected solubility impact per entry
- `ScreeningMatrixTable` — auto-generated experiment list: API form × counterion × solvent × prep method
- `SaltScreenResultsTable` — per-experiment results: observed form badge, XRPD/DSC/TGA text summaries
- `FormSelectionPanel` — solubility/MP/hygroscopicity comparison table across all observed forms; "Lock Preferred Form" button

**Backend APIs:**
- `GET /api/projects/{id}/salt-screening/` — get screen record for project
- `POST /api/projects/{id}/salt-screening/` — create screen
- `PATCH /api/salt-screens/{id}/` — update screen (including locking selected form)
- `GET /api/salt-screens/{id}/candidates/` — list salt former candidates
- `POST /api/salt-screens/{id}/candidates/` — add salt former candidate
- `POST /api/salt-screen-candidates/{id}/experiments/` — log experiment result
- `GET /api/salt-screen-candidates/{id}/experiments/` — list experiments

**Database Tables:** `salt_polymorph_screens`, `salt_screen_candidates`, `salt_screen_experiments`, `external_data_cache`

---

### 16. Process Development & Scale-Up (NEW)

**Description:** Translates a bench-scale synthesis route into a manufacturable process. Linked to a SynthesisPlan, the scientist documents critical process parameters (CPPs), critical quality attributes (CQAs), scale-up milestones (lab → pilot → manufacturing), and impurity profiles.

**External APIs used:** None (local data only)

**Vue Components:**
- `ProcessDevelopmentPage` (page root)
- `SynthesisRoutePicker` — dropdown of SynthesisPlan records for the project
- `CPPDocumentationAccordion` — one accordion panel per synthesis step: CPPs form (time, temp, agitation, addition order, equivalents), CQAs form (purity, yield, solvents, particle size), PAT notes
- `ScaleUpMilestoneTable` — editable rows for lab / pilot / manufacturing stages: target batch size, equipment, expected yield, go/no-go criteria
- `ImpurityProfileTable` — editable rows: impurity name, type (SM carryover / by-product / degradation), ICH class, limit, control strategy

**Backend APIs:**
- `GET /api/synthesis-plans/?project={id}` — list synthesis plans to pick from
- `GET /api/projects/{id}/process-development/` — get process development record
- `POST /api/projects/{id}/process-development/` — create record
- `PUT /api/process-developments/{id}/` — update record

**Database Tables:** `synthesis_plans`, `projects` (process_development data stored as JSON on project or new `process_developments` table — see implementation note)

---

### 17. Formulation Planning (NEW)

**Description:** Designs the drug product formulation. The scientist selects dosage form and release type, builds the excipient composition by selecting from the Excipient Library, views IIG compliance per component, and triggers a compatibility assessment. The page maintains one FormulationPlan per project.

**External APIs used:**
- **OpenFDA** — IIG limit lookup for selected excipients at the chosen route of administration

**Vue Components:**
- `FormulationPlanningPage` (page root)
- `DosageFormSelector` — dosage form dropdown, route selector, target dose input, release type, patient population notes
- `ExcipientBuilder` — dynamic row list: excipient name picker (searches ExcipientLibrary), function selector, mg input, %w/w auto-calculated, rationale text; "Add Row" button
- `IIGComplianceBadge` — green (compliant) / red (overage) badge per component row; shows IIG max inline
- `CompatibilityFlagList` — risk-level-colored flags (low/medium/high/critical); high and critical show mandatory rationale input
- `FormulationSummaryTable` — read-only composition table: ingredient, role, mg/unit, %w/w, IIG compliance, grade spec
- `ManufacturingProcessForm` — granulation method selector, coating notes, fill/finish notes

**Backend APIs:**
- `GET /api/projects/{id}/formulation/` — get formulation plan for project
- `POST /api/projects/{id}/formulation/` — create formulation plan
- `PUT /api/formulation-plans/{id}/` — update plan metadata
- `GET /api/formulation-plans/{id}/components/` — list components
- `POST /api/formulation-plans/{id}/components/` — add component
- `DELETE /api/formulation-components/{id}/` — remove component
- `POST /api/formulation-plans/{id}/check-compatibility/` — run compatibility check; creates CompatibilityFlag records
- `GET /api/formulation-plans/{id}/context/` — aggregated AI context

**Database Tables:** `formulation_plans`, `formulation_components`, `compatibility_flags`, `excipients`, `external_data_cache`

---

### 18. Excipient Library (NEW)

**Description:** Global searchable reference database of pharmaceutical excipients. Scientists search by name, function, or route to find IIG limits, GRAS status, incompatibilities, and monograph references. The library is seeded from FDA IIG data and a curated CSV — scientists browse but do not create records.

**External APIs used:** None (data is seeded; no live API calls)

**Vue Components:**
- `ExcipientLibraryPage` (page root)
- `ExcipientSearch` — text search + function filter chips + route filter dropdown
- `ExcipientResultsList` — card list with name, CAS, function badges, IIG limit summary
- `ExcipientDetailDrawer` — slide-in: full record including synonyms, all IIG limits by route, GRAS status, incompatibilities, USP/Ph. Eur. monograph reference

**Backend APIs:**
- `GET /api/excipients/?q={name}&function={fn}&route={route}` — search excipient library
- `GET /api/excipients/{id}/` — excipient detail

**Database Tables:** `excipients`

---

### 19. Stability Planning (NEW)

**Description:** Designs, tracks, and summarizes ICH-guideline stability studies for drug substance or drug product. The scientist builds a study matrix (conditions × timepoints × tests), logs results at each timepoint, and reviews trend charts with OOS/OOT flags.

**External APIs used:** None (ICH guideline data is hardcoded in service layer)

**Vue Components:**
- `StabilityPlanningPage` (page root)
- `StabilityObjectiveForm` — material type selector (DS/DP), intended storage condition input
- `StabilityMatrixBuilder` — condition checklist (long-term, intermediate, accelerated, etc.); per-condition timepoint configurator and test selector; total sample count calculator
- `StabilityResultsEntry` — per-condition/timepoint form: one field per selected test; OOS flag shown inline if value fails acceptance criterion
- `StabilityTrendChart` — line chart per test across timepoints per condition; OOS points highlighted in red
- `OOSFlagList` — list of all OOS and OOT flags with condition, timepoint, test, and observed value

**Backend APIs:**
- `GET /api/projects/{id}/stability/` — get stability plan for project
- `POST /api/projects/{id}/stability/` — create stability plan
- `GET /api/stability-plans/{id}/conditions/` — list conditions
- `POST /api/stability-plans/{id}/conditions/` — add condition (with timepoints and tests)
- `GET /api/stability-conditions/{id}/results/` — list results
- `POST /api/stability-conditions/{id}/results/` — log result for a timepoint
- `GET /api/stability-plans/{id}/context/` — aggregated AI context

**Database Tables:** `stability_plans`, `stability_conditions`, `stability_results`

---

### 20. Analytical Method Development (NEW)

**Description:** Plans and tracks development of analytical characterization methods. Each method has a type, purpose, development experiment log, final validated parameters, and an ICH Q2(R1) validation checklist. One page instance per method; a method list page shows all methods for a project.

**External APIs used:** None (local data only)

**Vue Components:**
- `AnalyticalMethodPage` (page root; also serves as list when no `method_id` param)
- `AnalyticalMethodList` — list of all methods for the project with status badges; "New Method" button
- `MethodDefinitionForm` — method name, type, purpose, analytes, instrument type, reference standards required
- `DevelopmentExperimentLog` — chronological list of dev experiments: column/conditions used, key chromatographic parameters observed, verdict badge
- `FinalParametersPanel` — settled method parameters displayed as a specification card: column, mobile phase, gradient, flow rate, wavelength, runtime, LOD, LOQ
- `ValidationChecklist` — ICH Q2(R1) characteristics checklist: specificity, linearity, range, accuracy, precision, LOD, LOQ, robustness — each with planned / done / pass / fail status

**Backend APIs:**
- `GET /api/projects/{id}/analytical-methods/` — list all methods
- `POST /api/projects/{id}/analytical-methods/` — create method
- `GET /api/analytical-methods/{id}/` — method detail
- `PUT /api/analytical-methods/{id}/` — update method (parameters, status)
- `DELETE /api/analytical-methods/{id}/` — delete method

**Database Tables:** `analytical_methods`, `experiments`

---

### 21. Specification Builder (NEW)

**Description:** Defines release and shelf-life specifications for the drug substance or drug product. Each test row references an analytical method, defines acceptance criteria, specifies stage (release / shelf-life) and regulatory basis. The full specification sheet can be exported as a regulatory-format table.

**External APIs used:** None (local data only)

**Vue Components:**
- `SpecificationBuilderPage` (page root)
- `MaterialTypeToggle` — drug substance / drug product
- `SpecificationTestRow` — test name, method picker (from analytical methods list), criteria type selector (NMT / NLT / between / conforms to), value inputs, stage, regulatory basis
- `SpecificationTable` — read-only assembled specification sheet; sortable by stage
- `ExportSpecButton` — triggers formatted table download (PDF or CSV)

**Backend APIs:**
- `GET /api/projects/{id}/specifications/` — get specification records (by material type)
- `POST /api/projects/{id}/specifications/` — create specification
- `PUT /api/specifications/{id}/` — update specification (add/remove tests)
- `POST /api/specifications/{id}/export/` — export formatted specification table

**Database Tables:** `specifications`, `analytical_methods`

---

### 22. Preclinical Study Planner (NEW)

**Description:** Plans and tracks non-clinical studies (in vitro and in vivo). The scientist creates study records with objectives, species, dose levels, endpoints, and success criteria, then logs results and conclusions. The page shows all studies for the project organized by study type.

**External APIs used:** None (local data only)

**Vue Components:**
- `PreclinicalStudyPlannerPage` (page root)
- `StudyTypeFilter` — tab or chip filter: All / In Vitro / In Vivo PK / Efficacy / Tox
- `StudyList` — card list: type badge, status badge, title, objective excerpt, conclusion badge when complete
- `StudyForm` — study title, type, objective, species/strain (conditional), dose levels, ROA, animals per group, primary + secondary endpoints, success criteria
- `StudyResultsForm` — results summary textarea, conclusion selector (go/no-go/inconclusive)
- `StudyDetailDrawer` — slide-in panel showing full study record and results

**Backend APIs:**
- `GET /api/projects/{id}/preclinical-studies/` — list studies
- `POST /api/projects/{id}/preclinical-studies/` — create study
- `GET /api/preclinical-studies/{id}/` — study detail
- `PUT /api/preclinical-studies/{id}/` — update study (results and conclusion)
- `GET /api/preclinical-studies/{id}/context/` — AI context for this study

**Database Tables:** `preclinical_studies`, `experiments`

---

### 23. ADMET Dashboard (NEW)

**Description:** Unified ADMET view for a project's compound. Combines computational predictions (pkCSM) and experimental measurements (from preclinical study results). Scientist-defined benchmarks are compared against both sources. Any endpoint with an experimental value overrides the computational prediction with a "Measured" badge.

**External APIs used:**
- **pkCSM REST** — ADMET predictions if not yet cached for this compound

**Vue Components:**
- `ADMETDashboardPage` (page root)
- `ComputationalADMETPanel` — pkCSM predictions in a color-coded grid (green/yellow/red per endpoint)
- `ExperimentalADMETPanel` — measured values from preclinical study logs; "Measured" badge; source study link
- `BenchmarkComparisonTable` — rows per endpoint: benchmark target range vs computational vs experimental; met/at-risk/failed chip
- `BenchmarkEditForm` — scientist defines target range per endpoint; saved per project
- `ADMETRadarChart` — spider chart normalized by endpoint benchmark; visual overall profile

**Backend APIs:**
- `GET /api/projects/{id}/admet-dashboard/` — aggregated ADMET data: computational (pkCSM) + experimental (from preclinical study results) + benchmarks
- `POST /api/projects/{id}/admet-benchmarks/` — save scientist-defined benchmark targets
- `GET /api/compounds/{id}/admet/` — refresh pkCSM predictions

**Database Tables:** `compounds`, `compound_properties`, `preclinical_studies`, `external_data_cache`

---

### 24. Experiment Planner

**Description:** Structured form for designing a new experiment. The scientist selects the experiment type (synthesis, formulation, analytical, stability, preclinical), states the objective, defines variable parameters, and sets success criteria. For synthesis experiments, an inline ASKCOS retrosynthesis preview is shown. For formulation experiments, excipient suggestions appear. In v2, experiments can be linked to a FormulationPlan or PreclinicalStudy in addition to Compounds and SynthesisPlans.

**External APIs used:**
- **ASKCOS** (local RDKit) — inline retrosynthesis preview for synthesis experiments
- **OpenFDA** — excipient suggestions for formulation experiments

**Vue Components:**
- `ExperimentPlannerPage` (page root)
- `ExperimentForm` — type selector, objective textarea, project/compound pickers, synthesis plan picker, formulation plan picker (v2 new), preclinical study picker (v2 new)
- `VariableBuilder` — dynamic row list: variable name, unit, range (min/max), control value
- `SuccessCriteriaPanel` — structured + free-text success criteria input
- `RetrosynPreview` — compact top-3 ASKCOS precursor candidates (synthesis type only)
- `ExcipientSuggestion` — common inactive ingredients for the dosage form (formulation type only)

**Backend APIs:**
- `POST /api/experiments/` — create experiment record
- `GET /api/experiments/{id}/` — retrieve experiment
- `PUT /api/experiments/{id}/` — update experiment
- `POST /api/synthesis/retro/` — inline retrosynthesis preview (ASKCOS)
- `GET /api/regulatory/excipients/?form={dosage_form}` — excipient suggestions

**Database Tables:** `experiments`, `external_data_cache`

---

### 25. Experiment Results

**Description:** Data entry and review for a planned experiment. Scientists enter key metric values and observations. The Claude AI generates an interpretation comparing results to success criteria and recommends a decision. Historical results are shown in a timeline with trend charts.

**External APIs used:**
- **Claude API** — AI interpretation of results in the context of objectives and success criteria

**Vue Components:**
- `ExperimentResultsPage` (page root)
- `ResultsForm` — dynamic metric fields matching experiment variables + free-text observations
- `AIInterpretation` — streamed Claude response below submitted results
- `DecisionPanel` — four-button selector: Optimize / Reproduce / Scale / Abort
- `ResultsTimeline` — chronological list of prior submissions
- `ResultsChart` — line/bar chart of key metrics across submissions

**Backend APIs:**
- `GET /api/experiments/{id}/` — experiment metadata and success criteria
- `GET /api/experiments/{id}/results/` — all results for this experiment
- `POST /api/experiments/{id}/results/` — log a result set
- `POST /api/experiments/{id}/interpret/` — trigger Claude AI interpretation (streamed)

**Database Tables:** `experiments`, `experiment_results`

---

### 26. Risk Analysis

**Description:** Project-level risk dashboard. Displays a 2D heat map (probability vs impact) with risk factors spanning scientific/technical, preclinical, IP/regulatory, and operational categories. AI-generated or manually edited.

**External APIs used:**
- **ClinicalTrials.gov API v2** — clinical precedent for the indication
- **PubMed E-utilities** — safety and scale-up literature
- **OpenFDA** — relevant FDA guidance documents
- **Claude API** — AI-generated risk factor list from project context

**Vue Components:**
- `RiskAnalysisPage` (page root)
- `RiskHeatMap` — SVG 5×5 probability–impact grid with draggable risk markers; color-coded by risk level
- `RiskFactorList` — editable list: category, probability, impact, mitigation strategy, owner
- `RegulatorySummary` — matched FDA guidance document cards with title and PDF link
- `ClinicalPrecedentCard` — trial count and phase breakdown for the indication
- `GenerateRiskBtn` — triggers AI risk assessment generation

**Backend APIs:**
- `GET /api/projects/{id}/risk-assessment/` — current risk assessment
- `POST /api/projects/{id}/risk-assessment/` — save manual assessment
- `POST /api/projects/{id}/risk-assessment/generate/` — AI-generated assessment (Claude, streamed)
- `GET /api/trials/search/?condition={cond}&intervention={drug}` — clinical precedent
- `GET /api/literature/search/?q={query}` — safety literature (PubMed)
- `GET /api/regulatory/guidance/?q={topic}` — FDA guidance (OpenFDA)

**Database Tables:** `risk_assessments`, `projects`, `compounds`, `external_data_cache`

---

### 27. Literature & Clinical Trials

**Description:** Unified search for biomedical literature, clinical trials, and patents. Three tabs: Literature (PubMed), Clinical Trials (ClinicalTrials.gov), and Patents (SureChEMBL + Espacenet). Results can be saved as project references.

**External APIs used:**
- **PubMed E-utilities** — ESearch, ESummary, EFetch
- **ClinicalTrials.gov API v2** — search and detail
- **SureChEMBL REST** — patent search by name or SMILES
- **Espacenet OPS REST** — patent claim text

**Vue Components:**
- `LiteraturePage` (page root — three tabs)
- `LiteratureSearch` — PubMed query with field selectors (title, abstract, author)
- `ArticleCard` — title, authors, journal, date, abstract excerpt, PubMed link, Save to Project button
- `TrialSearch` — condition + intervention inputs, phase and status filters
- `TrialCard` — NCT ID, title, phase, status, enrollment, primary outcome
- `PatentSearchBar` — name or SMILES search with mode toggle (reuses PatentExplorer logic)
- `PatentResultRow` — patent number, title, assignee, expiry; "View Claims" action

**Backend APIs:**
- `GET /api/literature/search/?q={query}&max={n}` — PubMed search (cached)
- `GET /api/literature/{pmid}/` — article abstract (cached)
- `GET /api/trials/search/?condition={c}&intervention={i}&phase={p}` — trial search (cached)
- `GET /api/trials/{nct_id}/` — trial detail (cached)
- `GET /api/patents/?q={query}&mode={name|smiles}` — patent search (cached)
- `GET /api/patents/{patent_number}/` — patent claims (Espacenet, cached)

**Database Tables:** `external_data_cache`

---

### 28. AI Chat Assistant

**Description:** Per-project and global persistent chat powered by Claude. Uses tool-calling to query all integrated external APIs on demand. All responses cite data sources. Sessions are saved per project.

**External APIs used:**
- **Claude API** — multi-turn conversation with tool use
- **All 20+ external APIs** — invoked dynamically as Claude tool calls

**Vue Components:**
- `ChatPage` (page root)
- `SessionList` — sidebar of saved sessions for the project
- `ChatInterface` — scrollable message history + input bar
- `MessageBubble` — single message with role indicator, timestamp
- `SourceCitation` — collapsible API source list on assistant messages
- `MarkdownRenderer` — renders Claude's markdown responses
- `SuggestedQueries` — example questions on empty session state
- `StreamingIndicator` — animated typing indicator while Claude responds

**Backend APIs:**
- `GET /api/chat/sessions/` — list sessions (filtered by project_id if provided)
- `POST /api/chat/sessions/` — create session
- `GET /api/chat/sessions/{id}/` — session with full message history
- `POST /api/chat/sessions/{id}/messages/` — send message; stream Claude response
- `DELETE /api/chat/sessions/{id}/` — delete session

**Database Tables:** `chat_sessions`, `chat_messages`, `external_data_cache`

---

### 29. Process Documentation

**Description:** Document generation and editing page. Supports 9 document types. Claude pre-populates a Markdown draft using project data. The scientist can edit inline and export as PDF or DOCX.

**External APIs used:**
- **Claude API** — document drafting from project context
- **DailyMed REST** — drug labeling language for regulatory sections
- **OpenFDA** — FDA guidance citations

**Vue Components:**
- `DocumentationPage` (page root)
- `DocumentList` — saved documents with type badge, status, date
- `DocumentEditor` — Markdown editor (CodeMirror) for inline editing
- `SectionBuilder` — collapsible section panels per document type
- `GenerateDocBtn` — triggers AI draft generation
- `ExportPanel` — PDF / DOCX format selector and download button

**Backend APIs:**
- `GET /api/projects/{id}/documents/` — list documents
- `POST /api/projects/{id}/documents/generate/` — AI-drafted document (Claude, streamed)
- `POST /api/projects/{id}/documents/` — save manual document
- `GET /api/documents/{id}/` — retrieve document
- `PUT /api/documents/{id}/` — update document
- `POST /api/documents/{id}/export/` — export as PDF or DOCX

**Database Tables:** `documents`, `projects`, `experiments`, `risk_assessments`, `formulation_plans`, `stability_plans`, `synthesis_plans`, `external_data_cache`

---

## Backend API List

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/login/` | Obtain session token |
| POST | `/api/auth/logout/` | Invalidate session |
| GET | `/api/auth/me/` | Current user info |

### Projects
| Method | Endpoint | Description | DB Tables |
|---|---|---|---|
| GET | `/api/projects/` | List all projects with stats | projects, experiments, project_phases |
| POST | `/api/projects/` | Create new project | projects |
| GET | `/api/projects/{id}/` | Project detail with nested data | projects, compounds, synthesis_plans, analog_candidates |
| PUT | `/api/projects/{id}/` | Update project | projects |
| DELETE | `/api/projects/{id}/` | Delete project and cascade | projects, … |
| GET | `/api/projects/pending-decisions/` | Projects awaiting a phase gate decision | project_phases |
| GET | `/api/projects/{id}/phases/` | List phase records for project | project_phases |
| POST | `/api/projects/{id}/phases/` | Create or update a phase record | project_phases |
| PATCH | `/api/projects/{id}/phases/{phase}/` | Update specific phase status or decision | project_phases |
| GET | `/api/projects/{id}/context/` | Full project context for AI window | projects, compounds, synthesis_plans, formulation_plans, … |

### Compounds
| Method | Endpoint | Description | External APIs |
|---|---|---|---|
| GET | `/api/compounds/search/?q={name}` | Search compound by name | PubChem, ChEMBL |
| POST | `/api/compounds/` | Save compound to project | — |
| GET | `/api/compounds/{id}/` | Compound record | — |
| DELETE | `/api/compounds/{id}/` | Delete compound | — |
| GET | `/api/compounds/{id}/properties/` | Physicochemical properties | PubChem |
| GET | `/api/compounds/{id}/admet/` | ADMET profile | pkCSM |
| GET | `/api/compounds/{id}/safety/` | Toxicity/hazard data | EPA CompTox |
| GET | `/api/compounds/{id}/targets/` | Pharmacological targets | ChEMBL, UniProt |
| GET | `/api/compounds/{id}/structure/` | 2D structure PNG (proxied) | PubChem |
| GET | `/api/compounds/{id}/similar/` | Fingerprint-similar CIDs | PubChem |
| GET | `/api/compounds/spectra/?cas={cas}&type={type}` | IR/MS spectra (JCAMP-DX) | NIST WebBook |
| GET | `/api/compounds/{id}/context/` | Compound context for AI window | — |

### Diseases & Targets
| Method | Endpoint | Description | External APIs |
|---|---|---|---|
| GET | `/api/diseases/search/?q={term}` | Disease search | Open Targets |
| GET | `/api/diseases/{efo_id}/targets/` | Target–disease associations | Open Targets |
| GET | `/api/diseases/{efo_id}/drugs/` | Known drugs for indication | Open Targets |
| GET | `/api/targets/{uniprot_id}/` | Protein detail | UniProt |
| GET | `/api/targets/{uniprot_id}/structures/` | PDB structures for target | RCSB PDB |
| GET | `/api/targets/{uniprot_id}/binding-sites/` | Binding site annotations | RCSB PDB |
| GET | `/api/targets/{uniprot_id}/binders/` | Known ChEMBL inhibitors/activators | ChEMBL |

### Virtual Screening
| Method | Endpoint | Description | External APIs |
|---|---|---|---|
| POST | `/api/virtual-screening/runs/` | Create run; triggers async docking | AutoDock Vina, ZINC |
| GET | `/api/virtual-screening/runs/{id}/` | Poll run status and metadata | — |
| GET | `/api/virtual-screening/runs/{id}/hits/` | Paginated hit list sorted by score | — |
| PATCH | `/api/virtual-screening/hits/{id}/` | Shortlist toggle; trigger ADMET or patent check | pkCSM, SureChEMBL |

### Experiments
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/experiments/recent/` | Last 10 experiments across all projects |
| GET | `/api/experiments/?project_id={id}` | Experiments for a project |
| POST | `/api/experiments/` | Create experiment |
| GET | `/api/experiments/{id}/` | Experiment detail |
| PUT | `/api/experiments/{id}/` | Update experiment |
| GET | `/api/experiments/{id}/results/` | All results for experiment |
| POST | `/api/experiments/{id}/results/` | Log a result set |
| POST | `/api/experiments/{id}/interpret/` | AI interpretation (Claude, streamed) |

### SAR Entries
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/projects/{id}/sar/` | List SAR entries for project |
| POST | `/api/projects/{id}/sar/` | Create SAR entry |
| GET | `/api/sar-entries/{id}/` | SAR entry detail |
| DELETE | `/api/sar-entries/{id}/` | Delete entry |

### Risk Assessment
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/projects/{id}/risk-assessment/` | Current risk assessment |
| POST | `/api/projects/{id}/risk-assessment/` | Save manual assessment |
| POST | `/api/projects/{id}/risk-assessment/generate/` | AI-generated assessment (Claude, streamed) |

### Synthesis Planning
| Method | Endpoint | Description | External APIs |
|---|---|---|---|
| POST | `/api/synthesis/retro/` | Single-step retrosynthesis | ASKCOS (local RDKit) |
| POST | `/api/synthesis/tree/` | Multi-step tree | ASKCOS |
| POST | `/api/synthesis/forward/` | Forward prediction | ASKCOS |
| POST | `/api/synthesis/conditions/` | Condition recommendation | ASKCOS |
| GET | `/api/synthesis/buyables/?smiles={smiles}` | Commercial availability check | ASKCOS |

### Synthesis Plans
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/synthesis-plans/?project={id}&analog={id}` | List plans (filterable) |
| POST | `/api/synthesis-plans/` | Create synthesis plan |
| GET | `/api/synthesis-plans/{id}/` | Plan detail |
| PATCH | `/api/synthesis-plans/{id}/` | Update plan status |
| DELETE | `/api/synthesis-plans/{id}/` | Delete plan |
| POST | `/api/synthesis-plans/{id}/plan-experiments/` | Create Experiment records from route steps |
| GET | `/api/synthesis-plans/{id}/context/` | Plan context for AI window |

### Salt & Polymorph Screening
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/projects/{id}/salt-screening/` | Get screen for project |
| POST | `/api/projects/{id}/salt-screening/` | Create screen |
| PATCH | `/api/salt-screens/{id}/` | Update screen (including lock selected form) |
| GET | `/api/salt-screens/{id}/candidates/` | List salt former candidates |
| POST | `/api/salt-screens/{id}/candidates/` | Add candidate |
| GET | `/api/salt-screen-candidates/{id}/experiments/` | List experiments |
| POST | `/api/salt-screen-candidates/{id}/experiments/` | Log experiment result |

### Formulation Plans
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/projects/{id}/formulation/` | Get formulation plan |
| POST | `/api/projects/{id}/formulation/` | Create formulation plan |
| PUT | `/api/formulation-plans/{id}/` | Update plan metadata |
| GET | `/api/formulation-plans/{id}/components/` | List components |
| POST | `/api/formulation-plans/{id}/components/` | Add component |
| DELETE | `/api/formulation-components/{id}/` | Remove component |
| POST | `/api/formulation-plans/{id}/check-compatibility/` | Run compatibility check |
| GET | `/api/formulation-plans/{id}/context/` | Plan context for AI window |

### Excipients
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/excipients/?q={name}&function={fn}&route={route}` | Search excipient library |
| GET | `/api/excipients/{id}/` | Excipient detail |

### Stability Plans
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/projects/{id}/stability/` | Get stability plan |
| POST | `/api/projects/{id}/stability/` | Create stability plan |
| GET | `/api/stability-plans/{id}/conditions/` | List conditions |
| POST | `/api/stability-plans/{id}/conditions/` | Add condition |
| GET | `/api/stability-conditions/{id}/results/` | List results |
| POST | `/api/stability-conditions/{id}/results/` | Log result for a timepoint |
| GET | `/api/stability-plans/{id}/context/` | Plan context for AI window |

### Analytical Methods
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/projects/{id}/analytical-methods/` | List all methods for project |
| POST | `/api/projects/{id}/analytical-methods/` | Create method |
| GET | `/api/analytical-methods/{id}/` | Method detail |
| PUT | `/api/analytical-methods/{id}/` | Update method |
| DELETE | `/api/analytical-methods/{id}/` | Delete method |

### Specifications
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/projects/{id}/specifications/` | Get specifications (by material type) |
| POST | `/api/projects/{id}/specifications/` | Create specification |
| PUT | `/api/specifications/{id}/` | Update specification |
| POST | `/api/specifications/{id}/export/` | Export formatted table |

### Preclinical Studies
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/projects/{id}/preclinical-studies/` | List studies |
| POST | `/api/projects/{id}/preclinical-studies/` | Create study |
| GET | `/api/preclinical-studies/{id}/` | Study detail |
| PUT | `/api/preclinical-studies/{id}/` | Update study |
| GET | `/api/preclinical-studies/{id}/context/` | Study context for AI window |
| GET | `/api/projects/{id}/admet-dashboard/` | Aggregated ADMET data (computational + experimental + benchmarks) |
| POST | `/api/projects/{id}/admet-benchmarks/` | Save benchmark targets |

### Literature & Clinical Trials
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/literature/search/?q={query}&max={n}` | PubMed article search |
| GET | `/api/literature/{pmid}/` | Article abstract + metadata |
| GET | `/api/trials/search/?condition={c}&intervention={i}&phase={p}` | Clinical trial search |
| GET | `/api/trials/{nct_id}/` | Trial detail |

### Regulatory
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/regulatory/guidance/?q={topic}` | FDA guidance document search |
| GET | `/api/regulatory/labels/?drug={name}` | Drug label (DailyMed) |
| GET | `/api/regulatory/ndc/?drug={name}` | NDC lookup (OpenFDA) |
| GET | `/api/regulatory/excipients/?form={dosage_form}` | Inactive ingredient suggestions |

### Drug Intelligence
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/drugs/search/?q={name}` | ChEMBL drug search |
| GET | `/api/drugs/{chembl_id}/` | Aggregated drug profile |
| GET | `/api/drugs/{chembl_id}/synthesis/` | PubMed synthesis articles |
| GET | `/api/drugs/{chembl_id}/trials/` | ClinicalTrials filtered by drug |
| GET | `/api/drugs/{chembl_id}/patents/` | SureChEMBL patent list |

### Patents
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/patents/?q={query}&mode={name\|smiles}` | SureChEMBL patent search |
| GET | `/api/patents/{patent_number}/` | Espacenet patent detail |

### Analogs & Investigations
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/analogs/search/` | PubChem similarity search |
| POST | `/api/analogs/patent-check/` | Parallel patent check |
| POST | `/api/analogs/admet/` | Parallel ADMET predictions |
| GET | `/api/investigations/` | List investigations |
| POST | `/api/investigations/` | Create investigation |
| GET | `/api/investigations/{id}/` | Investigation detail |
| PUT | `/api/investigations/{id}/` | Update investigation |
| POST | `/api/investigations/{id}/link-project/` | Link to project |
| GET | `/api/investigations/{id}/candidates/` | List candidates |
| POST | `/api/investigations/{id}/candidates/` | Add candidate |
| PATCH | `/api/analog-candidates/{id}/` | Update candidate (shortlist toggle) |

### AI Chat
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/chat/sessions/` | List sessions |
| POST | `/api/chat/sessions/` | Create session |
| GET | `/api/chat/sessions/{id}/` | Session with full history |
| POST | `/api/chat/sessions/{id}/messages/` | Send message; stream Claude response |
| DELETE | `/api/chat/sessions/{id}/` | Delete session |

### Documents
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/projects/{id}/documents/` | List project documents |
| POST | `/api/projects/{id}/documents/generate/` | AI-drafted document (Claude) |
| POST | `/api/projects/{id}/documents/` | Save manual document |
| GET | `/api/documents/{id}/` | Document content |
| PUT | `/api/documents/{id}/` | Update document |
| POST | `/api/documents/{id}/export/` | Export as PDF or DOCX |

---

## Vue Component List

### Layout
| Component | Description |
|---|---|
| `AppShell` | Root layout: side nav + main content area |
| `SideNav` | Navigation sidebar; includes Drug Discovery section, Projects section, per-project phase nav when inside a project |
| `TopBar` | Header: current project name, user menu, global compound search |
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
| `ExportButton` | Format selector (PDF/DOCX/CSV) + download trigger |
| `StreamingIndicator` | Animated dots while AI is generating |
| `StatsBadge` | Numeric chip label |
| `SaveReferenceBtn` | Saves an external item as a project reference |

### Dashboard
| Component | Description |
|---|---|
| `ProjectCard` | Project summary: name, pathway badge, phase progress dots, status, compound count |
| `RecentActivityFeed` | Chronological experiment + result + decision activity list |
| `QuickActionPanel` | CTA buttons: New Project, Open Chat, Search Compounds |
| `PendingDecisionsList` | Projects at a phase gate with no decision recorded |

### Project Page
| Component | Description |
|---|---|
| `ProjectForm` | Project name, description, pathway selector, status fields |
| `CompoundSearch` | Debounced compound name search against PubChem/ChEMBL |
| `CompoundPreviewCard` | Selected compound summary: SMILES, MW, formula |
| `PhaseTracker` | Horizontal pipeline of phase chips colored by status |
| `GoNoGoButton` | Opens decision modal: go/no-go + rationale text |
| `AnalogCandidateTable` | Shortlisted analogs with similarity, patent, plan status columns |
| `SynthesisPlanTable` | Plans with type, analog, status, step count, Browse/Compare actions |
| `PhaseSectionPanel` | Collapsible section wrapper per development phase |

### Compound Profile
| Component | Description |
|---|---|
| `CompoundHeader` | Name, IDs, approval badge, project link |
| `MoleculeViewer` | 2D structure PNG display |
| `PropertyTable` | Physicochemical key-value table with Lipinski flag |
| `ADMETCard` | Color-coded ADMET endpoint grid |
| `SafetyPanel` | Tox21 assay count, GHS hazard codes |
| `TargetList` | Pharmacological target table with UniProt links |
| `SimilarCompoundsList` | Fingerprint-similar compound mini cards |

### Target Profile
| Component | Description |
|---|---|
| `TargetHeader` | Gene symbol, UniProt accession, protein name, organism |
| `TargetFunctionCard` | Function annotation, GO terms, disease associations |
| `TissueExpressionChart` | Bar chart of expression levels by tissue |
| `PDBStructureTable` | PDB list with resolution, method, deposit date; "Use for Screening" action |
| `BindingSiteList` | Known active and allosteric sites |
| `KnownBindersList` | ChEMBL inhibitors with IC50/Ki and activity badge |
| `PathwayChoicePanel` | Two CTA buttons: Explore Known Drugs / Start Virtual Screening |

### Disease Explorer
| Component | Description |
|---|---|
| `DiseaseSearch` | Autocomplete disease name input |
| `DiseaseOverviewCard` | Disease name, EFO ID, description |
| `TargetAssociationTable` | Ranked target list; rows navigate to `/targets/:uniprot_id` |
| `KnownDrugsTable` | Clinical drugs; rows navigate to `/drugs/:chembl_id` |

### Virtual Screening
| Component | Description |
|---|---|
| `TargetSetupPanel` | PDB ID input/selector, binding site box definition |
| `LibrarySelector` | Radio group for library type; custom SMILES upload area |
| `DockingJobStatus` | Progress indicator polling run status |
| `HitResultsTable` | Ranked hits with score, Lipinski, patent badge, shortlist toggle |
| `HitDetailCard` | Slide-in panel: SMILES, score, ADMET summary |
| `ScreeningShortlistPanel` | Pinned hits with Save to Project CTA |

### SAR Tracker
| Component | Description |
|---|---|
| `SAREntryForm` | Compound/parent pickers, property, value/unit, verdict, rationale |
| `SARDataTable` | Sortable/filterable SAR entry list |
| `SARHeatmap` | Compound × property matrix colored by verdict |

### Candidate Selection
| Component | Description |
|---|---|
| `CandidateComparisonTable` | Side-by-side columns: structure, similarity, patent, ADMET, SAR, buyability |
| `SelectionForm` | Rationale textarea + "Select as Development Candidate" button |
| `SelectedCompoundBadge` | Confirmation chip when selection is made |

### Drug Intelligence & Drug Profile
| Component | Description |
|---|---|
| `DrugSearchInput` | Debounced drug name search with autocomplete |
| `DrugSearchResultsList` | Result rows navigating to drug profile |
| `DrugIdentityCard` | Structure image, SMILES, formula, MW, approval badge |
| `MechanismOfActionCard` | Target name, pathway, mechanism description |
| `FormulationDetailsCard` | Inactive ingredients, dosage form, route (DailyMed) |
| `ClinicalTrialsList` | Trials table for this drug |
| `SynthesisLiteratureList` | PubMed synthesis articles list |
| `PatentLandscapeTable` | Patent table with "View Claims" action |
| `PatentClaimsDrawer` | Slide-in panel with full patent claim text |

### Analog Workspace
| Component | Description |
|---|---|
| `ReferenceDrugPanel` | Reference SMILES, structure image, key props, threshold slider |
| `CandidatePoolPanel` | Grid of candidates with structure, scores, badges |
| `ShortlistPanel` | Pinned candidates, ADMET comparison table, Save to Project CTA |
| `PatentCheckProgress` | Bulk patent check progress bar |
| `ADMETRunProgress` | Bulk ADMET prediction progress bar |
| `ProjectModeModeBanner` | Blue banner for project mode |

### Salt & Polymorph Screening
| Component | Description |
|---|---|
| `ScreenObjectiveForm` | Objective, baseline pKa, baseline melting point |
| `SaltFormerSearch` | Searchable counterion list with pKa delta and solubility impact |
| `ScreeningMatrixTable` | Auto-generated experiment list |
| `SaltScreenResultsTable` | Per-experiment results with observed form badge |
| `FormSelectionPanel` | Comparison table + "Lock Preferred Form" button |

### Process Development
| Component | Description |
|---|---|
| `SynthesisRoutePicker` | Dropdown of SynthesisPlan records |
| `CPPDocumentationAccordion` | Per-step accordion: CPP form, CQA form, PAT notes |
| `ScaleUpMilestoneTable` | Lab/pilot/manufacturing milestone rows |
| `ImpurityProfileTable` | Impurity rows with ICH class, limit, control strategy |

### Formulation Planning
| Component | Description |
|---|---|
| `DosageFormSelector` | Form type, route, dose, release type, population notes |
| `ExcipientBuilder` | Dynamic component rows with function, qty, IIG badge |
| `IIGComplianceBadge` | Green/red compliance indicator per component |
| `CompatibilityFlagList` | Risk-colored flags with mandatory rationale for high/critical |
| `FormulationSummaryTable` | Read-only full composition table |
| `ManufacturingProcessForm` | Granulation, coating, fill/finish notes |

### Excipient Library
| Component | Description |
|---|---|
| `ExcipientSearch` | Text + function filter + route filter |
| `ExcipientResultsList` | Card list with name, CAS, function badges |
| `ExcipientDetailDrawer` | Slide-in full record |

### Stability Planning
| Component | Description |
|---|---|
| `StabilityObjectiveForm` | Material type, intended storage condition |
| `StabilityMatrixBuilder` | Condition checklist + timepoint/test configurator |
| `StabilityResultsEntry` | Per-condition/timepoint data entry form |
| `StabilityTrendChart` | Line chart per test; OOS highlighted in red |
| `OOSFlagList` | OOS and OOT result flags list |

### Analytical Methods
| Component | Description |
|---|---|
| `AnalyticalMethodList` | All methods for project with status badges |
| `MethodDefinitionForm` | Type, purpose, analytes, instrument, reference standards |
| `DevelopmentExperimentLog` | Method dev experiment history with verdict badges |
| `FinalParametersPanel` | Settled method parameters card |
| `ValidationChecklist` | ICH Q2(R1) characteristics checklist |

### Specification Builder
| Component | Description |
|---|---|
| `MaterialTypeToggle` | Drug substance / drug product selector |
| `SpecificationTestRow` | Test, method, criteria, stage, basis |
| `SpecificationTable` | Assembled spec sheet |
| `ExportSpecButton` | PDF or CSV download trigger |

### Preclinical
| Component | Description |
|---|---|
| `StudyTypeFilter` | Tab/chip filter by study type |
| `StudyList` | Study cards with type badge, status, conclusion |
| `StudyForm` | Full study design form |
| `StudyResultsForm` | Results summary + conclusion selector |
| `StudyDetailDrawer` | Slide-in full study record |

### ADMET Dashboard
| Component | Description |
|---|---|
| `ComputationalADMETPanel` | pkCSM predictions in traffic-light grid |
| `ExperimentalADMETPanel` | Measured values from preclinical studies with "Measured" badge |
| `BenchmarkComparisonTable` | Target ranges vs actual values; met/at-risk/failed chips |
| `BenchmarkEditForm` | Scientist-defined target range per endpoint |
| `ADMETRadarChart` | Spider chart normalized by benchmark |

### Experiment Planner
| Component | Description |
|---|---|
| `ExperimentForm` | Type, objective, project/compound/plan/study pickers |
| `VariableBuilder` | Dynamic variable row editor |
| `SuccessCriteriaPanel` | Structured + free-text criteria |
| `RetrosynPreview` | Inline ASKCOS top-3 precursors (synthesis) |
| `ExcipientSuggestion` | Inactive ingredient suggestions (formulation) |

### Experiment Results
| Component | Description |
|---|---|
| `ResultsForm` | Dynamic metric entry fields |
| `AIInterpretation` | Streamed Claude result interpretation |
| `DecisionPanel` | Optimize / Reproduce / Scale / Abort |
| `ResultsTimeline` | Chronological prior submissions |
| `ResultsChart` | Line/bar chart of metrics over time |

### Risk Analysis
| Component | Description |
|---|---|
| `RiskHeatMap` | 5×5 probability–impact grid with draggable markers |
| `RiskFactorList` | Editable risk factor rows |
| `RegulatorySummary` | FDA guidance document cards |
| `ClinicalPrecedentCard` | Trial count and phase breakdown |
| `GenerateRiskBtn` | Triggers AI risk generation |

### Synthesis Planning
| Component | Description |
|---|---|
| `SynthesisInput` | SMILES input with validation |
| `LockedContextPanel` | Pre-loaded analog and project context display |
| `AnalysisTypeToggle` | Single-step / multi-step toggle with lock support |
| `ReactionStepCard` | Step card: transform, precursors, conditions, buyability check |
| `SynthesisTreeNode` | Recursive multi-step tree node |
| `ConditionBox` | Inline reagents/solvent/temp/time display |
| `BuyableCheck` | Availability badge per precursor |
| `ForwardPredictionPanel` | Collapsed in Advanced Tools |
| `SpectraViewer` | NIST IR/MS spectrum plot |
| `ProjectPicker` | Project dropdown shown on standalone access |

### Literature
| Component | Description |
|---|---|
| `LiteratureSearch` | PubMed query with field selectors |
| `ArticleCard` | Title, authors, journal, date, abstract, save button |
| `TrialSearch` | Condition + intervention + phase/status filters |
| `TrialCard` | NCT ID, title, phase, status, enrollment |
| `PatentSearchBar` | Name / SMILES search for patents tab |
| `PatentResultRow` | Patent result row with View Claims action |

### AI Chat
| Component | Description |
|---|---|
| `SessionList` | Saved session sidebar |
| `ChatInterface` | Scrollable message history + input bar |
| `MessageBubble` | Single message with role and timestamp |
| `SourceCitation` | Collapsible API source list |
| `SuggestedQueries` | Example questions on empty session |

### Process Documentation
| Component | Description |
|---|---|
| `DocumentList` | Saved documents with type badges |
| `DocumentEditor` | Markdown editor (CodeMirror) |
| `SectionBuilder` | Collapsible document section panels |
| `GenerateDocBtn` | Triggers Claude draft generation |

---

## New Backend Service Files

### `core/services/pdb.py`
Queries the RCSB Protein Data Bank REST API for protein structure data.

| Function | Description |
|---|---|
| `search_structures(uniprot_id)` | Returns list of PDB entries for a UniProt accession (PDB ID, resolution, method, deposit date, chains) |
| `get_structure_metadata(pdb_id)` | Full metadata for a single PDB entry |
| `get_binding_sites(pdb_id)` | Binding site annotations from PDB SIFTS / ligand occupancy data |

Base URL: `https://data.rcsb.org/rest/v1/` — Cache TTL: 30 days — Source key: `pdb`

---

### `core/services/zinc.py`
Provides compound library subsets for virtual screening from ZINC20.

| Function | Description |
|---|---|
| `get_fda_approved(limit=2500)` | Returns SMILES list of FDA-approved drugs from ChEMBL approved subset (cached locally) |
| `get_clinical_candidates(limit=15000)` | Returns SMILES list of clinical stage compounds from ChEMBL (cached locally) |
| `get_fragment_library(limit=50000)` | Returns SMILES list from ZINC20 fragment subset (cached locally as file) |

Cache TTL: 7 days — Source key: `zinc`

---

### `core/services/autodock.py`
Manages AutoDock Vina docking jobs as background processes. Requires AutoDock Vina binary and Open Babel installed on the server.

| Function | Description |
|---|---|
| `prepare_receptor(pdb_id, binding_site)` | Downloads PDB file, strips water and ligands, converts to PDBQT via Open Babel subprocess |
| `prepare_ligands(smiles_list)` | Converts SMILES list to 3D SDF via RDKit, then to PDBQT via Open Babel |
| `run_docking(receptor_pdbqt, ligand_pdbqts, box_center, box_size)` | Runs `vina --receptor ... --ligands ... --out ...` subprocess; returns stdout log |
| `parse_results(vina_output_pdbqt)` | Parses Vina output PDBQT to extract docking scores per ligand |
| `run_screening_job(run_id)` | Full pipeline called by async worker: prepare → dock → parse → write hits to DB → update run status |

---

### `core/services/ccdc.py`
Queries the CCDC public REST API for crystal structure data to support salt/polymorph screening.

| Function | Description |
|---|---|
| `search_structures(smiles)` | Finds known crystal structures for a SMILES in the Cambridge Structural Database |
| `get_crystal_data(identifier)` | Returns crystal structure metadata: space group, unit cell, melting point, polymorph flag |

Base URL: `https://api.ccdc.cam.ac.uk/` — Cache TTL: 30 days — Source key: `ccdc`

---

## New Pinia Stores

### `stores/virtual_screening.js` — `useVirtualScreeningStore`
```js
state: {
  targetProfile: null,       // { uniprot_id, pdb_ids, selected_pdb_id, binding_site_definition }
  selectedLibrary: 'fda_approved',
  customSmiles: [],
  currentRun: null,          // { id, status, result_count }
  hits: [],                  // sorted by docking_score
  shortlisted: [],
  loading: { run, hits, admet, patents }
}
actions: setupTarget(uniprotId), selectPDB(pdbId), defineBindingSite(box),
         startScreening(), pollRunStatus(), checkADMET(hitIds), checkPatents(hitIds),
         toggleShortlist(hit), saveShortlistedToProject(projectId)
```

### `stores/sar.js` — `useSARStore`
```js
state: {
  entries: [],    // SAREntry records for current project
  loading: false,
  error: null
}
actions: fetchEntries(projectId), addEntry(data), deleteEntry(id)
```

### `stores/formulation.js` — `useFormulationStore`
```js
state: {
  plan: null,               // FormulationPlan record
  components: [],           // FormulationComponent records
  flags: [],                // CompatibilityFlag records
  excipientSearchResults: [],
  loading: { plan, components, compatibility, excipients }
}
actions: fetchPlan(projectId), savePlan(data), addComponent(data),
         removeComponent(id), checkCompatibility(), searchExcipients(q, fn, route)
```

### `stores/stability.js` — `useStabilityStore`
```js
state: {
  plan: null,              // StabilityPlan record
  conditions: [],          // StabilityCondition records
  results: {},             // keyed by condition_id → array of StabilityResult records
  loading: { plan, conditions, results }
}
actions: fetchPlan(projectId), savePlan(data), addCondition(data),
         fetchResults(conditionId), logResult(conditionId, timepoint, data)
```

### `stores/analytical.js` — `useAnalyticalStore`
```js
state: {
  methods: [],             // AnalyticalMethod records for project
  currentMethod: null,
  specifications: [],      // Specification records for project
  loading: { methods, specifications }
}
actions: fetchMethods(projectId), createMethod(data), updateMethod(id, data),
         deleteMethod(id), fetchSpecifications(projectId), saveSpecification(data)
```

### `stores/preclinical.js` — `usePreclinicalStore`
```js
state: {
  studies: [],             // PreclinicalStudy records for project
  admetData: null,         // aggregated ADMET dashboard data
  benchmarks: {},          // scientist-defined benchmark targets per endpoint
  loading: { studies, admet }
}
actions: fetchStudies(projectId), createStudy(data), updateStudy(id, data),
         fetchADMETDashboard(projectId), saveBenchmarks(projectId, data)
```

---

## AI Integration

All AI features use the **Claude API** (`claude-sonnet-4-6`) via the Anthropic Python SDK with prompt caching enabled on system prompts.

### Existing Integration Patterns (v1)

**Pattern 1 — Tool-use chat** (`/api/chat/sessions/{id}/messages/`)
Claude is given a system prompt with project context and tool definitions for all integrated external APIs. It calls tools dynamically during a turn and streams the final answer with source citations.

**Pattern 2 — Targeted generation (one-shot)**
Single Claude calls for experiment interpretation (`/experiments/{id}/interpret/`), risk assessment generation (`/projects/{id}/risk-assessment/generate/`), and document drafting (`/projects/{id}/documents/generate/`). Use structured system prompts and project data as user message context.

**Pattern 3 — Response streaming**
All Claude calls use the streaming API. The Django backend forwards Server-Sent Events (SSE) to the Vue frontend.

### New Integration Patterns (v2)

**Pattern 4 — Per-page AI context endpoints**
Each major entity (project, compound, synthesis plan, formulation plan, stability plan, preclinical study) exposes a `/context/` endpoint that returns a structured JSON payload containing all data currently visible on that page. These endpoints:
- Call no external APIs — query only the local DB
- Are fast (<50ms) and not cached (project data changes frequently)
- Are consumed by the per-page AI window panel (planned for v3)
- Also serve as the context payload for AI document generation calls

Context response structure (example for `/api/projects/{id}/context/`):
```json
{
  "project": { "id": 1, "name": "...", "pathway": "analog_based" },
  "current_phase": "drug_substance",
  "phases": [ { "phase": "lead_optimization", "status": "complete", "decision": "go" }, … ],
  "compound": { "name": "...", "smiles": "...", "mw": 342.4 },
  "synthesis_plans": [ … ],
  "formulation_plan": { … },
  "recent_experiments": [ … ],
  "risk_assessment": { … }
}
```

**Pattern 5 — New document types**
Five new `doc_type` values require distinct Claude system prompt sections in `claude_client.py`:

| Document Type | System Prompt Focus |
|---|---|
| `formulation_report` | ICH Q8 pharmaceutical development, excipient selection rationale, IIG compliance |
| `stability_summary` | ICH Q1A(R2) conditions, acceptance criteria, OOS investigation guidance |
| `admet_summary` | Drug-like properties benchmarks, ADMET interpretation, development risk |
| `ind_cmc` | FDA IND CMC section requirements (21 CFR 312.23); drug substance + drug product sections |
| `handoff` | Internal phase transition checklist format; key decisions and open actions |

`ind_cmc` is the most complex: it assembles content from synthesis plans, salt/polymorph screen, formulation plan, stability plan, and analytical methods into a structured CMC narrative following FDA format.

### New Tool Definitions (`TOOL_DEFINITIONS`)

```python
{
  "name": "get_pdb_structure",
  "description": "Retrieve protein structure metadata and binding site information for a PDB ID",
  "input_schema": {
    "type": "object",
    "properties": { "pdb_id": { "type": "string" } },
    "required": ["pdb_id"]
  }
},
{
  "name": "get_excipient_info",
  "description": "Look up IIG limits, GRAS status, and known incompatibilities for a pharmaceutical excipient",
  "input_schema": {
    "type": "object",
    "properties": {
      "excipient_name": { "type": "string" },
      "route": { "type": "string", "description": "Route of administration, e.g. oral, parenteral" }
    },
    "required": ["excipient_name"]
  }
},
{
  "name": "get_stability_guidelines",
  "description": "Return ICH Q1A(R2) stability conditions, timepoints, and acceptance criteria for a material type",
  "input_schema": {
    "type": "object",
    "properties": {
      "material_type": { "type": "string", "enum": ["drug_substance", "drug_product"] },
      "intended_storage": { "type": "string", "description": "e.g. Store below 25°C" }
    },
    "required": ["material_type"]
  }
}
```

---

## Router Configuration (Frontend)

All routes in `frontend/src/router/index.js`:

### Global Routes
| Path | Component | Description |
|---|---|---|
| `/` | `DashboardPage` | Main dashboard |
| `/diseases` | `DiseaseExplorerPage` | Disease & target explorer |
| `/targets/:uniprot_id` | `TargetProfilePage` | Target profile (new) |
| `/drugs` | `DrugIntelligencePage` | Drug search entry |
| `/drugs/:chembl_id` | `DrugProfilePage` | Reference drug profile |
| `/patents` | `PatentExplorerPage` | Patent search |
| `/analogs` | `AnalogWorkspacePage` | Analog workspace (drug-search mode) |
| `/investigations/:id` | `AnalogWorkspacePage` | Analog workspace (saved investigation) |
| `/virtual-screening` | `VirtualScreeningPage` | Virtual screening (new) |
| `/excipients` | `ExcipientLibraryPage` | Excipient reference library (new) |
| `/synthesis` | `SynthesisPlanningPage` | Synthesis planning |
| `/synthesis/compare` | `SynthesisPlanComparisonPage` | Plan comparison |
| `/literature` | `LiteraturePage` | Literature & clinical trials |
| `/chat` | `ChatPage` | AI chat assistant |

### Project Routes
| Path | Component | Description |
|---|---|---|
| `/projects/new` | `ProjectPage` | Create new project |
| `/projects/:id` | `ProjectPage` | Project overview |
| `/projects/:id/edit` | `ProjectPage` | Edit project (same component) |
| `/compounds/:id` | `CompoundProfilePage` | Compound profile |
| `/projects/:id/sar` | `SARTrackerPage` | SAR tracker (new) |
| `/projects/:id/candidates` | `CandidateSelectionPage` | Candidate selection gate (new) |
| `/projects/:id/salt-screening` | `SaltPolymorphScreeningPage` | Salt/polymorph screen (new) |
| `/projects/:id/process-development` | `ProcessDevelopmentPage` | Process scale-up (new) |
| `/projects/:id/formulation` | `FormulationPlanningPage` | Formulation planning (new) |
| `/projects/:id/stability` | `StabilityPlanningPage` | Stability planning (new) |
| `/projects/:id/analytical` | `AnalyticalMethodPage` | Analytical methods list (new) |
| `/projects/:id/analytical/:method_id` | `AnalyticalMethodPage` | Method detail (new) |
| `/projects/:id/specifications` | `SpecificationBuilderPage` | Specification builder (new) |
| `/projects/:id/preclinical` | `PreclinicalStudyPlannerPage` | Preclinical study planner (new) |
| `/projects/:id/admet` | `ADMETDashboardPage` | ADMET dashboard (new) |
| `/experiments/new` | `ExperimentPlannerPage` | Plan experiment |
| `/experiments/:id` | `ExperimentResultsPage` | Experiment results |
| `/projects/:id/risk` | `RiskAnalysisPage` | Risk analysis |
| `/projects/:id/documents` | `DocumentationPage` | Documentation |

---

## Caching Strategy

All external API responses are cached in `external_data_cache` keyed by `(source, sha256(endpoint + params))`.

| Source | Default TTL | Notes |
|---|---|---|
| PubChem, ChEMBL, UniProt, Open Targets | 7 days | Compound and target data is stable |
| EPA CompTox, pkCSM | 7 days | Prediction models updated infrequently |
| PubMed, ClinicalTrials.gov | 1 day | Literature updates more frequently |
| OpenFDA, DailyMed | 3 days | Drug labeling changes periodically |
| ASKCOS | 24 hours | Retrosynthesis results are deterministic |
| NIST WebBook | 30 days | Reference spectra are immutable |
| SureChEMBL, Espacenet | 30 days | Patent filings change slowly |
| RCSB PDB | 30 days | Protein structures are immutable records |
| ZINC | 7 days | Library subsets are stable |
| CCDC | 30 days | Crystal structures are immutable records |

In production, replace the DB cache table with **Redis** using `django-redis`. Compound structure images and ZINC library SMILES files are stored as static files rather than re-fetched on every request.

Context endpoints (`/context/`) are **not cached** — they query only the local DB and must reflect the current project state.

---

## Implementation Notes

### Virtual Screening Job Model
AutoDock Vina runs take minutes for 50k compounds. The backend creates a `virtual_screening_runs` record with `status=pending`, triggers the job via a background thread (development) or Celery task (production), and updates status to `running` → `complete` or `failed`. The frontend polls `GET /api/virtual-screening/runs/{id}/` every 10 seconds until the status is terminal.

### Excipient Library Seeding
The `excipients` table is populated at deploy time via a Django management command:
```bash
python manage.py seed_excipients --file core/data/excipients.csv
```
The CSV bundles FDA IIG data with common pharmaceutical excipients and their incompatibility profiles. Scientists search and select from this library — they do not create excipient records.

### Process Development Storage
Process development data (CPPs, CQAs, scale-up milestones, impurity profiles) is stored as structured JSON on a `process_developments` table (one record per project, linked to a SynthesisPlan). The table is added in the v2 migration but not listed in the new tables section above since it closely mirrors the `risk_assessments` pattern — a single JSON document per project.

### SideNav Per-Project Navigation
When the user is inside a project (any route under `/projects/:id/...`), the SideNav shows a secondary navigation panel for that project with links to all phase-specific pages. This panel is hidden when viewing global pages (Drug Discovery, Literature, etc.).

---

## UPDATE 1 — Technical Implementation Changes

### New Route

| Route | Name | Component | Purpose |
|---|---|---|---|
| `/projects/:id/synthesis` | `SynthesisHub` | `SynthesisHubPage.vue` | Analog candidates + synthesis plans + synthesis experiments hub |

### Schema Change

```python
# core/models.py — AnalogCandidate
selected = models.BooleanField(default=False)
```

Migration: `core/migrations/0006_add_analog_candidate_selected.py`

### New API Method

```js
// frontend/src/services/api.js — analogs module
update: (id, data) => api.patch(`/analog-candidates/${id}/`, data)
```

Uses the existing `AnalogCandidateDetailView` (`RetrieveUpdateAPIView`) — no backend changes needed.

### Backend Filter Addition

```python
# core/views/experiments.py — ExperimentListCreateView
plan_id = self.request.query_params.get('synthesis_plan')
if plan_id:
    qs = qs.filter(synthesis_plan_id=plan_id)
```

Allows fetching experiments scoped to a specific synthesis plan via `GET /api/experiments/?synthesis_plan=<id>`.

New API method: `experiments.listByPlan(planId)`.

### Vue Router Component Reuse Fix

```html
<!-- frontend/src/App.vue -->
<router-view :key="$route.fullPath" />
```

Without this, navigating from `/projects/new` to `/projects/:id/edit` (same component) reused the component instance. `isEdit = !!route.params.id` as a plain `const` evaluated once and stayed `false`, preventing the Reference Drug section from rendering. Adding `:key="$route.fullPath"` forces component teardown and remount on every route change.

### ProjectForm Pathway Event

```js
// frontend/src/components/projects/ProjectForm.vue
watch(() => form.pathway, (val) => emit('update:pathway', val))
```

The parent (`ProjectSetupPage`) listens via `@update:pathway="selectedPathway = $event"` to reactively show/hide the Reference Drug section when the user changes the pathway selector during project creation.

### Synthesis Planning — Experiment Integration

The `SynthesisPlanningPage` now:
- Loads experiments linked to the saved plan via `experiments.listByPlan(plan.id)` on mount and after save
- Shows an Experiments table below the plan actions bar
- "Plan Experiments" stays on the same page and refreshes the table instead of redirecting to the project page

### ExperimentPlannerPage — Query Param Pre-fill

When navigated to with `?project=X&plan=Y&type=synthesis`, the experiment creation form:
- Pre-fills and locks the Project selector
- Pre-fills and locks the Type selector
- Attaches `synthesis_plan: Y` to the POST payload
- Redirects back to the synthesis plan page (`/synthesis?project=X&plan=Y`) after creation instead of the experiment detail page

### Files Modified in UPDATE 1

| File | Change |
|---|---|
| `core/models.py` | Added `selected` field to `AnalogCandidate` |
| `core/migrations/0006_add_analog_candidate_selected.py` | New migration |
| `core/views/experiments.py` | Added `synthesis_plan` query filter |
| `frontend/src/App.vue` | Added `:key="$route.fullPath"` to `<router-view />` |
| `frontend/src/router/index.js` | Added `SynthesisHub` route |
| `frontend/src/components/layout/SideNav.vue` | Redesigned to 7 grouped phases with sub-items |
| `frontend/src/components/layout/TopBar.vue` | Added `SynthesisHub` to page title map |
| `frontend/src/components/projects/ProjectForm.vue` | Added `update:pathway` emit |
| `frontend/src/services/api.js` | Added `analogs.update()`, `experiments.listByPlan()` |
| `frontend/src/style.css` | Added `.nav-phase-header`, `.nav-subitem` styles |
| `frontend/src/views/ProjectSetupPage.vue` | Removed analog/plan/experiment sections; added quick links; added reference drug in create mode |
| `frontend/src/views/SARTrackerPage.vue` | Added "Candidate Selection →" button |
| `frontend/src/views/CandidateSelectionPage.vue` | Added "Select as Development Candidate" gate |
| `frontend/src/views/SynthesisHubPage.vue` | New page |
| `frontend/src/views/SynthesisPlanningPage.vue` | Added plan-linked experiments table; fixed Plan Experiments to stay on page |
| `frontend/src/views/ExperimentPlannerPage.vue` | Added query param pre-fill and lock for project/plan/type |
| `frontend/src/views/AnalogWorkspacePage.vue` | Fixed project context preservation; added "← Back to Discovery" button |

---

## UPDATE 2 — Process Development Redesign

### Problem Addressed

`ProcessDevelopmentPage` was showing a synthesis experiment table, duplicating the Synthesis Hub. The two pages now have clearly distinct responsibilities:

- **Synthesis Hub** (`/projects/:id/synthesis`): bench chemistry — analog candidates, synthesis plans, lab-scale synthesis experiments.
- **Process Development** (`/projects/:id/process-development`): manufacturing translation — scale-up milestones, CPPs/CQAs, impurity profiling.

### ProcessDevelopmentPage — Rewrite

The page was rewritten from scratch. Key implementation details:

**Route selector** loads `synthesisPlanApi.list(projectId)` on mount. A `selectedPlan` computed property derives the full plan object from `selectedPlanId`. "View Route →" constructs the synthesis navigation URL with `plan_type`, `plan.id`, and encoded `target_smiles`:

```js
router.push(`/synthesis?project=${projectId}&plan=${plan.id}&type=${plan.plan_type}&smiles=${encodeURIComponent(plan.target_smiles)}`)
```

**Scale-up milestones** are a `ref([])` of three fixed objects (Lab / Pilot / Manufacturing), each with `batch_size`, `equipment`, `yield_pct`, `status`, `notes`. Direct `v-model` binding into the array makes each table cell reactive without any additional logic.

**Impurity profile** entries are added to `impurities = ref([])` with a `Date.now()` id for keying. ICH `genotoxic` class gets a `badge-failed` CSS class for red highlighting.

**No new backend calls** were introduced. All state is component-local. When backend persistence is added, the milestones become `ScaleUpPlan` records and impurity entries become `ImpurityProfile` records linked to the project.

### Files Modified in UPDATE 2

| File | Change |
|---|---|
| `frontend/src/views/ProcessDevelopmentPage.vue` | Full rewrite — removed experiment table, added 4-section layout (route selector, milestones, CPP/CQA notes, impurity profile) |

---

## UPDATE 3 — Salt & Polymorph Screening — Full Redesign

### Reference Page Standard

**The Salt & Polymorph Screening page is the reference implementation for all future pages in this application.** It demonstrates the level of scientific detail, UX structure, and data model depth that every domain page should target. When building or reviewing any other page, ask: "does this match the screening page's standard?" Specifically:

- **Domain fidelity**: fields and workflows match what a real scientist would use (pKa delta rule, ICH prep methods, XRPD/DSC/TGA results, solid form classification)
- **Preset shortcuts**: quick-add lists for common choices (19 common counterions, polymorph form names) eliminate tedious manual entry for well-known values
- **Progressive disclosure**: four tabs (Setup → Candidates → Experiments → Results) guide the user through a sequential workflow without overwhelming them with one long form
- **Inline scientific guidance**: helper text explains why a field matters (e.g., "ΔpKa ≥ 2 rule for viable salt formation")
- **Compound state management**: `newScreenForm` (creation) and `screenForm` (editing) are separate refs — never share a creation form with an editing form
- **Always-visible list**: the campaigns list card is always rendered, not conditionally shown only when multiples exist
- **Auto-labeling**: multiple campaigns of the same type are auto-numbered ("Salt Screen 1", "Salt Screen 2") via a computed `screenLabel` map

### Model Expansions

**`SaltPolymorphScreen`** — added: `objective`, `baseline_pka`, `baseline_melting_point_c`, `baseline_solubility_mgml`, `baseline_logp`, `baseline_hygroscopicity` (choices), `baseline_notes`, `selection_rationale`, `updated_at`

**`SaltScreenCandidate`** — replaced `counterion_or_polymorph` with `name`; added `cas_number`, `counterion_type`, `pka_delta`, `theoretical_solubility_impact` (choices), `notes`. Legacy columns `counterion_or_polymorph`, `hygroscopicity`, `solubility_mgml`, `melting_point` retained in the model class with `blank=True, default=''` (see bug note below).

**`SaltScreenExperiment`** — replaced generic `method` / `conditions` JSON / `results` JSON with: `prep_method` (7 choices), `solvent`, `ratio`, `temperature_c`, `results_xrpd`, `results_dsc`, `results_tga`, `results_solubility`, `results_appearance`, `observed_form` (5 choices). Legacy fields retained as nullable.

### New API Endpoints

| Method | URL | Purpose |
|---|---|---|
| PATCH / DELETE | `/api/salt-screen-candidates/:id/` | Update or remove a single candidate |
| PATCH / DELETE | `/api/salt-screen-experiments/:id/` | Update or remove a single experiment |
| DELETE | `/api/salt-screens/:id/` | Delete a screen (cascades to candidates + experiments) |

### Bug Pattern: SQLite NOT NULL on Legacy Columns

**Root cause**: When a `CharField` without `null=True` exists in the DB but its field is removed from the Django model class, Django stops including it in INSERT statements. SQLite enforces NOT NULL with no DB-level fallback → `IntegrityError`.

**Wrong fix**: `AlterField` with `default=''` in a migration does NOT reliably add a `DEFAULT ''` clause to the SQLite column at the DB level. The migration runs without error but the problem persists at runtime.

**Correct fix**: Add the legacy field back to the model class with `blank=True, default=''`. Django then supplies the empty string on every INSERT, satisfying the constraint without any migration needed. This is the authoritative fix for this class of error anywhere in the codebase.

### UX Patterns Established (apply to all future pages)

| Pattern | Implementation |
|---|---|
| Entity list always visible | Render list card regardless of item count; don't hide at count ≤ 1 |
| Auto-numbered duplicate labels | Computed map — count per type, append number only when duplicates exist |
| Separate create vs edit forms | Two distinct refs; never bind a creation form to the same ref as an edit form |
| Preset quick-add chips | Static constant array; chip `disabled` when already added |
| Cascading delete with confirmation | `confirm()` with item name; DELETE → filter local array → auto-select next item |
| Save feedback | Boolean `ref` → success label for 3 s via `setTimeout` |
| Click isolation on row buttons | `@click.stop` on action buttons inside clickable rows |
| Color-coded categorical badges | `CATEGORY_COLORS` map → inline `style` object applied consistently |

### Files Modified in UPDATE 3

| File | Change |
|---|---|
| `core/models.py` | Expanded all three salt screen models; re-added legacy fields to `SaltScreenCandidate` |
| `core/migrations/0007_salt_screen_expanded_fields.py` | New fields on all three salt screen models |
| `core/migrations/0008_salt_candidate_counterion_nullable.py` | AlterField attempt (insufficient alone) |
| `core/migrations/0009_salt_candidate_legacy_defaults.py` | AlterField attempt for hygroscopicity (insufficient alone) |
| `core/views/salt_screening.py` | Added `SaltScreenCandidateDetailView`, `SaltScreenExperimentDetailView` |
| `core/serializers.py` | Fixed `read_only_fields` on `SaltPolymorphScreenSerializer`; added `experiment_count` and `candidate_name` computed fields |
| `core/views/__init__.py` | Exported two new detail views |
| `core/urls.py` | Registered detail routes for candidates and experiments |
| `frontend/src/services/api.js` | Added `saltScreening.updateCandidate`, `.deleteCandidate`, `.updateExperiment`, `.deleteExperiment`, `.delete` |
| `frontend/src/views/SaltPolymorphScreeningPage.vue` | Full rewrite — 4-tab layout, preset counterion chips, granular experiment form, results summary, form selection, campaigns list, auto-numbering, remove screen action |

---

## UPDATE 4 — Formulation Planning & Stability Planning — Full Redesign

### Root Cause Fixed: DRF Serializer 400 Pattern

Both pages failed with 400 on record creation. Root cause is identical across all pages with a project FK:

**Pattern**: `perform_create(serializer.save(project_id=self.kwargs['pk']))` — DRF validates the full payload before `perform_create` runs. Since `project` is a required FK on the model and `fields = '__all__'`, DRF demands the client supply it. The client never sends it (the view injects it). Fix: mark `project` as read-only so DRF skips validation.

**Applied fix** to both serializers:
```python
class FormulationPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormulationPlan
        fields = '__all__'
        read_only_fields = ('project', 'created_at', 'updated_at')

class StabilityPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = StabilityPlan
        fields = '__all__'
        read_only_fields = ('project', 'created_at', 'updated_at')
```

**Rule for future serializers**: Any serializer whose create view uses `perform_create` to inject `project_id` must declare `read_only_fields` containing at minimum `('project', 'created_at', 'updated_at')`.

---

### Model Change — StabilityResult New Fields

Two fields added to `StabilityResult`:

| Field | Type | Notes |
|---|---|---|
| `water_content_pct` | FloatField null/blank | Karl Fischer water content measurement |
| `dissolution_pct` | FloatField null/blank | % dissolved (USP apparatus) at specified timepoint |

`StabilityResultSerializer` already uses `fields = '__all__'` + `extra_kwargs = {'condition': {'required': False}}` — no serializer change needed.

Migration: `core/migrations/0010_stability_result_extra_fields.py`

---

### FormulationPlanningPage.vue — Technical Details

**State refs:**
- `creatingPlan` — boolean; controls creation modal visibility
- `newPlanForm` — creation-only form (dosage_form, route, target_dose_mg, release_type, rationale); reset after create
- `planForm` — edit form for target tab; populated from `store.plan` via `loadPlanIntoForm()` on mount and after creation
- `componentForm` — add-component form; reset after each add
- `compatForm` — add-compatibility-flag form
- `saveStatus` — `'saved'` | `''`; drives "✓ Saved" inline feedback

**Key computed:**
- `totalConcentration` — `store.components.reduce` on `concentration` field; `.toFixed(1)`
- `concentrationStatus` — returns `{ color, label }` based on total: > 102% = over (red), 99.5–102% = balanced (green), 90–99.5% = incomplete (orange), else grey
- `criticalFlagCount`, `warningFlagCount` — filtered from `store.flags`

**`PRESET_EXCIPIENTS`** — object keyed by component_type value (`diluent`, `binder`, `disintegrant`, `lubricant`, `glidant`, `coating`, `surfactant`, `preservative`). Each entry has: `name`, `grade`, `iig_limit`, `iig_unit`, `typical_pct`, `notes`. 37 presets total across 8 functional roles. `addPreset(preset, role)` pre-fills the `componentForm` ref.

**CSS architecture** — all styles scoped, no global classes. Notable patterns:
- `plan-header-bar`: flex row of stat pills with divider borders; responsive wrap
- `composition-bar-track` / `composition-bar-fill`: animated width + color transition on total %
- `preset-chip`: column flex button with name (blue) + typical % (grey); hover → blue border
- `sci-table`: full-width collapsed table with uppercase grey header row (2px bottom border), alternating hover, no bottom border on last row
- `severity-badge`: inline-flex pill with `background: color+'20'` (10% opacity fill) + solid border in severity color
- Tab badge: `min-width: 18px` pill; background overridden to red when critical flags present

---

### StabilityPlanningPage.vue — Technical Details

**State refs:**
- `creatingPlan` — boolean; controls creation modal
- `newPlanForm`, `planForm` — same separation pattern as FormulationPlanningPage
- `conditionForm` — includes `ich_category` (populated by preset) and `timepoints_months` (unused in current UI; reserved for future matrix builder)
- `resultForm` — 10 fields: condition_id, timepoint_weeks, assay_pct, degradants_pct, ph, water_content_pct, dissolution_pct, appearance, oos_flag, oot_flag, notes; reset after each log (preserving condition_id for sequential entry)

**`ICH_PRESETS`** — array of 6 objects with: `label`, `condition_label` (used as the DB field value), `temperature_c`, `humidity_rh` (null for frozen/refrigerated), `light_exposure`, `ich_category`, `guidance` (one-sentence ICH note), `color`. `applyPreset(preset)` fills `conditionForm` from the preset object.

**`ICH_TIMEPOINTS`** — array of 11 objects `{ months, weeks, label }` covering T0 through 60 months. Used both in the timepoint chips display and as the options source for the `timepoint_weeks` result form selector.

**Key computed:**
- `oosCount`, `ootCount` — `Object.values(store.results).flat().filter(r => r.oos_flag)` pattern
- `totalResults` — `Object.values(store.results).flat().length`
- `selectedConditionResults` — sorted by `timepoint_weeks` ascending for the active condition's result table

**`ichPresetColor(condition)`** — matches condition back to a preset by `condition_label` to retrieve the ICH category color; falls back to `#6b7280`. Used for left-border color on condition cards and the dot indicator in the conditions table.

**`assayStatusColor(val)`** — `< 97` → red; `< 98` → orange; else green. Applied to assay column cells in results table.

**`timepointLabel(weeks)`** — finds matching `ICH_TIMEPOINTS` entry within ±1 week; falls back to `${weeks}w`.

**Results table row coloring:**
- `.row-oos`: `background: #fff1f2` (red-50), hover `#fee2e2`
- `.row-oot`: `background: #fffbeb` (yellow-50), hover `#fef3c7`

**ICH compliance checklist** — live computed from `store.conditions` and `store.results`:
- Long-term: `store.conditions.some(c => c.temperature_c === 25)`
- Accelerated: `store.conditions.some(c => c.temperature_c === 40)`
- Photostability: `store.conditions.some(c => c.light_exposure?.includes('lux'))`
- OOS investigation: `oosCount === 0`
- 12-month data: `Object.values(store.results).flat().some(r => r.timepoint_weeks >= 52)`

---

### CSS Quality Standard Established

Both pages establish a consistent table and card visual pattern that should be used on all future pages:

| Element | CSS approach |
|---|---|
| Table headers | `background: #f9fafb`, `font-size: 12px`, uppercase + letter-spacing, `border-bottom: 2px solid #e5e7eb` |
| Table rows | `padding: 10px 12px`, `border-bottom: 1px solid #f3f4f6`, hover `background: #f9fafb` |
| Last row | `border-bottom: none` via `:last-child td` |
| Cards | `border: 1px solid #e5e7eb`, `border-radius: 8px`, `padding: 20px` — never box-shadow unless elevated modal |
| Section title | `font-size: 14px; font-weight: 600; color: #111827; margin: 0 0 16px` |
| Form inputs | `padding: 7px 10px`, `border: 1px solid #d1d5db`, `border-radius: 6px`, focus: `border-color: #2563eb + box-shadow: 0 0 0 2px #dbeafe` |
| Tab active indicator | `border-bottom: 2px solid #2563eb; color: #2563eb` — not background color |
| Tab transition | `animation: fadeIn .15s ease` on `.tab-content` — translateY(4px) → none |
| Modals | `position: fixed; inset: 0; background: rgba(0,0,0,.45)` overlay; box `border-radius: 10px`, `box-shadow: 0 20px 60px rgba(0,0,0,.2)` |

---

### Files Modified in UPDATE 4

| File | Change |
|---|---|
| `core/serializers.py` | Added `read_only_fields = ('project', 'created_at', 'updated_at')` to `FormulationPlanSerializer` and `StabilityPlanSerializer` |
| `core/models.py` | Added `water_content_pct` and `dissolution_pct` (FloatField null/blank) to `StabilityResult` |
| `core/migrations/0010_stability_result_extra_fields.py` | New migration for the two new `StabilityResult` fields |
| `frontend/src/views/FormulationPlanningPage.vue` | Full rewrite — creation modal, header bar, 4-tab layout, 37 preset excipient chips across 8 roles, composition progress bar, compatibility reference table, CSS quality upgrade |
| `frontend/src/views/StabilityPlanningPage.vue` | Full rewrite — creation modal, header bar with live OOS/OOT counts, 4-tab layout, 6 ICH preset buttons, timepoint chips, 10-field result form with OOS/OOT styled checkboxes, color-coded assay/dissolution columns, row highlighting, ICH compliance checklist, CSS quality upgrade |

---

## UPDATE 5 — Analytical Development — Full Redesign

### Overview

Both Analytical Development pages (`AnalyticalMethodPage.vue` and `SpecificationBuilderPage.vue`) were rewritten to the Reference Page Standard. Backend changes: serializer `read_only_fields` fixes (same DRF pattern as UPDATE 3/4), new `criteria_type` field on `Specification`, new `raw_material` spec type, migration `0011`.

---

### 6A — AnalyticalMethodPage.vue — Technical Details

#### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ PageHeader (title, + New Method button, save badge)             │
├──────────────────┬──────────────────────────────────────────────┤
│  Left panel      │  Right detail panel                          │
│  300px           │  flex: 1                                      │
│                  │                                               │
│  Methods list    │  Method header bar                           │
│  grouped by      │  (type pill · name · status · completion %)  │
│  type            │                                               │
│                  │  Tab nav: Definition | Dev Log | ICH Q2 | Ref│
│  ICH Q2(R1)      │                                               │
│  quick-ref       │  Tab content                                  │
│  table           │                                               │
└──────────────────┴──────────────────────────────────────────────┘
```

CSS: `display: grid; grid-template-columns: 300px 1fr; gap: 20px` on `.content-grid`.

#### Key State

```js
const activeMethodId = ref(null)        // drives store.currentMethod watcher
const activeTab = ref('params')         // 'params' | 'log' | 'validation' | 'reference'
const paramsForm = ref({})              // method-type-specific params (cleared on type change)
const newForm = ref({...})              // creation modal form — separate from detail
const showCreateModal = ref(false)
const devLogEntry = ref({date:'', experiment:'', observations:'', verdict:'suitable'})
const saveStatus = ref('')              // 'saved' | '' — clears after 2500ms
```

`watch(() => store.currentMethod, (m) => { if (m) loadMethod(m) })` — reloads `paramsForm` and fetches validation status whenever `currentMethod` changes.

#### PRESET_INSTRUMENTS (object keyed by method_type)

```js
PRESET_INSTRUMENTS = {
  hplc: ['Waters Acquity UPLC H-Class', 'Agilent 1260 Infinity II', 'Shimadzu Prominence UFLC',
         'Thermo Vanquish Core UHPLC', 'Waters Alliance e2695', 'Agilent 1290 Infinity II'],
  gc: ['Agilent 7890B GC', 'Shimadzu GC-2030', 'PerkinElmer Clarus 690', 'Thermo TRACE 1310'],
  nmr: ['Bruker Avance III 400 MHz', 'Bruker Avance NEO 600 MHz', 'JEOL ECZ-R 400 MHz', 'Oxford 300 MHz'],
  ms: ['Waters Xevo TQ-S', 'Thermo TSQ Altis', 'Agilent 6460 Triple Quad', 'Sciex QTRAP 6500+'],
  uv_vis: ['Shimadzu UV-2600', 'Agilent Cary 60', 'Thermo Evolution 220'],
  dissolution: ['Agilent 708-DS', 'Sotax AT 7 smart', 'Distek 2500', 'Hanson Research SR8-Plus'],
  particle_size: ['Malvern Mastersizer 3000', 'HORIBA LA-960V2', 'Sympatec HELOS'],
}
```

#### PRESET_PARAMS (object keyed by method_type, each value is array of preset objects)

Each HPLC preset: `{ label, column, mobile_phase_a, mobile_phase_b, gradient, flow_rate_ml_min, column_temp_c, injection_vol_ul, wavelength_nm, run_time_min, lod_ug_ml, loq_ug_ml, sample_prep }`. Three presets: `'Purity Gradient RP-HPLC'`, `'Assay Isocratic RP-HPLC'`, `'Impurity Gradient HPLC (PDA)'`.

Each GC preset: `{ label, column_type, carrier_gas, split_ratio, oven_program, inlet_temp_c, detector_type, detector_temp_c, loq_ppm }`. Two presets: `'Residual Solvent GC-HS (ICH Q3C)'`, `'Organic Volatile Impurities'`.

Each Dissolution preset: `{ label, apparatus, medium, medium_volume_ml, ph, temperature_c, rotation_rpm, sampling_timepoint, wavelength_nm }`. Three presets: `'Immediate Release USP <711>'`, `'Extended Release'`, `'Enteric Coated (pH 6.8)'`.

`applyParamPreset(preset)` — `Object.assign(paramsForm.value, preset)` (strips `label` key).

#### saveParams()

```js
async function saveParams() {
  const current = store.currentMethod.protocol || {}
  await store.updateMethod(store.currentMethod.id, {
    protocol: { ...current, params: { ...paramsForm.value } }
  })
  saveStatus.value = 'saved'
  setTimeout(() => { saveStatus.value = '' }, 2500)
}
```

Protocol merge pattern: always spread `current` first so `dev_log` and checklist keys are preserved.

#### addDevLogEntry()

```js
async function addDevLogEntry() {
  const current = store.currentMethod.protocol || {}
  const log = [...(current.dev_log || []), { ...devLogEntry.value, id: Date.now() }]
  await store.updateMethod(store.currentMethod.id, { protocol: { ...current, dev_log: log } })
  devLogEntry.value = { date: '', experiment: '', observations: '', verdict: 'suitable' }
}
```

Dev log displayed with `[...log].reverse()` — newest first.

#### toggleChecklist(item)

```js
async function toggleChecklist(item) {
  const current = store.currentMethod.protocol || {}
  await store.updateMethod(store.currentMethod.id, {
    protocol: { ...current, [item]: !current[item] }
  })
  await store.fetchValidationStatus(store.currentMethod.id)
}
```

`item` is a string key matching the backend's `VALIDATION_ITEMS` list (specificity, linearity, range, accuracy, repeatability, intermediate_precision, lod, loq, robustness). The backend `/validation/` endpoint reads `method.protocol.get(item)` and returns `{ completion_pct, items: [...] }`.

#### ICH_CHECKLIST_GUIDANCE (object keyed by item name)

Each entry: `{ title, criteria, experiments, note }`. Example for `linearity`:
```js
linearity: {
  title: 'Linearity',
  criteria: 'R² ≥ 0.999 across the range; y-intercept ≤ 2% of response at 100% level',
  experiments: 'Minimum 5 concentration levels spanning 50–150% of target concentration. Use independent dilutions, not serial. Plot response vs. concentration; perform linear regression. Check residuals.',
  note: 'ICH Q2(R1) Section 4.2. For impurity methods: range 0.1% reporting threshold to 120% specification limit.'
}
```

#### Method Type Color Map

```js
const METHOD_TYPE_COLORS = {
  hplc: '#2563eb', gc: '#16a34a', nmr: '#7c3aed', ms: '#d97706',
  uv_vis: '#0891b2', dissolution: '#dc2626', particle_size: '#6b7280', kf: '#059669',
  appearance: '#9ca3af', ph: '#0284c7', osmolality: '#7c3aed',
}
```

Used for the dot in the methods list, the type pill in the method header, and grouped list section headings.

#### methodsByType (computed)

```js
const methodsByType = computed(() => {
  const groups = {}
  for (const m of store.methods) {
    const t = m.method_type || 'other'
    if (!groups[t]) groups[t] = []
    groups[t].push(m)
  }
  return groups
})
```

Groups iterated with `Object.entries(methodsByType)` in the left panel.

---

### 6B — SpecificationBuilderPage.vue — Technical Details

#### Layout

Full-width single-column. No master-detail split — specs are a flat list per project, not a list within a list.

```
PageHeader (material type toggle · ICH Q6A button · + Add Specification)
Controls bar (material type chips · per-tab counts)
Tab nav (Release | Shelf Life | In-Process | Raw Material)
[Preset chips row — changes with material type + active tab]
[Spec table for active tab]
```

#### Key State

```js
const activeTab = ref('release')           // 'release' | 'shelf_life' | 'in_process' | 'raw_material'
const materialType = ref('DS')             // 'DS' | 'DP' | 'Intermediate'
const showModal = ref(false)
const editingId = ref(null)               // null = create, non-null = edit
const form = ref(emptyForm())             // single form ref for both create and edit
const showIchRef = ref(false)             // ICH Q6A reference panel toggle
const deletingId = ref(null)              // disables delete button during request
```

`emptyForm()` returns `{ spec_type: activeTab.value, attribute: '', criteria_type: 'NMT', acceptance_criteria: '', test_method: '', basis: '', analytical_method: null }`.

#### PRESET_SPECS structure

```js
PRESET_SPECS = {
  DS:           { release: [...15 presets], shelf_life: [...6], in_process: [...5], raw_material: [...5] },
  DP:           { release: [...13 presets], shelf_life: [...5], in_process: [...6], raw_material: [...4] },
  Intermediate: { release: [...5 presets],  shelf_life: [], in_process: [...3], raw_material: [...3] },
}
```

Each preset object: `{ attribute, criteria_type, acceptance_criteria, test_method, basis }`. `basis` always includes the ICH guideline reference and a note explaining the scientific rationale.

#### specsByTab (computed)

```js
const specsByTab = computed(() => {
  const map = {}
  for (const t of TABS) {
    map[t.key] = store.specifications.filter(s => s.spec_type === t.key)
  }
  return map
})
```

#### alreadyAdded (computed)

```js
const alreadyAdded = computed(() => {
  return new Set(activeSpecs.value.map(s => s.attribute.toLowerCase()))
})
```

Used to show a green checkmark on preset chips whose attribute already exists in the active tab. The check is case-insensitive but not normalized beyond that.

#### applyPreset(preset)

Pre-fills `form.value` from the preset and sets `editingId.value = null`, then opens the modal. The scientist reviews and saves — they don't need to retype standard compendial criteria.

#### save()

```js
async function save() {
  if (!form.value.attribute || !form.value.acceptance_criteria) return
  const payload = { ...form.value }
  if (editingId.value) {
    await store.saveSpecification(projectId, { ...payload, id: editingId.value })
  } else {
    await store.saveSpecification(projectId, payload)
  }
  showModal.value = false
  saveStatus.value = 'saved'
  setTimeout(() => { saveStatus.value = '' }, 2500)
}
```

`store.saveSpecification` already handles create vs. update by checking `data.id` presence.

#### criteriaColor map

```js
const criteriaColor = {
  NMT: '#dc2626',    // red   — upper limit
  NLT: '#2563eb',    // blue  — lower limit
  between: '#7c3aed',// purple — range
  conforms: '#16a34a',// green — qualitative
  report: '#6b7280', // grey  — informational
}
```

Badges use `color + '22'` for background (11% opacity) and `color + '66'` for border (40% opacity). This keeps all badges visually distinct without high-saturation fills.

#### ICH Q6A Reference Panel

`ICH_Q6A_TABLE` — 15 rows, each `{ test, ds, dp, note }`. Values for `ds`/`dp`: `'required'` / `'case-by-case'` / `'N/A'` / `'not typical'`. `ichBadge(val)` maps these to `{ label, bg, color }` for inline styling.

Below the main table: two side-by-side threshold tables:
- Q3A/B table: reporting / identification / qualification thresholds for DS and DP
- Q3C table: Class 1 / 2 / 3 limits with representative solvents

#### linkedMethodName(ref)

```js
const linkedMethodName = (ref) => {
  const id = ref && typeof ref === 'object' ? ref.id : ref
  return store.methods.find(m => m.id === id)?.method_name || `Method #${id}`
}
```

Handles both serializer representations: when the response nests the FK as an integer (default DRF PrimaryKeyRelatedField), and when it nests the full object (if a future serializer change adds depth).

#### Criteria type modal UX

The criteria type selector uses styled button toggles rather than a `<select>`. The active button gets inline style `{ background: criteriaColor[ct] + '22', borderColor: criteriaColor[ct], color: criteriaColor[ct] }`. This makes the selected type immediately obvious and reinforces the color coding established in the table.

The acceptance criteria input shows a `field-hint` below it that adapts to the selected `criteria_type`:
- NMT → `Enter limit value: NMT X% or just the value`
- NLT → `Enter limit: NLT X%`
- between → `Enter range: X–Y% or X to Y`
- conforms → `Describe reference: Conforms to [reference]`
- report → `Describe what is reported`

---

### Backend Changes in UPDATE 5

#### core/models.py — Specification

```python
class Specification(models.Model):
    SPEC_TYPE_CHOICES = [
        ('release', 'Release'),
        ('shelf_life', 'Shelf Life'),
        ('in_process', 'In-Process'),
        ('raw_material', 'Raw Material'),    # NEW
    ]
    CRITERIA_TYPE_CHOICES = [               # NEW
        ('NMT', 'NMT (Not More Than)'),
        ('NLT', 'NLT (Not Less Than)'),
        ('between', 'Between (Range)'),
        ('conforms', 'Conforms To'),
        ('report', 'Report Only'),
    ]
    # ... existing fields ...
    criteria_type = models.CharField(         # NEW
        max_length=20, choices=CRITERIA_TYPE_CHOICES, default='NMT', blank=True
    )
    acceptance_criteria = models.CharField(max_length=500)  # widened from 255
```

#### core/migrations/0011_specification_criteria_type_raw_material.py

```python
operations = [
    migrations.AddField('specification', 'criteria_type', models.CharField(...)),
    migrations.AlterField('specification', 'spec_type', models.CharField(choices=[..., ('raw_material', 'Raw Material')], ...)),
    migrations.AlterField('specification', 'acceptance_criteria', models.CharField(max_length=500)),
]
```

#### core/serializers.py — read_only_fields applied

```python
class AnalyticalMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticalMethod
        fields = '__all__'
        read_only_fields = ('project', 'created_at', 'updated_at')  # prevents 400

class SpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specification
        fields = '__all__'
        read_only_fields = ('project', 'created_at')               # prevents 400
        extra_kwargs = {'analytical_method': {'required': False, 'allow_null': True}}
```

#### frontend/src/services/api.js — delete added to analytical

```js
export const analytical = {
  list: (projectId) => api.get(`/projects/${projectId}/analytical-methods/`),
  create: (projectId, data) => api.post(`/projects/${projectId}/analytical-methods/`, data),
  get: (id) => api.get(`/analytical-methods/${id}/`),
  update: (id, data) => api.patch(`/analytical-methods/${id}/`, data),
  delete: (id) => api.delete(`/analytical-methods/${id}/`),   // was missing
  validation: (id) => api.get(`/analytical-methods/${id}/validation/`),
}
```

#### frontend/src/stores/analytical.js — deleteMethod added

```js
async deleteMethod(id) {
  try {
    await api.analytical.delete(id)
    this.methods = this.methods.filter(m => m.id !== id)
    if (this.currentMethod?.id === id) {
      this.currentMethod = this.methods[0] || null
      this.validationStatus = null
    }
  } catch (e) {
    this.error = e.message
  }
},
```

---

### Files Modified in UPDATE 5

| File | Change |
|---|---|
| `core/models.py` | Added `criteria_type` field and `raw_material` spec type to `Specification`; widened `acceptance_criteria` to 500 chars |
| `core/migrations/0011_specification_criteria_type_raw_material.py` | New migration |
| `core/serializers.py` | Added `read_only_fields` to `AnalyticalMethodSerializer` and `SpecificationSerializer` |
| `frontend/src/services/api.js` | Added `delete` to `analytical` API object |
| `frontend/src/stores/analytical.js` | Added `deleteMethod` action |
| `frontend/src/views/AnalyticalMethodPage.vue` | Full rewrite — two-column layout, create modal, 4-tab detail panel, method-type-specific parameter forms (HPLC 12-field, GC 8-field, NMR 7-field, Dissolution 8-field), preset parameter templates, development log (stored in protocol.dev_log), ICH Q2(R1) validation checklist with toggles (stored in protocol top-level keys), reference tables (system suitability, forced degradation, compendial references) |
| `frontend/src/views/SpecificationBuilderPage.vue` | Full rewrite — material type toggle, 4 spec type tabs, 50+ scientifically accurate presets across DS/DP/Intermediate, criteria type badge system (NMT/NLT/between/conforms/report with color coding), ICH Q6A reference panel with test applicability table + Q3A/B/C threshold tables, add/edit modal with criteria type toggle buttons and contextual field hints |

---

## UPDATE 6 — Technical Reference: ADMET Dashboard & Study Planner

### ADMETDashboardPage.vue — Architecture

**File:** `frontend/src/views/ADMETDashboardPage.vue`

#### Data Flow

```
store.fetchADMETDashboard(projectId)
  → GET /projects/{id}/admet-dashboard/
  → Response: {
      project_id,
      computed_admet: { compoundName: { compound_id, smiles, data: {pkCSM fields}, source } },
      experimental: [{ study_id, study_type, species, mtd_mgkg, findings: {...} }]
    }

// Extraction pattern
const firstCompoundEntry = computed(() => Object.entries(store.admetData?.computed_admet || {})[0])
const firstCompoundData  = computed(() => firstCompoundEntry.value?.[1]?.data)
// Access: firstCompoundData.value?.['Caco2+']
```

#### PKCSM_FIELDS Structure

```js
const PKCSM_FIELDS = {
  'Caco2+': {
    label: 'Caco-2 Permeability', unit: 'log cm/s', section: 'absorption',
    benchmark: '≥ −5.15 (high permeability)',
    pass: (v) => parseFloat(v) >= -5.15,
    guidance: 'Caco-2 Papp A→B <10⁻⁷ cm/s = BCS III/IV risk; >10⁻⁵ = excellent absorption',
  },
  'hERG_karim': {
    label: 'hERG Inhibition Risk', unit: 'probability', section: 'toxicity',
    benchmark: '< 0.5 (low risk)',
    pass: (v) => parseFloat(v) < 0.5,
    guidance: 'Probability >0.5 flags cardiac safety risk — pursue ICH S7B patch clamp and in vivo CV telemetry',
  },
  // ... 20+ total entries
}
```

Each entry: `label`, `unit`, `section` (`absorption|distribution|metabolism|excretion|toxicity`), `benchmark` (display string), `pass(v): bool`, `guidance` (full-sentence clinical context).

#### Key Computed Refs

| Ref | Returns |
|---|---|
| `bcsClass` | `'I'/'II'/'III'/'IV'` from HIA + Caco-2 + LogP |
| `riskFlags` | `[{id, label, detail, severity:'high'/'medium'/'info'}]` |
| `fieldsForSection(key)` | Filters PKCSM_FIELDS + attaches `.value` from firstCompoundData |
| `cellStatus(cfg, val)` | `'pass'/'flag'/'neutral'` using `cfg.pass(val)` |

#### CYP DDI Panel

5 enzymes (`CYP1A2`, `CYP2C9`, `CYP2C19`, `CYP2D6`, `CYP3A4`) × inhibitor + substrate matrix. pkCSM keys follow pattern: `CYP1A2_inhibitor`, `CYP1A2_substrate`, etc. Inhibitor = `true` flagged red; substrate = `true` flagged orange.

---

### PreclinicalStudyPlannerPage.vue — Architecture

**File:** `frontend/src/views/PreclinicalStudyPlannerPage.vue`  
**Lines:** 1210  
**Store:** `usePreclinicalStore` (preclinical.js)

#### Key Refs

| Ref | Purpose |
|---|---|
| `selectedStudy` | Full study object currently shown in detail panel |
| `activeTab` | `'design'/'protocol'/'results'/'ind'` |
| `indChecklist` | `{ [studyKey]: boolean }` — IND package checklist state (session-local) |
| `newStudyForm` | Controlled create-modal form |
| `studyForm` | Study Design tab edit form (synced from `selectedStudy` on select) |
| `resultsForm` | Results tab form — includes key_findings dict, conclusion, NOAEL, MTD |
| `newFindingKey/Value` | Transient row for adding key_findings entries |

#### selectStudy() Flow

```js
async function selectStudy(study) {
  const full = await store.fetchStudy(study.id)       // GET /preclinical-studies/{id}/
  selectedStudy.value = full || store.studies.find(s => s.id === study.id)
  activeTab.value = 'design'
  syncForms()   // copies selectedStudy fields into studyForm + resultsForm
}
```

#### saveDesign() vs saveResults()

| Action | Store method | API endpoint | Fields written |
|---|---|---|---|
| `saveDesign()` | `store.updateStudy(id, payload)` | `PATCH /preclinical-studies/{id}/` | study_type, title, glp, species, dose_route, dose_levels, duration_days, objective, primary_endpoints, success_criteria |
| `saveResults()` | `store.logResults(id, payload)` | `PATCH /preclinical-studies/{id}/results/` | status, conclusion, noael_mgkg, mtd_mgkg, results_summary, key_findings |

#### STUDY_PRESETS Structure

```js
STUDY_PRESETS = {
  [study_type]: [
    {
      label: string,          // Button label in create modal
      title: string,          // Pre-fills study title
      species: string,
      dose_route: string,
      dose_levels: number[],  // Array of mg/kg values
      duration_days: number,
      glp: boolean,
      objective: string,
      primary_endpoints: string[],
      success_criteria: string,
    }
  ]
}
```

8 study types covered. Presets are ICH M3(R2) / S2(R1) / S5(R3) / S7A/B compliant.

#### IND_PACKAGE Structure

```js
IND_PACKAGE = [
  {
    category: string,
    guideline: string,    // e.g. 'ICH S7A/S7B'
    note: string,
    studies: [
      { key: string, label: string, required: boolean }
    ]
  }
]
```

6 categories, 23 total studies (9 required, 14 recommended). `indProgress` computed tracks required-only completion percentage.

#### Status / Conclusion Colour Maps

```js
STATUS_STYLE = {
  planned:   { bg: '#eff6ff', color: '#1d4ed8', border: '#bfdbfe' },
  ongoing:   { bg: '#fff7ed', color: '#c2410c', border: '#fed7aa' },
  completed: { bg: '#f0fdf4', color: '#166534', border: '#bbf7d0' },
  reported:  { bg: '#f5f3ff', color: '#5b21b6', border: '#ddd6fe' },
  failed:    { bg: '#fef2f2', color: '#991b1b', border: '#fecaca' },
}

CONCLUSION_STYLE = {
  go:           { bg: '#f0fdf4', color: '#166534', border: '#bbf7d0' },
  no_go:        { bg: '#fef2f2', color: '#991b1b', border: '#fecaca' },
  inconclusive: { bg: '#fffbeb', color: '#92400e', border: '#fde68a' },
}
```

Inline style strings built by `statusStyle(status)` and `conclusionStyle(conclusion)` helpers.

---

### Backend Changes (UPDATE 6)

#### `core/views/preclinical.py` — PreclinicalStudyResultsView.patch()

Before:
```python
if 'key_findings' in request.data: study.key_findings = request.data['key_findings']
if 'mtd_mgkg' in request.data:     study.mtd_mgkg = request.data['mtd_mgkg']
if 'status' in request.data:       study.status = request.data['status']
```

After:
```python
for field in ('key_findings', 'mtd_mgkg', 'noael_mgkg', 'status', 'conclusion', 'results_summary'):
    if field in request.data:
        setattr(study, field, request.data[field])
```

#### Migration 0012 Fields

| Field | Type | Default |
|---|---|---|
| `title` | CharField(255) | `''` |
| `glp` | BooleanField | `False` |
| `primary_endpoints` | JSONField | `list` |
| `success_criteria` | TextField | `''` |
| `results_summary` | TextField | `''` |
| `conclusion` | CharField(20) | `''` |
| `noael_mgkg` | FloatField | `null` |

Applied: `python manage.py migrate core 0012`

---

### Files Modified (UPDATE 6)

| File | Type | Lines |
|---|---|---|
| `frontend/src/views/ADMETDashboardPage.vue` | Full rewrite | ~500 |
| `frontend/src/views/PreclinicalStudyPlannerPage.vue` | Full rewrite | 1210 |
| `frontend/src/services/api.js` | Added `preclinical.delete` | +1 |
| `frontend/src/stores/preclinical.js` | Added `fetchStudy`, `deleteStudy` | +16 |
| `core/views/preclinical.py` | Extended `ResultsView.patch()` | +3/−5 |
| `core/migrations/0012_preclinicalstudy_extended_fields.py` | NEW — 7 fields | 47 |
