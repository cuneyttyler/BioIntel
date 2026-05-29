# AI Assistant for Drug Development Scientists

## Business Purpose

The AI assistant is designed to accelerate and de-risk the drug development process phase by providing scientists with actionable guidance, process optimization, and integrated knowledge support. It helps R&D teams move efficiently from concept to clinical candidate by aligning experiments, regulatory requirements, and decision-making with the realities of drug development operations. The primary business purpose is to reduce time-to-decision, improve resource allocation, and increase confidence in process development strategies.

## Application Components

- **Process Knowledge Engine**
  - Encodes process development best practices for formulation, synthesis, scale-up, analytical characterization, and manufacturing readiness.
  - Supports phase-specific guidance for early development, preclinical studies, and drug substance/process validation.

- **Scientific Workflow Assistant**
  - Guides scientists through structured process phase workflows with step-by-step recommendations.
  - Provides real-time prompts for experiment planning, risk assessment, and decision review.

- **Data Integration Layer**
  - Aggregates experimental results, formulation data, analytical reports, and regulatory constraints.
  - Connects to internal databases, ELN systems, and process development records.

- **Recommendation and Prioritization Engine**
  - Generates prioritized next steps, critical path actions, and candidate process improvements.
  - Highlights options for optimization, such as solvent selection, impurity control, and process robustness.

- **Collaboration and Documentation Module**
  - Produces summary reports, process rationale, and knowledge artifacts for project teams.
  - Supports handoff from development scientists to manufacturing and regulatory stakeholders.

## User Workflow Steps

1. **Define the Process Objective**
   - The scientist inputs the current development goal: e.g., scalable synthesis route, formulation stability, analytical method validation, or manufacturing process readiness.
   - The assistant confirms the phase context and key constraints.

2. **Capture Experimental and Process Context**
   - The assistant prompts for existing data: compound properties, prior process steps, formulation components, known impurities, and target product profile.
   - It reviews process history and identifies gaps.

3. **Analyze Process Risks and Opportunities**
   - The assistant evaluates risk factors such as reagent availability, scale-up feasibility, batch consistency, and regulatory expectations.
   - It provides a risk heat map and suggests priority areas for investigation.

4. **Recommend Next-Step Actions**
   - Based on the process objective, the assistant proposes concrete actions such as targeted experiments, alternative process conditions, or analytical tests.
   - It sequences tasks for efficient development and highlights critical dependencies.

5. **Support Experiment Design**
   - The assistant helps design process development experiments with suggested variables, control conditions, and success criteria.
   - It recommends data capture fields and measurement endpoints for each experiment.

6. **Review and Refine Process Decisions**
   - After results are available, the assistant interprets findings in the process context and suggests refinements.
   - It helps decide whether to optimize, reproduce, scale, or transition to the next development milestone.

7. **Document Process Strategy**
   - The assistant generates a concise process summary, including rationale, decision points, and recommended next-phase actions.
   - It formats documentation for internal review and future handoff.

## Required Data at Each Step

- **Define the Process Objective**
  - Target product profile
  - Phase-specific goal (e.g., development candidate, pilot manufacturing)
  - Success criteria and key performance indicators

- **Capture Experimental and Process Context**
  - Compound physicochemical properties
  - Existing synthesis or formulation route details
  - Prior experimental outcomes and failure modes
  - Material specifications and impurity profile

- **Analyze Process Risks and Opportunities**
  - Scale-up constraints
  - Regulatory requirements for process validation
  - Historical batch variability
  - Equipment and facility limitations

- **Recommend Next-Step Actions**
  - Available experimental resources
  - Timeline and budget constraints
  - Feasibility data from similar compounds or processes
  - Process performance targets

- **Support Experiment Design**
  - Variable ranges and control parameters
  - Analytical methods and acceptance criteria
  - Sample throughput and resource availability
  - Hypotheses for process improvement

- **Review and Refine Process Decisions**
  - Experimental results and key metrics
  - Comparison to target performance
  - Observed failure modes and anomalies
  - Updated risk assessment

- **Document Process Strategy**
  - Finalized process route or formulation
  - Rationale for selected conditions
  - Confirmed readiness criteria
  - Recommended next milestones and handoff notes

---

## UPDATE 1 — Competitive Drug Intelligence & Analog Development Workflow

### Context

A scientist wants to develop a new drug that produces the same therapeutic effect as existing treatments for a disease — but with a different chemical formula or production process in order to avoid patent conflicts. This is a two-phase workflow:

1. **Intelligence phase**: Learn everything about existing drugs for the disease.
2. **Design phase**: Find or design a structurally distinct analog that preserves the therapeutic effect.

---

### Workflow Definition

#### Phase 1 — Existing Drug Intelligence

**Step 1: Identify the disease and its known treatments**
- The scientist searches for the target disease by name.
- The app returns a list of drugs in clinical development or already approved for that indication, along with their phase and approval status.

**Step 2: Select a reference drug and retrieve its full profile**
For each drug of interest, the scientist needs:

- **Chemical identity**: molecular structure (SMILES, InChI), formula, molecular weight, stereochemistry.
- **Production method**: known synthesis routes (reagents, solvents, lab conditions, reaction temperatures, purification steps). This comes from literature, ChEMBL cross-references, and DailyMed manufacturing sections.
- **Mechanism of action**: which biological target the drug binds, what pathway it modulates, what effect it produces in the body, and which aspect of the disease it addresses.
- **Formulation details**: inactive ingredients, dosage form, excipients, route of administration — sourced from DailyMed / FDA labels.
- **Clinical trial history**: all trials the drug was involved in (phase, status, enrollment size, primary outcome, sponsor), linked from ClinicalTrials.gov.
- **Patent landscape**: active patents covering the molecule itself, the formulation, and the manufacturing process. Expiry dates and jurisdiction.

**Step 3: Assess the patent landscape**
- The scientist needs to understand which structural features, process steps, and formulation components are claimed in existing patents.
- This determines the space available for a non-infringing design.

---

#### Phase 2 — Analog Design (Similar Drug, Different Formula)

**Step 4: Structural analog search**
- Using the reference drug's SMILES, find structurally similar compounds in PubChem and ChEMBL that are not identical to the patented molecule.
- Filter by degree of similarity, commercial availability of starting materials, and known ADMET profiles.

**Step 5: Patent freedom-to-operate screening**
- For each candidate analog, check whether it is covered by existing patents (by structure or by claim language).
- Identify analogs that fall outside all active claims — these are "free-to-operate" candidates.

**Step 6: ADMET and efficacy comparison**
- Predict ADMET properties (solubility, permeability, metabolic stability, toxicity) for each free-to-operate candidate.
- Compare against the reference drug's known profile to confirm the analog is likely to produce a similar therapeutic effect.

**Step 7: Synthesis planning for the chosen analog**
- After shortlisting a candidate and clicking "Save to Project", the app automatically redirects to the Synthesis Planning page with the candidate's SMILES pre-loaded.
- Design a synthesis route for the selected candidate that also avoids process patents on the reference drug's manufacturing method.
- Use retrosynthesis tools (single-step retro, multi-step tree, forward prediction) to find alternative routes to the same target molecule.
- The project ID is passed as a URL parameter so the route can later be saved against the project.

**Step 8: Experiment Planning**
- From Synthesis Planning, navigate to the Experiment Planner to design the lab work needed to execute and validate the chosen synthesis route.
- Log experiment results against the project compound.

**Step 9: Documentation**
- Produce a structured report: reference drug profile, patent gap analysis, selected analog rationale, ADMET comparison, and proposed synthesis route.
- Use the "Analog Development Report" document type in the project's Documentation page.

---

### Why the Current Implementation Does Not Support This Workflow

#### 1. No drug-centered exploration entry point
The current app is **project-centric**: the scientist must already have a compound in mind before creating a project. There is no flow that starts from "I want to treat disease X — show me existing drugs" and lets you drill into each drug's full profile. The Disease Explorer shows known drugs (name, phase, status) but offers no way to navigate into a drug's details.

#### 2. No patent data source
**Patent search is entirely absent** from the current data sources. There is no integration with SureChEMBL, Espacenet, Google Patents, or any other patent database. Without this, the core question — "which structural modifications are free to operate?" — cannot be answered.

#### 3. Drug production details are not surfaced
The scientist needs to know how an existing drug is manufactured (solvents, conditions, reagents, purification). DailyMed and PubMed are integrated, but neither is used to surface **synthesis and manufacturing detail for an existing reference drug**. The Synthesis Planning page only works on a SMILES the scientist provides — it doesn't look up how a named drug has been made before.

#### 4. Clinical trials are disconnected from drugs
The Literature page searches ClinicalTrials.gov by condition and intervention independently. There is no way to click a drug in the Disease Explorer's Known Drugs table and see all its associated trials. The clinical history of a specific reference drug is not retrievable as a unit.

#### 5. The Compound Profile page is designed for the scientist's own compound
The Compound Profile page fetches properties for a compound saved inside a project. It was not designed to be used as a "reference drug investigation" tool. There is no way to open the profile of a competitor or reference drug without first creating a project and saving it as a compound — which is a workflow mismatch.

#### 6. Analog search has no patent awareness
PubChem fingerprint similarity is implemented in the Compound Profile page, but the results are raw CIDs with no patent status, no free-to-operate indication, and no ADMET comparison against the reference drug. It is a lookup, not a decision-support tool.

#### 7. No unified comparison view
The scientist needs to compare multiple analog candidates side by side (ADMET, structure, patent risk). There is currently no comparison or shortlisting mechanism in the app.

---

### Suggested Changes to the App

#### New pages

| Page | Purpose |
|---|---|
| **Drug Intelligence** | Disease → known drugs → full reference drug profile (structure, mechanism, synthesis, formulation, clinical trials, patents) in one place |
| **Patent Explorer** | Search patents by drug name or SMILES structure; show claims, expiry, jurisdiction; flag which structural features are covered |
| **Analog Workspace** | Pick a reference drug → generate structural analogs → filter by patent freedom → compare ADMET → shortlist candidates |

#### Changes to existing pages

| Page | Change needed |
|---|---|
| **Disease Explorer** | Known Drugs table rows should be clickable and navigate to the Drug Intelligence page for that drug |
| **Compound Profile** | Add a "Use as Reference Drug" mode that enables the analog search and patent comparison workflow |
| **Synthesis Planning** | Add "Look up existing routes" — search PubMed and ChEMBL for published synthesis routes for a named drug before designing a new one |
| **Literature** | Add a "Patents" tab alongside PubMed and ClinicalTrials, powered by SureChEMBL or Espacenet |
| **Documentation** | Add a new document type: "Analog Development Report" — covers reference drug profile, patent gap analysis, chosen candidate, and proposed route |
| **Navigation / SideNav** | Add a "Drug Discovery" section grouping: Drug Intelligence, Patent Explorer, Analog Workspace — distinct from the project-based workflow |

#### New data sources required

| Source | Purpose | Access |
|---|---|---|
| **SureChEMBL** (EMBL-EBI) | Structure-searchable patent chemistry database; free REST API | Free, public |
| **Espacenet** (EPO) | Full patent text, claims, expiry dates, jurisdiction | Free, OPS REST API |
| **ChEMBL drug indications** | Map disease EFO IDs to approved drugs with ChEMBL IDs for richer drug profiles | Already integrated — extend usage |

#### Summary of data gaps per workflow step

| Workflow step | Current capability | Gap |
|---|---|---|
| Find drugs for a disease | Partial (Open Targets known drugs list) | No drill-down into drug profile |
| Synthesis / production details | None for existing drugs | Need PubMed synthesis route search + DailyMed manufacturing section |
| Mechanism of action | Partial (ChEMBL, Open Targets) | Not surfaced per drug in a unified view |
| Clinical trial history per drug | None as a linked flow | Need ClinicalTrials filtered by drug name, linked from disease explorer |
| Patent landscape | None | Need SureChEMBL / Espacenet integration |
| Structural analog search | Partial (PubChem similarity) | No patent freedom filter, no ADMET comparison |
| Free-to-operate screening | None | Requires patent data + structural overlap analysis |
| Alternative synthesis route | Partial (ASKCOS retrosynthesis) | No awareness of process patents to avoid |
| Analog development report | None | New document type needed |

---

## UPDATE 2 — Synthesis Planning ↔ Project Integration

### Context

After UPDATE 1 introduced Drug Intelligence and the Analog Workspace, a scientist could find a reference drug, discover structural analogs, and be redirected to the Synthesis Planning page — but the connection ended there. Synthesis plans existed only for the duration of the browser session; they were never persisted to a project. The project edit page showed only a bare form with no visibility into synthesis work. There was also no way to trace which reference drug or which analog candidates had spawned a given project.

This update closes those gaps by introducing a clean three-level hierarchy:

```
Project
  ├── DrugInvestigation (reference drug that prompted this project)
  ├── AnalogCandidates (shortlisted molecules from the investigation)
  ├── SynthesisPlan(s) (designed retrosynthetic routes for the target compound)
  │     └── Experiment(s) (lab execution steps derived from a plan)
  └── Experiment(s) (any other experiments: formulation, analytical, stability)
```

---

### What Changed

#### New concept: Synthesis Plan vs Experiment

Previously, clicking "Plan Experiments from Route" on the Synthesis Planning page created one `Experiment` record per retrosynthesis step. This conflated two distinct scientific objects:

- A **synthesis plan** is the *designed route* — the retrosynthetic analysis result. It answers "how could we make this molecule?" It captures the target SMILES, the route steps, and the type of analysis (single-step or multi-step tree).
- An **experiment** is the *lab execution* of a specific step — it has variables, conditions, results, and a decision (optimize / reproduce / scale / abort).

These are now modelled separately. A synthesis plan is saved first (by the scientist explicitly clicking "Save Route to Project"); experiments are created from it afterwards (either on demand from the Synthesis Planning page or from the project edit page).

---

#### Changes to the Analog Workspace

| Before | After |
|---|---|
| Always creates a new project | Scientist can pick an existing project from a dropdown or create a new one |
| Only the chosen analog SMILES was saved | All shortlisted analogs are linked to the project |
| No link back to the investigation | The `DrugInvestigation` and all shortlisted `AnalogCandidate` records are linked to the project |
| No handling of compound conflicts | If the selected existing project already has a compound, a dialog asks to replace it or add the analog alongside |

---

#### Changes to the Synthesis Planning page

| Before | After |
|---|---|
| Always required a `?project=Y` URL param to link experiments | Optional project picker shown at the top when accessed standalone |
| "Plan Experiments from Route" created experiments directly | New "Save Route to Project" button persists the route as a `SynthesisPlan` first |
| Experiments were created without any link back to the plan | Experiments created from "Plan Experiments" carry a `synthesis_plan` FK |

---

#### Changes to the Project Edit page

The project edit page now shows three additional sections in edit mode:

1. **Reference Drug & Analogs** — displayed when the project has a linked `DrugInvestigation`. Shows the reference drug name, ChEMBL ID, and SMILES, plus a chip list of all shortlisted analog candidates with their similarity score and patent status.

2. **Synthesis Plans** — a table of all `SynthesisPlan` records for the project. Each row shows the target SMILES, plan type (single-step / multi-step), status, number of steps, and creation date. Actions per row:
   - **Browse** — reopens Synthesis Planning with the target SMILES and project pre-filled
   - **Plan Experiments** — creates experiment records from the plan's route steps (only shown if no experiments exist yet for that plan)

3. **Experiments** — a table of all experiments for the project (all types), with a "View" link to each experiment detail page.

---

### Updated Workflow (Step-by-Step)

1. Scientist searches for a reference drug via Drug Intelligence.
2. Clicks "Start Analog Search" → creates a `DrugInvestigation` and opens the Analog Workspace.
3. Finds structurally similar compounds, checks patents, runs ADMET.
4. Shortlists candidates. In the Shortlist panel, selects an existing project or types a new name.
5. Clicks "Save to Project" → the chosen analog SMILES becomes the project's Compound; the investigation and all shortlisted candidates are linked to the project; the page redirects to Synthesis Planning with the analog SMILES and project ID pre-filled.
6. On the Synthesis Planning page, runs retrosynthesis (single-step or multi-step tree).
7. Clicks "Save Route to Project" → a `SynthesisPlan` record is created and stored.
8. Clicks "Plan Experiments" → `Experiment` records (type: synthesis) are created, each linked to the plan.
9. In the project edit page, the scientist can see the reference drug, the analog shortlist, all synthesis plans, and all experiments in one place.
10. Each synthesis plan row has a "Browse" button to return to Synthesis Planning for further exploration, and a "Plan Experiments" button if experiments haven't been created yet.
11. Experiments are executed in the lab and results logged via the Experiment Results page.

---

## UPDATE 3 — Synthesis Planning Page Redesign

### Context

After UPDATE 2 connected synthesis plans to projects, the Synthesis Planning page still required the scientist to manually click "Find Synthesis Route" after being redirected from the Analog Workspace, then manually click a separate "Save Route to Project" button. The page also offered no reaction conditions alongside the route steps, and the Forward Prediction tool sat at the top level where it distracted from the primary retrosynthesis workflow.

This update makes the synthesis planning experience match real scientific practice: the route analysis starts automatically, conditions appear inline with each step, and the plan is saved to the project without any extra button clicks.

---

### What Changed

#### Auto-run on redirect from Analog Workspace

When the scientist is redirected from the Analog Workspace with `?smiles=X&project=Y` URL parameters, the page detects this on mount and immediately runs single-step retrosynthesis for the target SMILES. The scientist sees results within seconds of arriving on the page — no manual action required.

#### Auto-save when a project is linked

Whenever retrosynthesis results load successfully and a project is linked (either via the URL param or selected manually in the project picker), the plan is automatically saved as a `SynthesisPlan` record. There is no separate "Save Route to Project" button — saving is a side-effect of running the analysis. This applies to both single-step retro and multi-step tree modes.

#### Inline reaction conditions per step

Each retrosynthetic disconnection card now shows the recommended lab conditions immediately below the starting materials:

| Field | Example |
|---|---|
| Reagents | HATU, DIPEA |
| Solvent | DMF |
| Temperature | RT |
| Time | 2–4 h |

Conditions are fetched in the background using the transform name (e.g. "Amide bond formation") as a lookup key against a curated conditions library. This gives the scientist everything needed to plan and cost the step without leaving the page.

#### Per-precursor buyability check

Each starting material in a step card has a "Check availability" button. Clicking it calls a heuristic buyability check (based on molecular weight, ring count, and heavy atom count) and reports the result inline — either "✓ Available" (green) or "✗ Custom synthesis" (red).

#### Forward Prediction moved to collapsed Advanced Tools

Forward Prediction is now hidden inside a collapsible "Advanced Tools" section at the bottom of the page. This is appropriate because forward prediction is a secondary, verification-oriented tool — used to confirm what a pair of specific starting materials will produce, not to plan a route. The primary workflow (retrosynthesis → conditions → plan experiments) is uncluttered.

---

### Updated Workflow (Step-by-Step, Synthesis Planning)

1. Scientist clicks "Save to Project" in the Analog Workspace → redirected to Synthesis Planning with `?smiles=TARGET&project=ID`.
2. Page auto-runs single-step retrosynthesis immediately on mount.
3. Results appear: each disconnection step card shows the transform name, forward reaction description, starting material SMILES, and reaction conditions.
4. Scientist reviews steps. For any starting material, clicks "Check availability" to get a buyability estimate.
5. If a project is linked, the plan is already saved automatically (toast: "Route saved to project").
6. Scientist clicks "Plan Experiments" → `Experiment` records are created for each route step and the scientist is redirected to the project edit page.
7. If the scientist wants to explore a multi-step tree instead, they click "Multi-Step Tree" — the tree result also auto-saves if a project is linked.
8. For verification of specific precursor pairs, the scientist opens "Advanced Tools" and uses Forward Prediction.

---

## UPDATE 4 — Analog-Centric Synthesis Planning & Plan Comparison

### Context

After UPDATE 3, synthesis plans existed per project but had no structural relationship to the individual analog candidates that spawned them. A project could accumulate many plans with no way to know which plan belonged to which analog, and there was no mechanism to prevent duplicate plans of the same type for the same molecule. Additionally, "Start New Plan" on the project page navigated directly to Synthesis Planning with no analog pre-selected — the page had no useful context to work with.

This update reorganises the synthesis planning workflow so that every plan is explicitly attached to one analog candidate, plans are created exclusively through the Analogs table on the project page, and scientists can select multiple plans across different analogs for side-by-side comparison.

---

### What Changed

#### Analog table replaces the chip list on the Project page

The project edit page previously showed shortlisted analogs as a compact chip list with no actions. This has been replaced by a full table:

| Column | Description |
|---|---|
| SMILES | Truncated canonical SMILES |
| Sim. | Tanimoto similarity to the reference drug |
| Patent | Patent status badge (free / covered / unknown) |
| Single-Step | "✓ Done" badge if a retro plan exists; "Plan →" button otherwise |
| Multi-Step | "✓ Done" badge if a tree plan exists; "Plan →" button otherwise |

Each "Plan →" button navigates directly to Synthesis Planning with the analog's SMILES pre-loaded, the analysis type locked, and auto-run enabled. A maximum of one single-step plan and one multi-step plan is enforced per analog at the database level.

#### "Start New Plan" removed; "Find Analog" added

The "Start New Plan" button that previously linked to Synthesis Planning with no context has been removed. Plans are now only creatable through the Analogs table. In its place, a "Find Analog" button opens the Analog Workspace in **project mode** so the scientist can add or modify shortlisted analogs for the project.

#### Analog Workspace — project mode

The Analog Workspace now has two distinct entry modes:

| Mode | Entry point | Behaviour |
|---|---|---|
| **Drug search mode** | Drug Intelligence → "Start Analog Search" | Full workflow; save creates/updates a project and returns to the project page |
| **Project mode** | Project page → "Find Analog" (`?project=ID` URL param) | Pre-loads existing shortlisted analogs; toggle buttons immediately PATCH the DB; "Done" button saves any new candidates and returns to the project page |

In drug search mode, saving to a project now redirects to the **project page** (not Synthesis Planning, as in UPDATE 3). Synthesis routes are planned separately per analog from the project page.

In drug search mode, if no `DrugInvestigation` exists yet (the scientist came from a drug search without creating one first), `saveToProject` creates the investigation on the fly, persists all shortlisted candidates to it, and then links it to the project.

#### Synthesis Planning — plan-aware entry

The Synthesis Planning page now accepts three additional URL parameters:

| Parameter | Effect |
|---|---|
| `?plan=ID` | Load a specific saved plan by ID; hydrate results from stored `route_data`; lock the analysis type to the plan's type |
| `?analog=ID` | Resolve the analog's SMILES from the project detail; skip the analog picker and show the locked context panel directly |
| `?type=retro\|tree` | Lock the analysis type toggle; the non-matching button is disabled |
| `?autorun=1` | Strip flag from URL immediately, then auto-run the locked type and auto-save (used when arriving from an analog "Plan →" button) |

"Browse" on the Synthesis Plans table now passes `?plan=ID&type=TYPE&smiles=SMILES` so the exact saved plan is loaded and its full route is rendered immediately without re-running analysis.

#### Plan comparison

The Synthesis Plans table on the project page supports multi-select via row checkboxes. When two or more plans are selected, a **Compare** button becomes active and navigates to `/synthesis/compare?plans=1,2,...`. The comparison page shows plans side by side: structure image, type, status, step count, and the full route detail (retro steps or synthesis tree) in parallel columns.

---

### Updated Workflow (Step-by-Step)

1. Scientist searches for a reference drug via Drug Intelligence → clicks "Start Analog Search".
2. Analog Workspace opens in drug-search mode. Scientist finds analogs, checks patents, runs ADMET, shortlists candidates.
3. Scientist selects an existing project or types a new name → clicks "Save to Project" → redirected to the **project page** (not Synthesis Planning).
4. On the project page, the Analogs table shows all shortlisted analogs with their plan status.
5. To add or change analogs, scientist clicks "Find Analog" → Analog Workspace opens in project mode with existing analogs pre-selected.
6. To plan a route for an analog, scientist clicks "Plan →" in the Single-Step or Multi-Step column.
7. Synthesis Planning opens with the analog's SMILES locked, the analysis type locked, and retrosynthesis running automatically.
8. The plan is auto-saved. Scientist can review conditions, check buyability, and click "Plan Experiments" to create lab records.
9. Back on the project page, to compare two routes, scientist checks two rows in the Synthesis Plans table and clicks **Compare**.
10. The comparison page shows the two plans side by side: structure, route steps, and conditions.