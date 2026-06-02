# BioIntel — Product Specification v2

## Vision

BioIntel is the ultimate pharmaceutical R&D platform for drug development scientists. It covers the entire drug development pipeline — from identifying a biological target or researching a competitor drug, through synthesis and formulation, to preclinical evidence and regulatory documentation. The system is designed for both **analog-based development** (designing around an existing drug's patents) and **novel drug design** (discovering new chemical entities from scratch against a defined biological target).

All workflows are manually executable by scientists today. Each page is structured so that an AI window can be added later on the right side, receiving the page's full data context to answer questions and suggest next steps. An automated drug design agent — where a scientist describes a problem in natural language and the system designs a full development plan — is a planned future capability, not part of this version.

---

## User Personas

### Medicinal Chemist
Focused on finding, designing, and optimizing drug-like molecules. Primary workflows: target exploration, compound profiling, analog search, SAR tracking, virtual screening, ADMET comparison.

### Process / Formulation Scientist
Focused on taking a promising molecule and developing it into a manufacturable drug product. Primary workflows: synthesis planning, salt and polymorph screening, formulation planning, excipient compatibility, stability design, scale-up planning.

### Analytical Scientist
Focused on characterizing the compound and product, developing and validating methods. Primary workflows: method development, specification building, analytical experiment planning.

### Drug Development Manager
Needs a portfolio view of all projects, phase status, go/no-go decisions, and documentation for regulatory submissions. Primary workflows: dashboard, project phases, risk assessment, documentation.

---

## Drug Development Pipeline

BioIntel is organized around the following sequential development phases. Each project tracks which phase it is in, with explicit decision gates between phases.

```
Target Biology
     ↓
Drug Discovery
     ↓
Lead Optimization
     ↓  [Go/No-Go: Candidate Selection]
Drug Substance Development
     ↓
Drug Product Development
     ↓  [Go/No-Go: Formulation Lock]
Analytical Development
     ↓
Preclinical Development
     ↓  [Go/No-Go: IND Readiness]
Regulatory & Clinical
```

Each phase has a **status** (not started / in progress / complete / on hold) and a recorded **go/no-go decision** (with rationale) before the next phase begins. This decision trail is what the AI will later use to understand the project's history and current situation.

---

## Project Hierarchy

Every piece of work in BioIntel lives inside a **Project**. A project maps to a single drug candidate (one target molecule). The structure:

```
Project
  ├── Phase: Drug Discovery
  │     ├── DrugInvestigation (reference drug researched)
  │     └── AnalogCandidates (shortlisted from investigation)
  │
  ├── Phase: Lead Optimization
  │     ├── Compound (the chosen candidate molecule)
  │     ├── CompoundProperties (physicochemical, ADMET, safety)
  │     └── SAREntries (structure-activity observations)
  │
  ├── Phase: Drug Substance Development
  │     ├── SynthesisPlan(s) (retrosynthetic routes per analog)
  │     ├── SaltPolymorphScreen (screening plan + results)
  │     ├── ScaleUpPlan (process development milestones)
  │     └── Experiments [type: synthesis]
  │
  ├── Phase: Drug Product Development
  │     ├── FormulationPlan (dosage form, excipients, rationale)
  │     ├── StabilityPlan (ICH conditions and timepoints)
  │     └── Experiments [type: formulation, stability]
  │
  ├── Phase: Analytical Development
  │     ├── AnalyticalMethods (HPLC, NMR, etc.)
  │     ├── Specifications (purity, potency, impurities)
  │     └── Experiments [type: analytical]
  │
  ├── Phase: Preclinical Development
  │     ├── Studies (in vitro and in vivo)
  │     └── RiskAssessment
  │
  ├── Documentation (reports, regulatory packages, summaries)
  └── ChatSessions (AI assistant history per project)
```

---

## Module 1 — Target Biology & Disease Research

### Purpose
The entry point for **novel drug design** — when the scientist doesn't have a reference drug to start from. The scientist identifies a disease, finds the biological targets associated with it, selects a target, and retrieves all available structural and functional data about that target. This becomes the starting point for virtual screening and de novo compound design.

This module also serves the analog development workflow — the Disease Explorer already identifies known drugs, and the Target Explorer shows which biological targets those drugs act on.

### User Workflow

**Step 1: Disease Search**
- Scientist searches for a disease by name.
- The system returns a list of diseases with their EFO IDs, descriptions, and associated target counts.

**Step 2: Target–Disease Association Review**
- For the selected disease, the system shows all associated protein targets ranked by evidence score.
- Each target shows: gene symbol, protein name, UniProt accession, association score, and number of known drugs.
- Scientist selects a target of interest.

**Step 3: Target Profile**
- Full target detail view:
  - Protein identity (UniProt accession, gene name, organism, length)
  - Function and biological process annotation
  - Tissue and cell expression map
  - Disease associations with evidence types
  - Known binding sites and druggability assessment
  - PDB structures (list with resolution, method, coverage of binding site)
  - Known inhibitors / activators from ChEMBL bioactivity data
  - Link to Known Drugs for the disease this target is associated with

**Step 4: Choose Development Pathway**
From the Target Profile, the scientist can choose:
- **"Explore Known Drugs"** → navigates to Drug Intelligence pre-filtered to this disease/target (analog-based pathway)
- **"Start Virtual Screening"** → opens Virtual Screening with this target's PDB structure pre-loaded (novel drug design pathway)

### Pages
- `DiseaseExplorerPage` — disease search, target association table, known drugs table
- `TargetProfilePage` — full target detail with structure list, binding sites, known binders

### Required Data at Each Step
- Disease search: disease name, EFO ID
- Target associations: Open Targets association scores, UniProt accession
- Target profile: UniProt function annotation, tissue expression, PDB structure list, ChEMBL bioactivity data

### External Data Sources
| Source | Use |
|---|---|
| Open Targets Platform (GraphQL) | Disease search, target–disease associations, known drugs per indication |
| UniProt REST | Target protein function, expression, sequences, disease links |
| RCSB PDB REST | PDB structure list, resolution, method, deposit date |
| ChEMBL REST | Known binders / inhibitors, bioactivity IC50/Ki values |

---

## Module 2 — Drug Discovery

### Purpose
Supports both development pathways:
- **Analog pathway**: Research an existing drug fully, understand its patents, find structurally distinct analogs that preserve therapeutic effect.
- **Novel pathway**: Starting from a target, screen a virtual compound library for hits, or generate de novo candidates.

### 2A — Drug Intelligence

#### Purpose
Provides a complete profile of a known reference drug: its chemical identity, mechanism of action, production methods, formulation, clinical history, and patent landscape. This is the intelligence-gathering step before designing an analog.

#### User Workflow

**Step 1: Drug Search**
- Search for a drug by name (INN, brand name, or ChEMBL ID).
- Results list: drug name, approval status, indication, ChEMBL ID.

**Step 2: Drug Profile**
Full reference drug profile, assembled from multiple sources:
- **Structure & Identity**: SMILES, InChI, formula, molecular weight, stereochemistry (ChEMBL)
- **Mechanism of Action**: biological target, pathway, effect on disease (ChEMBL + Open Targets)
- **Formulation Details**: inactive ingredients, dosage form, route of administration, excipients (DailyMed / OpenFDA)
- **Clinical Trial History**: all trials filtered by this drug as intervention — phase, status, enrollment, outcome (ClinicalTrials.gov)
- **Synthesis Literature**: published synthesis routes from PubMed (`{drug_name} synthesis route`)
- **Patent Landscape**: patents covering this molecule, formulation, or process — number, title, assignee, filing date, derived expiry (SureChEMBL)

**Step 3: Patent Assessment**
- Scientist reviews the patent landscape to understand which structural features, process steps, and formulation components are claimed.
- The "View Claims" action on any patent fetches full claim text (Espacenet).

**Step 4: Start Analog Search**
- Clicking "Start Analog Search" creates a `DrugInvestigation` record and opens the Analog Workspace pre-loaded with this drug's SMILES.

#### Pages
- `DrugIntelligencePage` — search entry point
- `DrugProfilePage` — full reference drug profile in tabbed sections

---

### 2B — Patent Explorer

#### Purpose
Standalone patent search for scientists who want to search by molecule structure (SMILES) or by drug/keyword — independent of the Drug Intelligence workflow.

#### User Workflow
- Search by **drug name** or paste a **SMILES** structure.
- Results table: patent number, title, assignee, filing date, expiry date (filing + 20 years), jurisdiction.
- "View Claims" fetches full patent text from Espacenet.
- "Flag for Project" links the patent as a risk factor to the current project.

#### Pages
- `PatentExplorerPage`

---

### 2C — Virtual Screening (Novel Drug Design)

#### Purpose
Enables scientists to identify hit compounds for a protein target without starting from a known drug. The scientist provides a PDB structure (or selects one from the Target Profile), selects a binding site, and screens a compound library using molecular docking. Top hits are reviewed and can be added to the Analog Workspace or directly to a project.

#### User Workflow

**Step 1: Target Setup**
- Select a PDB structure for the target (list populated from Target Profile, or manually enter a PDB ID).
- Identify the binding site: either select from known active sites (fetched from PDB annotations) or define a box manually by residue range.

**Step 2: Library Selection**
- Choose a virtual screening library:
  - **FDA-Approved Drugs** (ChEMBL approved subset, ~2,500 compounds) — for drug repurposing
  - **Clinical Candidates** (ChEMBL phase 1–3 subset, ~15,000 compounds)
  - **Drug-Like Fragment Library** (ZINC fragment subset, ~50,000 compounds)
  - **Custom SMILES List** — paste or upload a list of SMILES

**Step 3: Docking Run**
- The system submits the docking job.
- Results table: compound SMILES, compound name (if known), docking score, PubChem CID (if matched), ChEMBL ID (if matched).
- 3D pose viewer shows the top-ranked compound in the binding site.

**Step 4: Hit Review & Shortlisting**
- Scientist reviews docking scores, lipophilicity, MW (Lipinski compliance shown inline).
- "Check ADMET" button runs pkCSM predictions for selected compounds.
- "Check Patents" button checks SureChEMBL for patent coverage.
- Scientist shortlists hits — shortlisted compounds can be:
  - Saved to a project as candidate compounds
  - Passed to the Analog Workspace for further analog search around the hit scaffold

#### Pages
- `VirtualScreeningPage` — binding site setup, library selection, docking results, hit review

#### External Data Sources
| Source | Use |
|---|---|
| RCSB PDB | Structure retrieval by PDB ID |
| AutoDock Vina (local/remote service) | Molecular docking |
| ZINC | Fragment and drug-like compound library |
| ChEMBL | Approved drug / clinical candidate SMILES library |
| pkCSM | ADMET predictions for hits |
| SureChEMBL | Patent coverage check for hits |

---

### 2D — Analog Workspace

#### Purpose
Starting from a reference drug's SMILES, find structurally similar compounds that may preserve the therapeutic effect but avoid the reference drug's patents. This is the bridge between Drug Intelligence and the development project.

#### User Workflow

**Step 1: Reference Drug Panel**
- Shows reference SMILES, 2D structure image, key properties.
- Similarity threshold slider (default 0.7 Tanimoto).

**Step 2: Candidate Pool**
- Similarity search returns compounds from PubChem with similarity scores and structure thumbnails.
- "Check Patents" overlays a `free` / `covered` / `unknown` badge on each candidate.
- "Run ADMET" runs pkCSM predictions on all free-to-operate candidates.

**Step 3: Shortlist**
- Scientist pins candidates to the shortlist.
- Side-by-side ADMET comparison (rows = endpoints, columns = candidates + reference drug).
- "Save to Project" creates or links to a project; all shortlisted candidates are linked.

#### Entry Modes
| Mode | Entry Point | Behavior |
|---|---|---|
| Drug search mode | Drug Intelligence → "Start Analog Search" | Full workflow; creates DrugInvestigation; saves to project; redirects to project page |
| Project mode | Project page → "Find Analog" (`?project=ID`) | Pre-loads existing shortlisted analogs; immediate PATCH on toggle; "Done" returns to project page |

#### Pages
- `AnalogWorkspacePage`

---

## Module 3 — Lead Optimization

### Purpose
Once a candidate molecule is identified (from analog search, virtual screening, or designed de novo), the scientist characterizes it fully, tracks what structural changes improve or hurt its properties, and makes the final selection before committing to development.

### 3A — Compound Profile

#### Purpose
Detailed characterization of the candidate compound: physicochemical properties, ADMET predictions, safety/toxicity, pharmacological targets, and similar known compounds.

#### Profile Sections
- **Structure & Identity**: 2D structure image, SMILES, InChI key, formula, molecular weight, ChEMBL ID, PubChem CID
- **Physicochemical Properties**: LogP, TPSA, HBD, HBA, rotatable bonds, Lipinski compliance (PubChem)
- **ADMET Profile**: solubility, Caco-2 permeability, BBB penetration, CYP metabolism, P-gp substrate, hERG liability, AMES mutagenicity, hepatotoxicity — color-coded (pkCSM)
- **Safety & Toxicity**: Tox21 active assay count, regulatory flags, REACH/GHS hazard codes (EPA CompTox)
- **Pharmacological Targets**: protein targets, binding affinities, mechanism of action (ChEMBL + UniProt)
- **Similar Known Compounds**: fingerprint-similar CIDs with structure thumbnails (PubChem)

#### Pages
- `CompoundProfilePage`

---

### 3B — SAR Tracker

#### Purpose
Structure-Activity Relationship tracking. As the scientist explores analogs and runs experiments, they record which structural modifications improved or worsened a specific property (potency, selectivity, solubility, metabolic stability, etc.). This builds a structured SAR log that the AI will later be able to query and reason over.

#### User Workflow

**Step 1: Add SAR Entry**
- Select the compound (from analog candidates or project compound list).
- Select the property being tracked (e.g., hERG IC50, solubility, CYP3A4 inhibition).
- Record the observed value and the structural change made vs. the parent compound.
- Note the verdict: improved / worsened / no change / mixed.

**Step 2: SAR Table**
- Table of all entries for the project: compound, structural change description, property, value, verdict, date.
- Columns are sortable and filterable by property type and verdict.

**Step 3: SAR Heatmap**
- Visual matrix: compounds (rows) × properties (columns), colored by verdict.
- Quickly shows which analogs are strong across all tracked properties.

#### Data Captured Per SAR Entry
| Field | Type |
|---|---|
| Compound (candidate) | FK |
| Parent compound | FK (nullable) |
| Structural modification | Text (free-text description) |
| Property tracked | Enum (potency / selectivity / solubility / permeability / metabolic_stability / herg / toxicity / other) |
| Observed value | Numeric + unit |
| Assay method | Text |
| Verdict | Enum (improved / worsened / no_change / mixed) |
| Rationale | Text |
| Experiment reference | FK → Experiment (nullable) |

#### Pages
- `SARTrackerPage` — entry form, SAR table, SAR heatmap

---

### 3C — Candidate Selection

A decision gate page before entering Drug Substance Development. The scientist reviews all shortlisted candidates side by side (ADMET, SAR, patent status) and formally selects one compound as the **development candidate**. The selection is recorded with a rationale, and the project advances to the Drug Substance phase.

**Comparison table**: each candidate column shows similarity score, patent status, ADMET flags, SAR verdict count, buyability assessment.

**Selection action**: clicking "Select as Development Candidate" locks the compound to the project and creates the Drug Substance phase record. Previous candidates remain linked to the project for reference.

#### Pages
- `CandidateSelectionPage`

---

## Module 4 — Drug Substance Development

### Purpose
Takes the selected development candidate and develops a manufacturable synthesis route: designing the synthetic pathway, screening for the best salt/polymorph form, developing process conditions, and planning scale-up.

### 4A — Synthesis Planning

Computer-aided synthesis planning for the target molecule. Full retrosynthetic analysis with inline reaction conditions.

#### Features (carried forward from v1, enhanced)
- Single-step retrosynthesis (ASKCOS)
- Multi-step retrosynthesis tree (ASKCOS)
- Inline reaction conditions per step (reagents, solvent, temperature, time)
- Per-precursor buyability check
- Forward prediction (in Advanced Tools, collapsed)
- Auto-run when redirected from project page with SMILES
- Auto-save to SynthesisPlan when project is linked
- Plan comparison across multiple analogs

#### Plan-Analog Structure
Each synthesis plan is linked to a specific analog candidate. At most one single-step plan and one multi-step plan per analog. Plans are created from the Analogs table on the project page.

#### Pages
- `SynthesisPlanningPage`
- `SynthesisPlanComparisonPage`

---

### 4B — Salt & Polymorph Screening

#### Purpose
Most APIs need to be in an appropriate solid form for bioavailability, stability, and manufacturability. This module helps the scientist plan and track a salt/polymorph screening campaign — identifying which solid form of the API is best suited for development.

#### User Workflow

**Step 1: Define Screening Objectives**
- State the goal: e.g., improve aqueous solubility, maximize thermal stability, avoid hygroscopic forms.
- Record baseline API properties (pKa, melting point, hygroscopicity).

**Step 2: Salt Former / Coformer Selection**
- Search the FDA-approved salt former list (common pharmaceutical counterions: HCl, maleate, tartrate, mesylate, etc.).
- Select a shortlist of counterions to screen.
- For cocrystal screening, select coformers from a curated GRAS list.
- For each candidate, the system shows the theoretical salt/cocrystal pKa delta and expected solubility impact.

**Step 3: Screening Plan**
- Define the screening matrix: which API form × which counterion/coformer × which solvent system.
- Auto-generates an experiment list — one experiment per condition.
- Each experiment captures: preparation method (slurry, evaporation, grinding), solvent, ratio, temperature.

**Step 4: Results Logging**
- For each screening experiment: enter characterization results (XRPD pattern, DSC melting point, TGA, visual appearance, observed form).
- System flags if a new crystalline form is observed vs. amorphous or unchanged API.

**Step 5: Form Selection**
- Review all forms: solubility, melting point, hygroscopicity, XRPD pattern.
- Select the preferred solid form with a recorded rationale.
- The selected form is locked to the project's Drug Substance record.

#### Data Captured
| Entity | Key Fields |
|---|---|
| `SaltPolymorphScreen` | project, objective, baseline_pka, baseline_melting_point |
| `SaltFormerCandidate` | screen, counterion_name, pka_delta, theoretical_solubility_impact |
| `SaltScreenExperiment` | candidate, prep_method, solvent, ratio, temperature, results_xrpd, results_dsc, results_tga, observed_form, notes |

#### External Data Sources
| Source | Use |
|---|---|
| FDA IIG (OpenFDA label data) | Approved pharmaceutical excipients / salt formers list |
| CCDC / CSD API | Known crystal structures for the API or its analogs |
| PubChem | pKa data for the API |

#### Pages
- `SaltPolymorphScreeningPage`

---

### 4C — Process Development & Scale-Up Planning

#### Purpose
Translates the bench-scale synthesis route into a process suitable for manufacturing. Tracks process parameters at each scale, documents critical process parameters (CPPs) and critical quality attributes (CQAs), and plans scale-up milestones.

#### User Workflow

**Step 1: Select Synthesis Route**
- Link to an existing SynthesisPlan as the starting route.
- Define the initial batch size (lab scale, e.g., 1 g).

**Step 2: Process Parameter Documentation**
- For each step in the synthesis route, document:
  - Critical process parameters (CPPs): reaction time, temperature, agitation rate, addition order, reagent equivalents
  - Critical quality attributes (CQAs): purity, yield, residual solvents, particle size
  - Process analytical technology (PAT) requirements

**Step 3: Scale-Up Milestones**
- Define scale-up stages: lab (1–10 g) → pilot (100 g – 1 kg) → manufacturing (1 kg+)
- For each stage: target batch size, equipment requirements, expected yield, risk factors.
- Go/no-go criteria per stage.

**Step 4: Impurity Profiling**
- Record known and potential impurities per step: type (starting material carryover, reaction by-product, degradation product), ICH classification (specified / unspecified), acceptable limit, control strategy.

#### Pages
- `ProcessDevelopmentPage`

---

## Module 5 — Drug Product Development

### Purpose
Transforms the developed drug substance (API in its selected solid form) into the final dosage form — a tablet, capsule, injection, patch, or other delivery vehicle. This module is entirely new in v2 and is one of the most important additions.

### 5A — Formulation Planning

#### Purpose
The scientist designs the drug product: selects the dosage form, identifies excipients for each functional role, and builds the full formulation composition with rationale.

#### User Workflow

**Step 1: Define the Drug Product Target**
- Target dose (mg of API per unit)
- Dosage form: tablet / capsule / oral solution / injectable / topical / transdermal patch / inhaled
- Route of administration
- Target patient population (drives swallowability, taste masking, pediatric considerations)
- Release type: immediate release / modified release / extended release / delayed release

**Step 2: Excipient Selection**

For each functional role in the formulation, the scientist selects excipients from the Excipient Library:

| Role | Examples |
|---|---|
| Diluent / Filler | Lactose, microcrystalline cellulose, mannitol |
| Binder | PVP, HPMC, starch |
| Disintegrant | Croscarmellose sodium, crospovidone |
| Lubricant | Magnesium stearate, stearic acid |
| Glidant | Colloidal silicon dioxide |
| Coating polymer | HPMC, Eudragit variants |
| Stabilizer | Antioxidants (BHT, ascorbic acid), chelating agents |
| Surfactant | SDS, Polysorbate 80 |
| Preservative (for liquids) | Benzalkonium chloride, parabens |
| Solubilizer (for injectables) | Cyclodextrins, PEG 400 |

For each excipient selected:
- Enter the function, quantity (% w/w or mg/unit), and rationale.
- The system checks the FDA Inactive Ingredient Guide (IIG) for the maximum approved level at this route of administration and flags any overages.

**Step 3: Compatibility Assessment**
- For each excipient in the formulation, the system flags known API–excipient incompatibilities based on the compound's functional groups and the excipient's reactivity profile.
- Risk levels: low / medium / high / critical.
- High and critical incompatibilities trigger a mandatory rationale text field.
- Compatibility data sourced from a curated pharmaceutical incompatibility library.

**Step 4: Formulation Summary**
- Full composition table: ingredient, role, quantity (mg/unit and %w/w), supplier grade specification, IIG compliance status.
- Manufacturing process description: granulation method (wet, dry, direct compression), coating process, fill/finish process for injectables.
- Rationale statement for the formulation approach.

#### Data Captured
| Entity | Key Fields |
|---|---|
| `FormulationPlan` | project, dosage_form, route, target_dose_mg, release_type, manufacturing_process, rationale, status |
| `FormulationComponent` | formulation_plan, excipient_id, function, quantity_mg, quantity_pct, iig_max_mg, iig_compliant, rationale |
| `CompatibilityFlag` | formulation_plan, excipient_id, risk_level, mechanism, rationale |

#### Pages
- `FormulationPlanningPage`

---

### 5B — Excipient Library

#### Purpose
A searchable reference database of pharmaceutical excipients. Scientists search for excipients by name, function, or route of administration and get regulatory status, IIG limits, known incompatibilities, and GRAS status.

#### Excipient Record Fields
- Common name and synonyms
- CAS number, molecular formula
- Functional categories (multi-select)
- Approved routes of administration
- Maximum level per route (from FDA IIG)
- GRAS status
- Known incompatibilities (e.g., magnesium stearate incompatible with moisture-sensitive APIs)
- Common supplier grades and specifications
- Relevant Ph. Eur. / USP monograph reference

#### Pages
- `ExcipientLibraryPage` — search + filter; detail view per excipient

#### External Data Sources
| Source | Use |
|---|---|
| FDA Inactive Ingredient Guide (OpenFDA label data) | Max approved levels per route |
| FDA GRAS Notices | GRAS status |
| USP/Ph. Eur. monograph references | Specification standards |

---

### 5C — Stability Planning

#### Purpose
Designs the stability study program for the drug substance and drug product, aligned with ICH guidelines (Q1A(R2) for long-term, Q1B for photostability).

#### User Workflow

**Step 1: Define Stability Objectives**
- Is this a drug substance stability study, drug product, or both?
- Intended storage condition for labeling (e.g., "Store below 25°C" → long-term condition: 25°C/60% RH).
- Accelerated condition: 40°C/75% RH.

**Step 2: Build Study Matrix**
- Select ICH storage conditions: Long-term (25°C/60%RH), Intermediate (30°C/65%RH), Accelerated (40°C/75%RH), Refrigerated (5°C), Frozen (-20°C).
- Define timepoints for each condition: 0, 1, 2, 3, 6, 9, 12, 18, 24, 36 months (configurable).
- Select tests to run at each timepoint: appearance, assay (potency), related substances (impurities), water content, dissolution, pH, microbial limits.

**Step 3: Sample Planning**
- Samples required per timepoint, containers, orientation (upright/inverted).
- Total sample count calculated automatically.

**Step 4: Results Logging**
- At each timepoint, enter test results.
- System flags out-of-specification (OOS) and out-of-trend (OOT) results based on ICH acceptance criteria.

**Step 5: Stability Summary**
- Graphical trend charts per test across timepoints.
- Auto-generated stability summary text (for regulatory submission) based on logged results.

#### Pages
- `StabilityPlanningPage`

---

## Module 6 — Analytical Development

### Purpose
Develops and validates the analytical methods needed to characterize the drug substance and drug product, and defines the specifications that the compound must meet for release.

### 6A — Analytical Method Development

#### Purpose
Plans and tracks analytical method development for characterization methods (HPLC purity, assay, dissolution, etc.).

#### Method Types
- HPLC (isocratic and gradient)
- NMR
- Mass Spectrometry (MS)
- Karl Fischer (water content)
- Dissolution
- Particle size analysis
- pH / osmolality (for liquids)
- Appearance / color / odor

#### User Workflow

**Step 1: Method Definition**
- Method name, type, purpose (identification / assay / purity / impurity / dissolution / water)
- Analyte(s) detected
- Instrument type
- Reference standards required

**Step 2: Development Experiments**
- Each method development experiment captures: column / instrument settings, mobile phase / solvent, run conditions, observed chromatographic parameters (retention time, resolution, tailing factor, theoretical plates).
- Verdict: suitable / not suitable / needs optimization.

**Step 3: Method Parameters (Final)**
- Record the validated / developed method parameters (column, mobile phase, gradient, flow rate, wavelength, runtime, LOD, LOQ).

**Step 4: Validation Planning** (tracked, not auto-run)
- Checklist of ICH Q2(R1) validation characteristics: specificity, linearity, range, accuracy, precision (repeatability, intermediate precision), LOD, LOQ, robustness.
- For each characteristic: planned experiment, result, pass/fail.

#### Pages
- `AnalyticalMethodPage` — per method

---

### 6B — Specification Builder

#### Purpose
Defines the release and shelf-life specifications for the drug substance and drug product.

#### Specification Structure

For each specification (drug substance or drug product):
- Test name
- Method reference (linked to an Analytical Method record)
- Acceptance criteria (limit: NMT, NLT, between, conforms to)
- Stage (release / shelf-life)
- Regulatory basis (pharmacopoeial / in-house / ICH)

The full specification sheet can be exported as a table formatted for inclusion in regulatory submissions.

#### Pages
- `SpecificationBuilderPage`

---

## Module 7 — Preclinical Development

### Purpose
Plans and tracks the non-clinical studies required to support an IND (Investigational New Drug) application and ultimately a marketing authorization. Covers in vitro mechanistic studies, ADMET profiling, efficacy models, and safety/toxicology studies.

### 7A — Preclinical Study Planner

#### Purpose
Plans in vitro and in vivo non-clinical studies. Each study is defined with its scientific objective, study design, species (for in vivo), expected endpoints, and success criteria.

#### Study Types
| Type | Examples |
|---|---|
| In vitro mechanistic | Receptor binding assay, enzyme inhibition (IC50), cell viability |
| In vitro ADMET | Caco-2 permeability, metabolic stability (microsomal), protein binding, CYP inhibition panel |
| In vivo PK | Single-dose PK (IV + oral), bioavailability, half-life |
| In vivo efficacy | Disease model (e.g., tumor xenograft, HFD mouse model) |
| In vivo safety / tox | Dose range finding, 28-day GLP tox, genotoxicity (Ames, micronucleus) |

#### Study Record Fields
- Study title, type, objective
- Species and strain (for in vivo)
- Dose levels and route of administration
- Number of animals per group (for in vivo)
- Primary and secondary endpoints
- Success criteria (go/no-go thresholds)
- Status (planned / in-progress / completed)
- Results summary and conclusion

#### Pages
- `PreclinicalStudyPlannerPage`

---

### 7B — ADMET Dashboard

#### Purpose
A unified view of all ADMET-relevant data for the project's compound: computational predictions (pkCSM), experimental measurements from preclinical studies, and comparison against development benchmarks.

#### Dashboard Sections
- **Computational ADMET** (pkCSM): solubility, Caco-2, BBB, CYP, hERG, AMES, hepatotoxicity — with traffic-light coloring
- **Experimental ADMET** (from logged study results): any endpoint with an experimental value overrides the computational prediction and is shown with a "Measured" badge
- **Development Benchmarks**: target ranges for each endpoint (scientist-defined, e.g., "aqueous solubility ≥ 0.1 mg/mL"); flagged as met / at-risk / failed

#### Pages
- `ADMETDashboardPage`

---

### 7C — Risk Assessment

Project-level risk dashboard. Displays a 2D risk heat map (probability vs. impact) with color-coded risk factors.

Risk categories:
- **Scientific/Technical**: synthesis complexity, formulation challenges, stability risks
- **Preclinical**: safety flags (hERG, hepatotoxicity), efficacy model translatability
- **IP/Regulatory**: patent freedom-to-operate, regulatory precedent
- **Operational**: reagent availability, manufacturing readiness, timeline

Risk factors can be generated by AI (from project context, literature, and compound properties) or entered manually. Each risk factor has: category, probability (1–5), impact (1–5), mitigation strategy, and owner.

#### Pages
- `RiskAssessmentPage`

---

## Module 8 — Research & Literature

### Purpose
Centralized literature and clinical intelligence tools. Used across all development phases for evidence gathering.

### 8A — Literature & Clinical Trials

#### Features
- **PubMed search**: keyword, author, title, journal, date range filters; abstract view; save to project as reference
- **ClinicalTrials.gov search**: condition + intervention filters, phase, status; study detail; save to project
- **Patents tab**: SureChEMBL and Espacenet search integrated alongside PubMed and ClinicalTrials

#### Pages
- `LiteraturePage` (tabbed: Literature / Clinical Trials / Patents)

---

## Module 9 — Regulatory & Documentation

### Purpose
Generates, manages, and exports regulatory-facing documents and internal summaries.

### 9A — Process Documentation

Document types:
| Document Type | Content |
|---|---|
| Process Summary | Synthesis route rationale, CPPs, CQAs, process validation plan |
| Risk Report | Risk heat map, risk factors, mitigations |
| Formulation Report | Drug product composition, excipient rationale, compatibility, IIG compliance |
| Stability Summary | Study design, results trend, proposed shelf life |
| ADMET Summary | Computational + experimental ADMET comparison, development readiness |
| Analog Development Report | Reference drug profile, patent gap analysis, selected analog, ADMET comparison, proposed route |
| IND CMC Package | Chemistry, Manufacturing, and Controls section for IND submission (Drug Substance + Drug Product sections) |
| Handoff Note | Internal handoff for transition between development phases or teams |

Each document can be:
1. AI-drafted (Claude) from project context
2. Manually authored in the built-in Markdown editor
3. Exported as PDF or DOCX

#### Pages
- `DocumentationPage`

---

## Module 10 — Project Management & Dashboard

### 10A — Dashboard

The landing page. Shows:
- All active projects as cards with phase indicator and status badge
- Development phase progress bars (how many phases complete vs. in progress)
- Recent activity feed (experiments, results, milestones across all projects)
- Pending decisions (projects awaiting a go/no-go decision at a phase gate)
- Quick actions: New Project, Open Chat, Search Compounds

### 10B — Project Page

Central hub for a project. Shows all content organized by development phase:

| Section | Content |
|---|---|
| **Header** | Compound name, structure image, phase badge, status |
| **Phase Tracker** | Visual pipeline: each phase with status (not started / in progress / complete / on hold) and go/no-go decision button |
| **Drug Discovery** | Reference drug, analog candidates table (SMILES, similarity, patent, plan status) |
| **Drug Substance** | Synthesis plans table (with Browse / Plan Experiments actions); salt screen summary |
| **Drug Product** | Formulation plan summary; stability study summary |
| **Analytical** | Methods list; specification sheet link |
| **Preclinical** | ADMET dashboard link; study list |
| **Experiments** | All experiments across all types, filterable by phase |
| **Documents** | All documents with type badges |

### 10C — Project Setup

Wizard for creating or editing a project. Captures:
- Project name, description
- Development pathway: **Analog-based** (start from a known drug) or **Novel design** (start from a target)
- Phase entry point: which phase is this project starting at?
- Compound attachment: search PubChem / ChEMBL or paste SMILES directly

---

## Module 11 — AI Assistant (Existing)

Per-project and global chat assistant powered by Claude. Uses tool-calling to query all integrated external APIs. Sessions are saved per project and can be resumed at any time. Every response cites the data sources used.

---

## AI Architecture (Planned — Not Built in v2)

### Per-Page AI Window

Every page in the application will have a collapsible AI window on the right side. The window receives the full data context of the current page and maintains a short per-page conversation history. The window appears as a right-side panel (not a full-page chat). Each context call packages:

- The page's primary entity (project, compound, synthesis plan, formulation plan, etc.)
- All data currently visible on the page
- The project's phase status and recent activity
- A system prompt specific to the page type (e.g., the formulation page AI knows about excipient chemistry)

This is separate from the global Chat Assistant (Module 11), which is more powerful and context-rich but requires navigating away from the page being worked on.

### Automated Drug Design Agent (Planned)

A natural-language interface where the scientist describes a problem ("I need to treat Type 2 diabetes with a mechanism that avoids GLP-1 receptor agonists") and the system automatically:
1. Identifies relevant biological targets
2. Searches known drugs for those targets
3. Identifies patent landscape constraints
4. Generates a set of analog candidates
5. Profiles their ADMET
6. Proposes a development plan with a synthesis route and formulation approach
7. Produces a structured project with all entities pre-populated

This agent will use BioIntel's own pages, APIs, and data models as its toolset — not external general-purpose tools. The structured data models in this specification (SynthesisPlan, FormulationPlan, SAREntry, etc.) are what the agent will write to and read from.

---

## Navigation Structure

```
BioIntel
│
├── Dashboard
│
├── Drug Discovery
│   ├── Disease & Target Explorer
│   ├── Drug Intelligence
│   ├── Patent Explorer
│   ├── Virtual Screening
│   └── Analog Workspace
│
├── Projects
│   └── [Project List + New Project]
│
│   (Per-Project Navigation — visible when inside a project)
│   ├── Overview (Project Page)
│   ├── Lead Optimization
│   │   ├── Compound Profile
│   │   ├── SAR Tracker
│   │   └── Candidate Selection
│   ├── Drug Substance
│   │   ├── Synthesis Planning
│   │   ├── Salt & Polymorph Screening
│   │   └── Process Development
│   ├── Drug Product
│   │   ├── Formulation Planning
│   │   ├── Excipient Library
│   │   └── Stability Planning
│   ├── Analytical
│   │   ├── Methods
│   │   └── Specifications
│   ├── Preclinical
│   │   ├── ADMET Dashboard
│   │   ├── Study Planner
│   │   └── Risk Assessment
│   ├── Experiments
│   └── Documents
│
├── Research
│   └── Literature & Clinical Trials
│
└── Chat Assistant
```

---

## External Data Sources

| Source | Purpose | Module(s) |
|---|---|---|
| **Open Targets** (GraphQL) | Disease search, target-disease associations, known drugs | Target Biology, Drug Discovery |
| **UniProt REST** | Protein function, expression, sequence, PDB cross-refs | Target Biology, Compound Profile |
| **RCSB PDB REST** | Protein 3D structures, binding sites | Target Biology, Virtual Screening |
| **ChEMBL REST** | Drug identity, mechanism, bioactivity, approved drugs | Drug Intelligence, Compound Profile, Virtual Screening |
| **PubChem PUG REST** | Compound identity, physicochemical properties, similarity search | Compound Profile, Analog Workspace |
| **DailyMed REST** | Drug formulation details, inactive ingredients, labeling | Drug Intelligence |
| **SureChEMBL REST** | Patent structure search, patent compound registry | Patent Explorer, Analog Workspace, Virtual Screening |
| **Espacenet OPS REST** | Full patent text and claims | Patent Explorer, Drug Intelligence |
| **pkCSM REST** | ADMET predictions from SMILES | Compound Profile, Analog Workspace, Virtual Screening |
| **EPA CompTox** | Toxicity data, Tox21 bioassay results | Compound Profile |
| **ASKCOS REST** | Retrosynthesis, forward prediction, reaction conditions, buyability | Synthesis Planning |
| **NIST WebBook** | IR/MS reference spectra | Synthesis Planning |
| **ClinicalTrials.gov API v2** | Clinical trial search by condition/drug | Drug Intelligence, Literature |
| **PubMed E-utilities** | Literature search, abstracts | Drug Intelligence, Literature, Risk Assessment |
| **OpenFDA** | FDA guidance, inactive ingredient guide (IIG), drug labels | Formulation Planning, Excipient Library, Regulatory |
| **FDA GRAS (OpenFDA)** | Excipient GRAS status | Excipient Library |
| **AutoDock Vina** | Molecular docking engine | Virtual Screening |
| **ZINC** | Virtual screening compound libraries | Virtual Screening |
| **CCDC / CSD API** | Crystal structure data for salt/polymorph screening | Salt & Polymorph Screening |
| **Claude API** | AI chat assistant, document drafting, experiment interpretation | All modules |

---

## Database Schema — New Tables (v2 Additions)

The following tables are new in v2. Full schema for existing tables is in `v1/technical.md`.

### `project_phases`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | |
| phase | VARCHAR(30) | discovery / lead_optimization / drug_substance / drug_product / analytical / preclinical / regulatory |
| status | VARCHAR(20) | not_started / in_progress / complete / on_hold |
| decision | VARCHAR(10) | go / no_go / null |
| decision_rationale | TEXT | |
| decided_at | DATETIME | |
| created_at | DATETIME | auto_now_add |

### `sar_entries`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | |
| compound_id | INTEGER FK → compounds | the modified compound |
| parent_compound_id | INTEGER FK → compounds | nullable; the parent structure |
| structural_modification | TEXT | free-text description of the change |
| property | VARCHAR(30) | potency / selectivity / solubility / permeability / metabolic_stability / herg / toxicity / other |
| observed_value | FLOAT | |
| unit | VARCHAR(30) | |
| assay_method | TEXT | |
| verdict | VARCHAR(20) | improved / worsened / no_change / mixed |
| rationale | TEXT | |
| experiment_id | INTEGER FK → experiments | nullable |
| created_at | DATETIME | auto_now_add |

### `formulation_plans`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | |
| dosage_form | VARCHAR(30) | tablet / capsule / oral_solution / injectable / topical / patch / inhaled |
| route_of_administration | VARCHAR(30) | oral / parenteral / topical / inhalation / transdermal |
| target_dose_mg | FLOAT | |
| release_type | VARCHAR(30) | immediate / modified / extended / delayed |
| manufacturing_process | TEXT | |
| rationale | TEXT | |
| status | VARCHAR(20) | draft / active / locked |
| created_at | DATETIME | auto_now_add |
| updated_at | DATETIME | auto_now |

### `formulation_components`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| formulation_plan_id | INTEGER FK → formulation_plans | |
| excipient_name | VARCHAR(255) | |
| excipient_id | INTEGER FK → excipients | nullable |
| function | VARCHAR(50) | diluent / binder / disintegrant / lubricant / glidant / coating / stabilizer / surfactant / preservative / solubilizer / other |
| quantity_mg | FLOAT | per unit |
| quantity_pct | FLOAT | %w/w |
| iig_max_mg | FLOAT | nullable; from IIG lookup |
| iig_compliant | BOOLEAN | nullable |
| rationale | TEXT | |

### `compatibility_flags`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| formulation_plan_id | INTEGER FK → formulation_plans | |
| excipient_name | VARCHAR(255) | |
| risk_level | VARCHAR(10) | low / medium / high / critical |
| mechanism | TEXT | reason for incompatibility |
| rationale | TEXT | scientist override rationale if accepted |

### `excipients`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| name | VARCHAR(255) | |
| synonyms | JSON | list of alternative names |
| cas_number | VARCHAR(20) | |
| formula | VARCHAR(100) | |
| functions | JSON | list of functional categories |
| routes | JSON | list of approved administration routes |
| iig_limits | JSON | `{"oral": 500, "parenteral": 50}` mg limits |
| gras | BOOLEAN | |
| known_incompatibilities | JSON | list of functional groups or compound types |
| usp_monograph | VARCHAR(100) | |
| ph_eur_monograph | VARCHAR(100) | |

### `salt_polymorph_screens`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | |
| objective | TEXT | |
| baseline_pka | FLOAT | nullable |
| baseline_melting_point | FLOAT | nullable |
| selected_form | VARCHAR(255) | nullable; the chosen solid form |
| selection_rationale | TEXT | |
| status | VARCHAR(20) | planned / in_progress / complete |
| created_at | DATETIME | auto_now_add |

### `salt_screen_candidates`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| screen_id | INTEGER FK → salt_polymorph_screens | |
| counterion_name | VARCHAR(255) | |
| cas_number | VARCHAR(20) | nullable |
| pka_delta | FLOAT | nullable |
| theoretical_solubility_impact | VARCHAR(30) | improved / neutral / decreased / unknown |

### `salt_screen_experiments`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| candidate_id | INTEGER FK → salt_screen_candidates | |
| prep_method | VARCHAR(30) | slurry / evaporation / grinding / spray_dry |
| solvent | VARCHAR(100) | |
| ratio | VARCHAR(50) | e.g. "1:1 API:counterion" |
| temperature_c | FLOAT | |
| results_xrpd | TEXT | |
| results_dsc | TEXT | |
| results_tga | TEXT | |
| observed_form | VARCHAR(30) | crystalline / amorphous / unchanged / mixed |
| notes | TEXT | |
| created_at | DATETIME | auto_now_add |

### `stability_plans`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | |
| material_type | VARCHAR(20) | drug_substance / drug_product |
| intended_storage_condition | VARCHAR(100) | e.g. "Store below 25°C" |
| status | VARCHAR(20) | planned / in_progress / complete |
| created_at | DATETIME | auto_now_add |

### `stability_conditions`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| stability_plan_id | INTEGER FK → stability_plans | |
| condition_name | VARCHAR(50) | long_term / intermediate / accelerated / refrigerated / frozen / photostability |
| temperature_c | FLOAT | |
| humidity_rh | FLOAT | nullable |
| timepoints | JSON | list of months: [0, 1, 3, 6, 12, 24] |

### `stability_results`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| condition_id | INTEGER FK → stability_conditions | |
| timepoint_months | FLOAT | |
| test_results | JSON | `{"assay": 99.2, "impurity_total": 0.3, "appearance": "white powder"}` |
| oos_flags | JSON | list of tests that failed acceptance criteria |
| recorded_at | DATETIME | auto_now_add |
| notes | TEXT | |

### `analytical_methods`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | |
| name | VARCHAR(255) | |
| method_type | VARCHAR(30) | hplc / nmr / ms / kf / dissolution / particle_size / appearance / ph / osmolality |
| purpose | VARCHAR(30) | identification / assay / purity / impurity / dissolution / water |
| analytes | JSON | list of analytes detected |
| instrument_type | VARCHAR(100) | |
| final_parameters | JSON | column, mobile phase, gradient, flow rate, wavelength, etc. |
| status | VARCHAR(20) | in_development / developed / validated |
| created_at | DATETIME | auto_now_add |

### `specifications`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | |
| material_type | VARCHAR(20) | drug_substance / drug_product |
| tests | JSON | list of `{test, method_id, criteria_type, criteria_value, stage, basis}` |
| version | VARCHAR(10) | |
| status | VARCHAR(20) | draft / approved |
| created_at | DATETIME | auto_now_add |

### `preclinical_studies`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | |
| title | VARCHAR(255) | |
| study_type | VARCHAR(30) | in_vitro_mechanistic / in_vitro_admet / in_vivo_pk / in_vivo_efficacy / in_vivo_tox |
| objective | TEXT | |
| species | VARCHAR(50) | nullable; for in vivo |
| dose_levels | JSON | nullable |
| primary_endpoints | JSON | |
| success_criteria | TEXT | |
| status | VARCHAR(20) | planned / in_progress / completed |
| results_summary | TEXT | |
| conclusion | VARCHAR(10) | go / no_go / inconclusive / null |
| created_at | DATETIME | auto_now_add |

### `target_profiles` (for Virtual Screening entry point)
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| uniprot_id | VARCHAR(20) | |
| gene_symbol | VARCHAR(50) | |
| protein_name | VARCHAR(255) | |
| organism | VARCHAR(100) | |
| pdb_ids | JSON | list of PDB IDs for this target |
| selected_pdb_id | VARCHAR(10) | nullable; chosen for docking |
| binding_site_definition | JSON | residue range or coordinates for docking box |
| notes | TEXT | |
| created_at | DATETIME | auto_now_add |

### `virtual_screening_runs`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| target_profile_id | INTEGER FK → target_profiles | |
| library | VARCHAR(30) | fda_approved / clinical_candidates / fragments / custom |
| custom_smiles | JSON | nullable; list of SMILES for custom library |
| status | VARCHAR(20) | pending / running / complete / failed |
| result_count | INTEGER | |
| created_at | DATETIME | auto_now_add |

### `virtual_screening_hits`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| run_id | INTEGER FK → virtual_screening_runs | |
| smiles | TEXT | |
| pubchem_cid | INTEGER | nullable |
| chembl_id | VARCHAR(20) | nullable |
| compound_name | VARCHAR(255) | nullable |
| docking_score | FLOAT | (kcal/mol; more negative = better) |
| lipinski_compliant | BOOLEAN | |
| patent_status | VARCHAR(20) | free / covered / unknown |
| admet_data | JSON | nullable; pkCSM predictions |
| shortlisted | BOOLEAN | default False |

---

## UPDATE 1 — Pipeline Restructure & Workflow Fixes

### What Changed

#### 1. Pipeline Navigation Redesign
The sidebar navigation was redesigned from 9 flat numbered steps to 7 grouped phases, each with sub-items. This matches the actual drug development pipeline and makes the progression clear.

| Phase | Sub-items |
|---|---|
| 1 Discovery | Project Overview · Analog Workspace |
| 2 Lead Optimization | SAR Tracker |
| 3 Drug Substance | Synthesis Hub · Salt & Polymorph Screen · Process Development |
| 4 Drug Product | Formulation Planning · Stability Planning |
| 5 Analytical | Methods · Specifications |
| 6 Preclinical | ADMET Dashboard · Study Planner |
| 7 Regulatory | Documents |

Phase headers are non-clickable labels. Sub-items are the actual navigation links.

#### 2. Workflow Clarification: SAR vs Synthesis Experiments

SAR entries and synthesis experiments are **different things** and belong in different phases:

- **SAR (Lead Optimization)**: Records the *biological activity* of a compound measured in a lab assay (IC50, Ki, EC50). Answers: "does this structural change make the molecule more or less potent?" Scientists must synthesize the compound and run a bioassay first — SAR is the result they log.
- **Synthesis Experiments (Drug Substance)**: Records the *chemistry* of actually making the molecule — reaction conditions, yield, purity. Answers: "can we physically make this compound and how well?"

Section 2 (Lead Optimization) now contains only SAR. Section 3 (Drug Substance) contains synthesis work.

#### 3. Synthesis Hub — New Page

A dedicated **Synthesis Hub** page (`/projects/:id/synthesis`) replaces the scattered analog/synthesis/experiment content that was split across the project edit page and the standalone synthesis planning page.

The Synthesis Hub shows three sections in one place:
1. **Analog Candidates** — shortlisted analogs from the analog workspace, with synthesis plan status per candidate (Single-Step: done/pending, Multi-Step: done/pending). "Plan →" buttons launch the synthesis analysis page pre-filled.
2. **Synthesis Plans** — all plans across all analogs, with Browse, Plan Experiments, and Compare actions.
3. **Synthesis Experiments** — all synthesis-type experiments linked to this project.

The standalone `/synthesis` analysis page (retrosynthesis + tree) remains as the drill-down tool reached from the hub.

#### 4. Reference Drug in Project Creation

Reference drug selection was moved to the project **creation** flow (not just the edit page). For analog-based projects, a "Reference Drug" section appears on the create form after the pathway selector. The user can search ChEMBL and select a reference drug as part of creating the project. This creates the `DrugInvestigation` record immediately after the project is saved.

#### 5. Attach Compound Removed

The "Attach Compound" section in project creation was removed. It was a v1 artifact with no defined role in the v2 analog-based workflow. The reference drug (via `DrugInvestigation`) and analog candidates (via `AnalogCandidate`) replace it.

#### 6. Candidate Selection — Formal Development Candidate Gate

The Candidate Selection page now has a formal **"Select as Development Candidate"** action per analog row. When clicked, the user confirms and the analog is marked as the selected development candidate (`AnalogCandidate.selected = True`). A success banner appears with a direct link to "Begin Synthesis Planning →".

This formalises the gate between Lead Optimization and Drug Substance that was previously missing.

#### 7. Schema Addition

| Table | Field | Type | Notes |
|---|---|---|---|
| `analog_candidates` | `selected` | BOOLEAN | default False; marks the formally chosen development candidate |

---

## UPDATE 2 — Process Development Redesign

### What Changed

#### 1. Process Development Page — Full Rewrite

`ProcessDevelopmentPage` previously showed a synthesis experiment table identical to the Synthesis Hub — duplicated content with no distinct value. The page has been rewritten to reflect its actual purpose per §4C: translating a bench synthesis route into a manufacturable process.

The new page contains four sections:

**Section 1 — Process Route Selector**
A dropdown populated from `GET /api/synthesis-plans/?project=:id` lets the scientist select one existing synthesis plan as the reference route for all scale-up work. A "View Route →" button opens the synthesis analysis page for that plan. A summary card below the selector shows plan type, status, experiment count, and target SMILES.

**Section 2 — Scale-Up Milestones**
A fixed three-stage table: Lab (1–10 g) → Pilot (100 g–1 kg) → Manufacturing (1 kg+). For each stage the scientist fills in:

| Field | Input Type |
|---|---|
| Target batch size | Text (e.g. "5 g") |
| Equipment notes | Textarea |
| Expected yield (%) | Number |
| Status | Dropdown: planned / in_progress / complete / on_hold |
| Notes / risk factors | Textarea |

**Section 3 — CPP / CQA Notes**
A freeform monospace textarea for documenting Critical Process Parameters (reaction time, temperature, agitation, addition order, reagent equivalents) and Critical Quality Attributes (purity, yield, residual solvents, particle size) per synthesis step.

**Section 4 — Impurity Profile**
An add/remove table for tracking known and potential impurities. Each entry captures:

| Field | Values |
|---|---|
| Impurity name | Free text |
| Type | by_product / starting_material / degradant / solvent_residue / other |
| ICH classification | specified / unspecified / genotoxic |
| Acceptable limit | Free text (e.g. "≤ 0.15%") |

Genotoxic impurities are highlighted with a red badge.

#### 2. What Was Removed

- The synthesis experiment table that was previously shown on this page (it duplicated the Synthesis Hub's experiment section and belonged there, not here).
- The "Go to Synthesis Planning" link (replaced by the inline route selector).

#### 3. Data Persistence

All Process Development page state (milestones, CPP notes, impurities) is currently client-side only — it does not persist across browser sessions. A future update will add backend models (`ScaleUpPlan`, `ImpurityProfile`) and API endpoints to persist this data per project.

---

## UPDATE 3 — Salt & Polymorph Screening — Full Redesign

### Reference Page Standard

**The Salt & Polymorph Screening page (`SaltPolymorphScreeningPage`) is the reference implementation for all future domain pages in BioIntel.** Every page built from this point forward should match its standard of scientific depth, UX structure, and data completeness. When reviewing a new page, compare it against this benchmark.

What "screening page quality" means in practice:

| Dimension | What it looks like |
|---|---|
| **Scientific accuracy** | Fields map to real lab concepts a scientist would recognize. Choices are domain-correct (prep methods, ICH classifications, pKa delta rule). Helper text explains *why* a field matters, not just what it is. |
| **Preset shortcuts** | Common values are one click away. Scientists shouldn't type "Hydrochloride (HCl)" — they click it from a pre-populated list. |
| **Sequential workflow** | Complex pages use tabs or sections that mirror the natural scientific order (define → select candidates → run experiments → interpret results). |
| **Always-visible entity list** | Every collection of saved records (screens, candidates, plans) is shown as a persistent list, not hidden until there are "enough" of them. |
| **Inline feedback** | Saves confirm with a brief "✓ Saved" signal. Deletes ask for confirmation with the item name. |
| **Cascading actions** | Deleting a parent record removes all children. The UI communicates what will be deleted before confirming. |
| **Color-coded status** | Categorical outcomes (crystalline / amorphous / genotoxic / improved) use a consistent color map applied everywhere that concept appears. |

### What Changed in the Screening Page

The original screening page had: screen type selector, a rationale field, a simple candidate table (counterion name, solubility, melting point, hygroscopicity), and a basic create-screen form. It returned a 400 on screen creation (serializer bug) and a 500 on candidate creation (SQLite legacy column constraint).

The redesigned page has:

**Four-tab workflow:**

1. **Setup & Baseline** — screen type, objective, and full baseline API characterization: pKa (with ΔpKa rule explanation), melting point, LogP, aqueous solubility, hygroscopicity (four-tier classification), XRPD/DSC/TGA notes on the free form.

2. **Candidates** — 19 common pharmaceutical counterion presets (HCl, HBr, maleate, tartrate, mesylate, fumarate, Na, K, Ca, Mg, etc.) as one-click chips; 7 polymorph form presets for polymorph screens; manual add form with CAS, type, pKa, theoretical solubility impact.

3. **Experiments** — per-candidate experiment logging with: prep method (7 choices: slurry, slow evaporation, grinding, spray drying, antisolvent, cooling crystallization), solvent system, API:counterion ratio, temperature, XRPD pattern description, DSC (melting point, enthalpy), TGA (weight loss onset), visual appearance, aqueous solubility measurement, and observed solid form (5 choices with color coding: crystalline=green, amorphous=amber, oily=red, mixed=purple, unchanged=grey).

4. **Results & Selection** — comparison table across all candidates showing experiment count, best observed form, best measured solubility, theoretical solubility delta. "Select" button marks preferred form. Form selection decision records selected form name and full scientific rationale. Locked form shows "→ Process Development" CTA.

**Campaigns list** — always-visible card listing all screening campaigns. Multiple campaigns of the same type are auto-numbered (Salt Screen 1, Salt Screen 2). Each row shows label, objective preview, status badge, candidate count, and a Remove button with cascading confirmation.

### Bugs Fixed

| Bug | Fix |
|---|---|
| 400 on screen creation | `SaltPolymorphScreenSerializer` lacked `read_only_fields` for `project` — DRF validated it as required before `perform_create` injected it |
| 500 on candidate creation (`counterion_or_polymorph NOT NULL`) | Legacy column existed in DB with NOT NULL and no default; Django no longer included it in INSERTs after it was removed from the model. Fixed by re-adding it to the model class with `blank=True, default=''` |
| 500 on candidate creation (`hygroscopicity NOT NULL`) | Same root cause, same fix |
| Setup form blank after selecting a screen | `selectScreen()` was not calling `loadScreenIntoForm()` on initial load |
| Setup form stale after creating a screen | `createScreen()` called `loadScreenIntoForm()` then immediately reset `screenForm` with an explicit reassignment, overriding it. Fixed by separating creation form (`newScreenForm`) from editing form (`screenForm`) |
| Screen selector hidden for single screen | Chip bar was conditionally rendered only when `screens.length > 1`. Replaced with a permanent campaigns list card. |

---

## UPDATE 4 — Formulation Planning & Stability Planning — Full Redesign

### Pages Rebuilt to Reference Standard

Both pages had a creation 400 error and minimal scientific content. Both have been fully rewritten to match the Reference Page Standard established in UPDATE 3.

---

### 5A — Formulation Planning — What Changed

The original page had a flat form (dosage form, route, release type, rationale) and a basic composition table with no preset excipients, no compatibility workflow, and no tab structure. It returned a 400 on plan creation.

The redesigned page has:

**Header summary bar** — always visible once a plan exists: dosage form, route, target dose, release type, component count, and compatibility flag count (critical shown in red, warnings in orange).

**Four-tab workflow:**

1. **Target Definition** — dosage form, route of administration (with full label: "Oral (PO)", "Intravenous (IV)", etc.), release type (IR/MR/ER/DR with label), target dose (mg), formulation rationale textarea, manufacturing process textarea (with placeholder showing a complete wet granulation narrative). Three info cards below the form explain BCS Classification, API Properties Impact, and Bioavailability Target — linking the formulation choices to upstream drug substance data.

2. **Excipient Selection** — live composition tracker bar showing total `%w/w` with color-coded fill (green at ~100%, orange when incomplete, red when over). Current composition table (component name, functional role badge in blue, concentration, grade, supplier, notes). Add-component form with 11 functional role choices. **Preset excipient chips** in 7 categories (37 total presets):
   - Diluents: MCC Avicel PH102, Lactose Monohydrate, Mannitol, Dibasic Calcium Phosphate, Sorbitol — each with typical %w/w range and formulation notes on hover
   - Binders: HPMC E5, PVP K30, HPC LF, Copovidone VA64
   - Disintegrants: Croscarmellose Sodium (Ac-Di-Sol), Sodium Starch Glycolate, Crospovidone (PVPP)
   - Lubricants: Magnesium Stearate (IIG 1.5%), PRUV / Sodium Stearyl Fumarate (IIG 2.0%), Stearic Acid
   - Glidants: Colloidal Silicon Dioxide Aerosil 200 (IIG 1.0%), Talc
   - Coating Agents: HPMC E5 clear, Eudragit L30D-55 (enteric), Eudragit RL/RS (sustained release)
   - Surfactants/Solubilizers: Polysorbate 80 (IIG 25 mg/dose), SLS, Vitamin E TPGS
   - Preservatives: Benzalkonium Chloride (IIG 0.03%), Methylparaben (IIG 0.18%), Propylparaben (IIG 0.02%)
   
   Clicking a preset pre-fills the add-component form with name, grade, and formulation notes — the scientist only needs to fill in concentration.

3. **Compatibility** — color-coded severity badges (CRITICAL=red, WARNING=orange, INFO=blue). Inline add-flag form (component A, component B, flag type, severity, evidence/literature reference). "Run Auto-Check" button triggers the backend compatibility check. **Reference guidance table** (always visible): six known high-risk interaction patterns with mechanism and mitigation — primary amine + lactose (Maillard), over-lubrication with Mg stearate, carboxylic acid API + Mg stearate, cationic drug + SLS, Eudragit plasticizer ratio, oxidation-prone API + Polysorbate 80.

4. **Summary** — 8-cell summary grid (dosage form, route, dose, release, component count, total concentration colored by balance, flag count, status); rationale and manufacturing process text below; full composition table reprinted.

### Bugs Fixed

| Bug | Fix |
|---|---|
| 400 on plan creation | `FormulationPlanSerializer` lacked `read_only_fields` for `project` — DRF validated it as required before `perform_create` injected it |

---

### 5C — Stability Planning — What Changed

The original page had a two-field plan form (material type, intended storage condition), a flat ICH preset button row, a condition add-form, and a "Log Result" form with 5 fields. It returned a 400 on plan creation.

The redesigned page has:

**Header summary bar** — material type, storage claim, condition count, total result count, OOS flag count (red when > 0), OOT flag count (orange when > 0), plan status.

**Four-tab workflow:**

1. **Study Objectives** — material type selector, intended storage condition selector (dropdown with 6 options). Below the form, a full **ICH Q1A(R2) reference table** listing all 6 study conditions with temperature, humidity, minimum duration, and recommended timepoints. A two-column **Recommended Test Attributes** card distinguishes Drug Substance tests (XRPD, residual solvents, water content, particle size, assay NLT 98%, ICH degradant limits) from Drug Product tests (dissolution, microbial quality, container closure integrity, hardness/friability).

2. **Study Matrix** — six color-coded **ICH Q1A(R2) preset buttons** (long-term=green, intermediate=blue, accelerated=orange, refrigerated=purple, frozen=cyan, photostability=red-orange) each showing the condition label, temperature/RH, and the relevant ICH guideline note. Clicking a preset pre-fills the add-condition form. Conditions table shows ICH category dot, temperature, RH, light exposure, results logged count, and OOS/OOT badges per condition. **ICH timepoint chips** at the bottom showing all standard timepoints (T0 through 60 months, with week equivalents).

3. **Results** — OOS and OOT alert banners appear at the top when flags are present. Log Result form: condition dropdown, timepoint selector (ICH standard timepoints as labeled options), and 7 test fields: Assay (%), Total Degradants (%), pH, Water Content (%), Dissolution (%), Appearance, Notes. **Two styled checkbox tiles** — OOS (red highlight when checked) and OOT (orange highlight when checked) — communicate the significance of each flag type. Results table for the selected condition shows color-coded assay column (red < 97%, orange < 98–97%, green ≥ 98%), degradant warning when > 1.0%, dissolution warning when < 80%; OOS rows highlighted in red, OOT rows in yellow. Overview table when no condition is selected shows per-condition summary (result count, last timepoint, min assay, max degradants, flag status).

4. **ICH Summary** — 6-cell summary grid. Conditions status grid: one card per condition with color-coded left border matching its ICH category. **ICH Q1A(R2) Compliance Checklist** with live status checking: long-term condition defined (checks for 25°C condition), accelerated condition defined (checks for 40°C condition), photostability done (checks for lux·h exposure value), OOS investigation documented, 12-month data available — each showing ✓ Done / ✗ Missing / ○ Pending.

### Model Change

`StabilityResult` gained two new fields:

| Field | Type | Notes |
|---|---|---|
| `water_content_pct` | FLOAT nullable | Karl Fischer water content per timepoint |
| `dissolution_pct` | FLOAT nullable | % dissolved (USP apparatus, at specified time) |

Migration: `0010_stability_result_extra_fields`

### Bugs Fixed

| Bug | Fix |
|---|---|
| 400 on plan creation | `StabilityPlanSerializer` lacked `read_only_fields` for `project` — same DRF serializer pattern as previous pages |

---

### Pattern Confirmed: DRF 400 on Creation

Every page that creates a record with a `project` FK via `perform_create(serializer.save(project_id=self.kwargs['pk']))` will fail with 400 unless the serializer marks `project` as read-only. DRF validates all fields as required before `perform_create` injects the value.

**Rule**: Any serializer whose view uses `perform_create` to inject `project_id` must include:
```python
read_only_fields = ('project', 'created_at', 'updated_at')
```

This has now been applied to: `SaltPolymorphScreenSerializer`, `FormulationPlanSerializer`, `StabilityPlanSerializer`, `AnalyticalMethodSerializer`, `SpecificationSerializer`.

---

## UPDATE 5 — Analytical Development — Full Redesign

### Pages Rebuilt to Reference Standard

Both Analytical Development pages had minimal scientific content and a 400 on record creation. Both have been fully rewritten to match the Reference Page Standard (UPDATE 3).

---

### 6A — Analytical Method Development — What Changed

The original page was a single-panel list with a flat creation form and a basic method details view. It had no method-type-specific parameters, no development log, no validation tracking, and no ICH Q2(R1) content.

The redesigned page has:

**Two-column layout** — 300 px left panel (method list + ICH Q2(R1) quick reference) and a full-width right detail panel. Methods are grouped by type with a color-coded dot per type.

**Create method modal** — method name, type, purpose, instrument (with datalist populated from `PRESET_INSTRUMENTS` per selected type — e.g., 6 HPLC instruments, 4 GC instruments, 4 NMR instruments).

**Method header bar** — type pill, method name, validation status pill (in development / developed / validated), and live validation completion percentage from the backend `/validation/` endpoint.

**Four-tab detail panel:**

1. **Definition & Parameters** — method-type-specific parameter forms:
   - HPLC: 12 fields — column, mobile phase A/B, gradient (text), flow rate (mL/min), column temp (°C), injection volume (μL), wavelength (nm), run time (min), LOD, LOQ (both in μg/mL), sample prep notes
   - GC: 8 fields — column type, carrier gas, split ratio, oven program, inlet temp, detector type, detector temp, LOQ
   - NMR: 7 fields — nucleus, field strength (MHz), solvent, pulse sequence, relaxation delay, number of scans, sample concentration
   - Dissolution: 8 fields — apparatus (USP 1–7), medium, medium volume (mL), pH, temperature (°C), rotation speed (rpm), sampling timepoint, UV wavelength
   - Generic (MS, UV-Vis, Particle Size, etc.): free-text parameters
   
   **Preset parameter templates** per type — clicking a chip pre-fills the entire parameter form. HPLC has 3 templates (Purity Gradient RP-HPLC, Assay Isocratic RP-HPLC, Impurity Gradient HPLC with PDA); GC has 2 (Residual Solvent GC-HS, Organic Volatile Impurities); Dissolution has 3 (Immediate Release USP <711>, Extended Release, Enteric Coated). After editing, "Save Parameters" PATCHes `protocol: {...current, params: {...paramsForm}}`.

2. **Development Log** — chronological log of experiments and observations. Each entry captures: date, experiment description, observations (chromatographic parameters observed), verdict (suitable/not-suitable/needs-optimization). Entries stored in `protocol.dev_log` array and displayed newest-first.

3. **ICH Q2(R1) Validation Checklist** — 8 validation characteristics with toggle checkboxes: Specificity, Linearity, Range, Accuracy, Precision (Repeatability), Precision (Intermediate), LOD, LOQ, Robustness. Each characteristic has full ICH Q2(R1) guidance text (acceptance criteria, typical experiments, pass/fail indicators). Clicking a checkbox PATCHes `protocol: {...current, [item]: true/false}`. Live completion percentage shown in the method header.

4. **Reference** — three always-visible reference tables:
   - **System suitability requirements**: Resolution (Rs ≥ 2.0), Asymmetry factor (As 0.8–1.5), Theoretical plates (N ≥ 2000), Injection precision (%RSD ≤ 1.0), Capacity factor (k' ≥ 2.0), Selectivity (α ≥ 1.2)
   - **Forced degradation conditions**: Acid (0.1N HCl, 80°C, 1h), Base (0.1N NaOH, 80°C, 1h), Oxidation (3% H₂O₂, RT, 1h), Thermal (105°C dry heat, 1h), Photolysis (ICH Q1B, 1.2M lux·h), Neutral (pH 7 buffer, 80°C, 1h)
   - **Compendial references**: ICH Q2(R1)/(R2), ICH Q3A/B/C, USP \<621\>, Ph. Eur. 2.2.46, USP \<711\>, ICH Q1B

**Protocol JSON dual-use**: `AnalyticalMethod.protocol` (existing JSONField) stores three categories of data: method parameters under `protocol.params`, development log entries under `protocol.dev_log`, and ICH validation checklist completions as top-level boolean keys (`protocol.specificity = true`, etc.). This allows the existing backend `/validation/` endpoint — which reads `method.protocol.get(item)` — to compute completion without any backend changes.

**Left panel ICH Q2(R1) quick-reference table** — condensed 4-column table (Assay / Impurities / Dissolution / Identification) showing which validation characteristics apply per method purpose; always visible as a reference anchor.

---

### 6B — Specification Builder — What Changed

The original page was a flat list with a single add-form (spec type dropdown, attribute, acceptance criteria, test method, basis). It had no presets, no material type distinction, no criteria type classification, and no ICH Q6A reference.

The redesigned page has:

**Material type toggle** — DS / DP / Intermediate — switches which preset bank is shown. Does not filter saved specs (specs are typed at creation time, not filtered by material).

**Four tabs** — Release | Shelf Life | In-Process | Raw Material — each with a live count badge. Previous design had only Release, Shelf Life, In-Process.

**Preset specification bank** — 50+ scientifically accurate presets across all three material types and four spec types. Each preset carries attribute name, criteria type, full acceptance criteria text, compendial test method reference, and ICH citation basis. Examples:

| Material | Spec Type | Preset | Acceptance Criteria | Basis |
|---|---|---|---|---|
| DS | Release | Assay | 97.0–103.0% (anhydrous basis) | ICH Q6A — reflects ±2% analytical variability |
| DS | Release | Specified impurity A | NMT 0.20% | ICH Q3A — qualification threshold (daily dose > 10 mg) |
| DS | Release | Polymorphic form | Conforms to Form I reference diffractogram | XRPD — required if bioavailability-relevant |
| DS | Release | Elemental impurities | Per ICH Q3D PDEs (Pb ≤ 5 μg/day) | ICH Q3D — risk assessment + controls required |
| DP | Release | Uniformity of dosage units | AV ≤ 15.0; no individual outside ±25% of mean | Ph. Eur. 2.9.40 — mandatory for ≤ 25 mg or ≤ 25% fill weight |
| DP | Release | Dissolution (30 min) | NLT Q+5% = 85% in 30 min (50 rpm, 0.1N HCl, 37°C) | USP \<711\> / ICH Q6A — bioequivalence anchor |
| DP | In-Process | Blend uniformity | RSD NMT 3.0%; all individuals 90–110% of target | ASTM E2709 statistical design; PQRI guidance |
| DP | In-Process | Coating weight gain | 2.5–3.5% w/w | Development data — moisture barrier + appearance |

Presets already added to the active tab are shown with a green checkmark. Clicking any preset pre-fills the add modal — the scientist only edits as needed before saving.

**Specification table** — per tab: row number, attribute name, criteria type badge (color-coded: NMT=red, NLT=blue, between=purple, conforms=green, report=grey), acceptance criteria in monospace font, test method, linked analytical method (resolved by name from the methods store), basis/justification, edit and delete actions.

**Add/edit modal** — spec type selector, attribute name, criteria type toggles (styled buttons with live color), acceptance criteria (monospace input with contextual field hint explaining expected format per type — e.g., "Enter range: X–Y%" for `between`), test method, linked analytical method dropdown (all project methods), basis textarea.

**ICH Q6A reference panel** (toggled via header button) — 15-row test applicability table showing each test/characteristic as required / case-by-case / N/A for DS vs DP; plus two threshold reference tables:
- ICH Q3A/B impurity thresholds: reporting / identification / qualification thresholds for DS (Q3A) and DP (Q3B)
- ICH Q3C residual solvent classes: Class 1 (avoid — benzene 2 ppm), Class 2 (limit — DCM 600 ppm, THF 720 ppm), Class 3 (NMT 5000 ppm — EtOAc, IPA, acetone)

### Model Changes

| Model | Change |
|---|---|
| `Specification.criteria_type` | New CharField — NMT / NLT / between / conforms / report (default NMT) |
| `Specification.spec_type` | Added `raw_material` to choices (previously: release / shelf_life / in_process only) |
| `Specification.acceptance_criteria` | Widened from max_length=255 to max_length=500 |

Migration: `0011_specification_criteria_type_raw_material`

### Bugs Fixed

| Bug | Fix |
|---|---|
| 400 on analytical method creation | `AnalyticalMethodSerializer` lacked `read_only_fields` — same DRF pattern |
| 400 on specification creation | `SpecificationSerializer` lacked `read_only_fields = ('project', 'created_at')` |
| Missing delete in analytical API service | `analytical` object in `api.js` was missing `delete: (id) => api.delete(...)` |
| Missing `deleteMethod` store action | `analytical.js` store had no `deleteMethod` — added with currentMethod fallback logic |

---

## UPDATE 6 — Section 6: ADMET Dashboard & Preclinical Study Planner

### 6A — ADMETDashboardPage.vue (Full Rewrite)

**Before:** Basic page showing a flat list of ADMET property values with no scientific structure or interpretation.

**After:** Comprehensive 6-section scientific dashboard for drug scientists evaluating ADMET liabilities.

#### Navigation Sections

| Section | Content |
|---|---|
| Physicochemical | MW, LogP, HBD, HBA, TPSA, RotBonds — Lipinski Ro5 and Veber rule evaluation with pass/flag badges |
| Absorption (A) | Caco-2, HIA, P-gp substrate/inhibitor, BCS classification (I–IV) |
| Distribution (D) | BBB penetration (Martins), fu (fraction unbound), VDss, plasma:blood partitioning |
| Metabolism (M) | CYP1A2/2C9/2C19/2D6/3A4 inhibitor + substrate matrix, TDI flag |
| Excretion & Toxicity (E/T) | t½, hepatic clearance, AMES mutagenicity, hERG, hepatotoxicity |
| Experimental Data | Pulls `experimental[]` array from ADMET Dashboard API — MTD, key findings from preclinical studies |
| Regulatory Context | ICH S7B/S2(R1)/M7 mapping table, IND enabling package sequence |

#### Key Design Elements

- **`PKCSM_FIELDS` map** — 20+ pkCSM API keys mapped to `{label, unit, section, benchmark, direction, pass(v), guidance}`. Each field has a `pass()` function using evidence-based thresholds (e.g. `Caco-2 ≥-5.15 log cm/s`, `hERG IC50 flag when value > 0.5 inhibitor probability`).
- **BCS Classification** — computed from HIA (≥80% = high solubility surrogate), Caco-2 Papp, and LogP. Classes I–IV displayed with colour badges and clinical implication text.
- **Risk Flag Strip** — `riskFlags` computed generates prioritised flag list with severity `high/medium/info`. Flags on hERG, AMES, hepatotoxicity, P-gp, CYP3A4 DDI risk, CNS penetration anomalies.
- **CYP DDI Panel** — 5 enzymes × inhibitor/substrate matrix. Colour-coded by inhibitor (red) and substrate (orange) flags.
- **`ICH_ADMET_CONTEXT` table** — 9 rows linking safety flag → regulatory guideline → required action (e.g. hERG hit → ICH S7B → in vivo telemetry study required).
- **IND Enabling Sequence** — 5-step visual timeline: Safety Pharm → Genotox → Acute Tox → Repeat-dose → Reproductive Tox.

#### Data Extraction Pattern

```js
// API response: { project_id, computed_admet: { compoundName: { data, smiles, compound_id } }, experimental: [...] }
const firstCompoundEntry = computed(() => Object.entries(store.admetData?.computed_admet || {})[0])
const firstCompoundData  = computed(() => firstCompoundEntry.value?.[1]?.data)
```

---

### 6B — PreclinicalStudyPlannerPage.vue (Full Rewrite)

**Before:** 175-line basic form with flat study list, single create form, minimal detail view.

**After:** Comprehensive 1210-line ICH-compliant study planning platform.

#### Layout

Two-column design: 300px study list (grouped by study type) + right detail panel with 4 tabs.

```
┌─────────────────────┬──────────────────────────────────────────────┐
│  Study List         │  [Study Design] [Protocol] [Results] [IND]   │
│  ─────────────────  │                                              │
│  Toxicology         │  TAB CONTENT (see below)                     │
│   ▸ Acute Tox       │                                              │
│   ▸ 28-Day Rat      │                                              │
│  Safety Pharm       │                                              │
│   ▸ Irwin CNS       │                                              │
│  ─────────────────  │                                              │
│  IND Progress       │                                              │
│  [====---] 5/9 req  │                                              │
└─────────────────────┴──────────────────────────────────────────────┘
```

#### Study Type Coverage (8 types with ICH presets)

| Type | Presets | Guideline |
|---|---|---|
| Acute Toxicology | Limit Test (rat PO), MTD estimation (mouse IP) | ICH M3(R2) |
| Repeat-Dose Toxicology | 28-day rat GLP, 28-day dog GLP, 90-day rat GLP | ICH M3(R2) Table 1 |
| Genotoxicity | Ames test, In vitro MN (TK6), In vivo MN (rat) | ICH S2(R1) |
| Safety Pharmacology | CNS Irwin/FOB, hERG patch clamp, CV telemetry dog, respiratory | ICH S7A/S7B |
| Pharmacokinetics | IV/PO crossover, dose-proportionality, TK satellite | ICH M3(R2) |
| ADME | In vitro panel, [¹⁴C] mass balance | ICH M3(R2) |
| Efficacy | POC rodent model, dose-response ED₅₀ | — |
| Reproductive Toxicology | Fertility (Seg I), EFD rat (Seg II) | ICH S5(R3) |

Each preset pre-fills: title, species, dose_route, dose_levels, duration_days, glp, objective, primary_endpoints[], success_criteria.

#### Tab Detail

**Study Design tab**
- Editable: title, study_type, status, species, dose_route, dose_levels, duration_days, glp checkbox, objective, success_criteria
- Quick results summary card shown if study already has conclusion/NOAEL

**Protocol & Endpoints tab**
- Numbered endpoint list with add/remove controls
- ICH guideline reference table (8 study categories × guideline × IND requirement)
- Species justification reference cards (rat, mouse, dog, monkey, rabbit, in vitro — use cases and CYP notes)

**Results tab**
- Status + conclusion (Go / No-Go / Inconclusive) selectors with colour badges
- NOAEL (mg/kg) and MTD (mg/kg) numeric fields with field-level hints (ICH definitions)
- Results summary textarea
- Key Findings structured dictionary — add/remove parameter:value pairs
- Safety margin guidance card (NOAEL-HED conversion, AUC-based margin, Cmax-based margin, HNSTD)

**IND Package tab**
- 6 ICH categories × study checklist (required/recommended badges)
- Progress bar showing % of required studies checked
- FDA 21 CFR Part 312 IND filing checklist (Cover sheet, IB, CMC, etc.)
- Checklist state stored in local `indChecklist` ref (not persisted — session-only)

#### IND Package Categories
- Safety Pharmacology (ICH S7A/S7B) — 6 studies
- Genotoxicity (ICH S2(R1)) — 3 studies
- Acute/Single-Dose Toxicology (ICH M3(R2)) — 2 studies
- Repeat-Dose Toxicology (ICH M3(R2)) — 4 studies
- Pharmacokinetics & ADME — 4 studies
- Reproductive Toxicology (ICH S5(R3)) — 4 studies

---

### Backend Changes (UPDATE 6)

| File | Change |
|---|---|
| `core/views/preclinical.py` | `PreclinicalStudyResultsView.patch()` extended to handle `conclusion`, `noael_mgkg`, `results_summary` in addition to existing `key_findings`, `mtd_mgkg`, `status` |
| `core/migrations/0012_preclinicalstudy_extended_fields.py` | Added: `title`, `glp`, `primary_endpoints` (JSONField), `success_criteria`, `results_summary`, `conclusion`, `noael_mgkg` |

### Frontend Changes (UPDATE 6)

| File | Change |
|---|---|
| `frontend/src/views/ADMETDashboardPage.vue` | Full rewrite — 6-section ADMET dashboard (see 6A above) |
| `frontend/src/views/PreclinicalStudyPlannerPage.vue` | Full rewrite — 1210-line ICH study planner (see 6B above) |
| `frontend/src/services/api.js` | `preclinical.delete` added; `preclinical.logResults` already present |
| `frontend/src/stores/preclinical.js` | `fetchStudy` and `deleteStudy` actions added |

### Pattern Confirmed (UPDATE 6)

`PreclinicalStudyResultsView.patch()` now uses `setattr` loop over allowed result fields — consistent pattern with other partial-update views. Does NOT go through serializer validation (intentional — result fields are trusted internal data from the app).
