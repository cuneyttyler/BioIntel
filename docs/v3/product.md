# BioIntel — Product Specification v3

## Vision

BioIntel v3 is the first drug development platform where AI and scientists co-author the development plan. Building on v2's comprehensive manual pipeline, v3 introduces two levels of AI integration: a contextual per-page assistant available on every page, and a fully autonomous AI-Driven project mode where an intelligent agent guides scientists through the entire drug development pipeline step by step — grounded at every recommendation in peer-reviewed methodology and ICH regulatory guidelines.

v3 covers both **small molecule** and **biologic** drug development. The AI is not a black box — every recommendation it makes cites the specific guideline, paper, or data source behind it. Scientists remain in control at every gate. The AI proposes; the scientist decides.

The platform is designed for teams that want to move faster without compromising scientific rigor, and for organizations that need an auditable AI trail alongside their experimental data.

---

## User Personas

### Medicinal Chemist
Focused on finding, designing, and optimizing drug-like molecules. Primary workflows: target exploration, compound profiling, analog search, SAR tracking, virtual screening, ADMET comparison. In v3, uses the AI-Driven Plan to get ADMET-grounded candidate shortlists and SAR optimization suggestions with peer-reviewed benchmarks.

### Process / Formulation Scientist
Focused on taking a promising molecule and developing it into a manufacturable drug product. Primary workflows: synthesis planning, salt and polymorph screening, formulation planning, excipient compatibility, stability design, scale-up planning. In v3, uses the per-page AI panel to get ICH Q8(R2)-grounded formulation advice inline with their work.

### Analytical Scientist
Focused on characterizing the compound and product, developing and validating methods. Primary workflows: method development, specification building, analytical experiment planning. In v3, uses the per-page AI panel to get ICH Q2(R1)-referenced method development guidance.

### Drug Development Manager
Needs a portfolio view of all projects, phase status, go/no-go decisions, and documentation for regulatory submissions. In v3, uses AI-Driven Plan summaries to track AI recommendations vs. actual decisions, and uses the Document Portal to manage regulatory submissions alongside AI-drafted documents.

### Computational Scientist (NEW)
Focused on AI-first workflows: initiating projects via the AI Lab, running virtual screening, using AI-Driven Plans for rapid pipeline planning, and managing the pharmaceutical RAG corpus. Primary workflows: AI Lab, Virtual Screening, AI-Driven Plan, Document Portal, Biologics Antibody Design.

---

## Project Modes

Every project in BioIntel v3 has a **mode**:

### Manual Mode
v2 behavior. Scientists drive all workflows manually. Per-page AI panel is available for contextual Q&A (no plan context). Global Chat Assistant is available for deep multi-turn queries. No AI-Driven Plan.

### AI-Driven Mode
All v2 pages plus an **AI-Driven Plan** section on the project page. The AI generates a structured step-by-step development plan grounded in the pharmaceutical playbook corpus. Scientists approve or discuss each step before it advances. The per-page AI panel is plan-aware — it surfaces the current step's recommendation on the relevant page and shares the conversation thread with the plan.

**Mode is set at project creation.** Manual projects can be upgraded to AI-Driven at any time from the project settings. When upgrading, the AI reads all existing project data and generates a plan from the current state, marking already-completed steps appropriately.

### Molecule Type
AI-Driven projects declare a `molecule_type`:
- **Small Molecule** — classical medicinal chemistry pipeline. All existing v2 modules apply. ASKCOS synthesis, pkCSM ADMET, ICH Q-series guidance.
- **Biologic** — antibody, protein, peptide, or gene therapy pipeline. New biologics-specific modules (Module 15). ICH Q5-series + S6(R1) guidance. ASKCOS/pkCSM disabled; developability tools used instead.
- **Undetermined** — AI helps determine the appropriate pathway during intake.

---

## Drug Development Pipeline

BioIntel organizes all projects around a sequential development pipeline. Phase structure is the same for both small molecule and biologic projects; the content at each phase differs.

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
     ↓  [Go/No-Go: IND / CTA Readiness]
Regulatory & Clinical
```

Each phase has a **status** (not started / in progress / complete / on hold) and a recorded **go/no-go decision** (with rationale). In v3, AI-Driven projects additionally show an **AI readiness summary** at each gate — a structured assessment of whether the phase data meets progression criteria per ICH or published methodology. This is a recommendation, not a decision; the scientist records the final go/no-go.

---

## Project Hierarchy

Every piece of work lives inside a **Project**. In v3, AI-Driven projects carry an additional `AIPlan` entity with its associated steps and discussion threads.

```
Project [mode: manual | ai_driven] [molecule_type: small_molecule | biologic]
  │
  ├── AIPlan (AI-Driven only)
  │     ├── AIPlanStep × 15 (small molecule) or × 15 (biologic)
  │     └── AIPlanDiscussion × N (per step + plan-level)
  │
  ├── Phase: Target Biology / Drug Discovery
  │     ├── DrugInvestigation
  │     └── AnalogCandidates
  │
  ├── Phase: Lead Optimization
  │     ├── Compound
  │     ├── CompoundProperties
  │     └── SAREntries
  │
  ├── Phase: Drug Substance Development
  │     ├── SynthesisPlan(s)
  │     ├── SaltPolymorphScreen
  │     ├── ScaleUpPlan
  │     └── Experiments [type: synthesis]
  │     │
  │     (Biologic only)
  │     ├── CellLineDevelopment
  │     └── BioprocessDevelopment
  │
  ├── Phase: Drug Product Development
  │     ├── FormulationPlan
  │     ├── StabilityPlan
  │     └── Experiments [type: formulation, stability]
  │     │
  │     (Biologic only)
  │     ├── BiologicsFormulation
  │     └── DownstreamPurification
  │
  ├── Phase: Analytical Development
  │     ├── AnalyticalMethods
  │     └── Specifications
  │     │
  │     (Biologic only)
  │     └── BiologicsCharacterizationMethods
  │
  ├── Phase: Preclinical Development
  │     ├── Studies
  │     └── RiskAssessment
  │
  ├── Documents
  ├── ChatSessions (Manual projects)
  └── LinkedRagDocuments (from Document Portal)
```

---

## Modules 1–10 — Carried Forward from v2

All ten v2 modules are present in v3 without breaking changes. The following enhancements apply across all modules in v3:

- Every page gains a **Per-Page AI Panel** (Module 13) — a collapsible right-side assistant.
- AI-Driven projects: the panel is plan-aware and shares context with the AI-Driven Plan.
- Manual projects: the panel provides contextual Q&A using only the page data and project history.

Module-level AI enhancements (detailed in Module 13):
- Module 1 (Target Biology): Panel can explain target druggability scores, suggest complementary targets, and cite Open Targets methodology.
- Module 2 (Drug Discovery): Panel can compare analog ADMET profiles, explain patent claims, and suggest structural modifications to avoid IP conflicts.
- Module 3 (Lead Optimization): Panel provides SAR interpretation, flags problematic structural motifs, and benchmarks properties against Lipinski/Wager/Gleeson thresholds.
- Module 4 (Drug Substance): Panel provides retrosynthesis commentary, ICH Q11-referenced process guidance, and salt/polymorph screening interpretation.
- Module 5 (Drug Product): Panel provides ICH Q8(R2)-grounded formulation advice, excipient selection rationale, and compatibility risk interpretation.
- Module 6 (Analytical): Panel provides ICH Q2(R1) method development guidance and specification drafting suggestions.
- Module 7 (Preclinical): Panel provides ICH M3(R2)/S7A/S7B-referenced study design guidance, species selection rationale, and NOAEL interpretation.
- Module 8 (Literature): Panel can summarize retrieved papers and extract relevant data for the project.
- Module 9 (Regulatory): Panel can assist in drafting and reviewing regulatory documents using ICH templates.
- Module 10 (Dashboard/Projects): Panel is not shown on non-project global pages (Dashboard, Drug Discovery search pages).

---

## Module 11 — AI Lab (NEW)

### Purpose
The AI Lab is the entry point for AI-first workflows. Instead of filling in a project form and then running a plan separately, scientists describe what they want to develop in natural language. The AI conducts a structured intake interview, then proposes a complete project and development plan. Scientists confirm, and both are created atomically.

### AI Lab Page (`/ai-lab`)

**Layout:**
- Left sidebar (260px): previous AI Lab session list with session title (auto-generated from disease description), date, and status (in_progress / project_created)
- Main panel: chat interface with streaming AI responses, same visual pattern as existing Chat Assistant

**Intake flow:**

The AI conducts a structured intake interview, asking questions in a conversational way. The intake covers seven topics, asked one or two at a time (not as a form):

1. **Disease / condition**: What disease or biological condition are they targeting? Any specific patient population or unmet need?
2. **Development pathway**: Do they have a known reference drug (analog-based), are they starting from a biological target (novel small molecule design), or are they developing a biologic?
3. **Molecule type**: Is this small molecule or biologic? If unsure, AI suggests based on disease and pathway.
4. **IP and mechanism constraints**: Any known IP landscape issues? Any mechanisms, structural classes, or targets to avoid?
5. **Starting point**: What development stage are they entering at? Do they have any existing data (compounds, ADMET results, prior synthesis work)?
6. **Internal documents**: Have they uploaded relevant documents to the Document Portal? If not, AI notes which types of documents would improve plan quality.
7. **Timeline and risk appetite**: Are there specific timeline pressures? Is this a high-risk/high-reward or conservative development strategy?

After intake, the AI presents a **project proposal summary**:
- Proposed project name
- Development pathway (analog-based / novel design / biologic)
- Molecule type
- Starting phase
- Key constraints and assumptions noted
- First 3 plan steps as a preview

The scientist can ask follow-up questions, correct any misunderstanding, or say "looks good." Once confirmed, the **"Create Project & Plan"** button appears. Clicking it creates:
1. The `Project` record (mode: ai_driven, molecule_type as determined)
2. The `AIPlan` record (status: active)
3. All 15 `AIPlanStep` records (status: pending for steps 2–15, status: in_progress for step 1)
4. The AI Lab session is closed; user is redirected to the new project page

### Pages
- `AILabPage` — left session sidebar + main intake chat

---

## Module 12 — AI-Driven Plan (NEW)

### Purpose
The AI-Driven Plan is a living, AI-authored development plan for the project. It is grounded in the pharmaceutical playbook corpus (ICH guidelines + canonical methodology papers). It advances step by step as the scientist approves each recommendation. Scientists can discuss any step with the AI, request revisions, or branch the plan backward when experiment results change direction.

### Plan Section on Project Page

The Project page gains a new **"AI-Driven Plan"** section below the Phase Tracker. This section is only visible for AI-Driven projects.

**When no plan exists** (Manual-to-AI-Driven upgrade path):
- A "Generate AI-Driven Plan" card with a brief description and a CTA button
- Clicking launches the plan generation interface

**When a plan exists:**
- A vertical timeline of step cards
- A "Plan Status" header bar: active / paused / completed, with step progress (e.g., "4 of 15 steps complete")
- Each step rendered as a `AIPlanStepCard`

### AI-Driven Plan Step Card

Each step card shows:
- **Step number** (circle badge, colored by status)
- **Phase badge** (matches the development phase this step belongs to)
- **Step title** (e.g., "Patent Landscape Review & FTO Assessment")
- **Status badge**: pending (grey) / in_progress (blue, pulsing) / awaiting_approval (amber) / approved (green) / revision_needed (orange) / completed (green, checkmark) / skipped (grey, strikethrough) / abandoned (grey, strikethrough)
- **AI recommendation preview** (first 2 lines of the narrative, truncated) — only shown when status is awaiting_approval or approved
- **RAG citations** — small pill badges showing "ICH Q6A" / "Lipinski 1997" etc.
- **Action buttons** (context-sensitive per status):
  - `awaiting_approval`: [Approve & Proceed] [Discuss] [Request Revision]
  - `in_progress`: streaming indicator + [Cancel]
  - `revision_needed`: [Discuss] (AI auto-starts revision)
  - `approved / completed`: [View Details] [Discuss]
  - `pending`: [Skip] (only for steps scientist wants to bypass)

Clicking **"Approve & Proceed"** marks the step completed, moves it to `completed` status, and triggers the next step's AI generation (in_progress).

Clicking **"Discuss"** expands an inline discussion panel below the step card — a streaming chat thread scoped to this step.

Clicking **"Request Revision"** sets the step to `revision_needed` and opens the discussion panel with a prompt for the scientist to describe what they want changed.

### Per-Step Discussion Panel

Inline expansion below the step card. Shows:
- The full AI reasoning (complete text, not just preview)
- RAG citations as expandable blocks (shows the actual guideline/paper text chunk cited)
- The full discussion thread (scientist messages + AI responses) for this step
- Input field for the scientist to type
- AI responds with streaming, using the same tool set as the global Chat Assistant plus plan-specific tools

The discussion panel shares context with the Per-Page AI Panel (Module 13): if the scientist is on the Formulation Planning page during step 10, the panel shows the same step discussion.

### Plan Generation (First Run)

When "Generate AI-Driven Plan" is first triggered (either from AI Lab or from project page):

1. A full-width streaming panel opens on the project page
2. The AI streams its plan generation reasoning in real time:
   - "Reviewing project context: [project name], analog-based small molecule, targeting [disease]..."
   - It calls tools: `search_disease`, `get_disease_targets`, `search_patents`, `search_pubmed`
   - It retrieves relevant playbook chunks: [Source: ICH Q6A], [Source: Bleicher et al. 2003]
   - It generates each step title + brief description + phase assignment
3. As each step is finalized, a step card appears in the timeline below with a "typewriter" animation
4. When all steps are generated, the panel collapses and the timeline is fully populated
5. Step 1 immediately transitions to `in_progress` and starts generating its recommendation

### Post-Experiment AI Analysis

Steps that require experiment results (synthesis, ADMET, SAR, stability, preclinical) show a special state:

- After step is `approved`: an "Awaiting Experiment Results" banner appears on the step card
- A **"Log Experiment"** button links to the relevant experiment logging page (pre-filled with the experiment parameters the AI recommended)
- After the scientist logs results and returns to the project page, a **"Run AI Analysis"** button appears on the step card
- Clicking "Run AI Analysis" triggers `stream_result_analysis()`:
  - AI reads the logged experiment data
  - Compares to original recommendation and success criteria
  - Proposes one of three actions: **Proceed as planned** / **Revise current step** / **Go back to step N**
  - Streams the analysis with citations
  - Posts a summary to the step discussion thread
  - If "Proceed": next step starts automatically
  - If "Revise": step returns to in_progress with revision context
  - If "Go back": scientist confirms which step to branch to

### Branching: Go Back to Step N

When the AI (via result analysis) or the scientist (via manual action) triggers a go-back:

1. A confirmation dialog shows: "This will mark steps N through [current] as abandoned. Their data will be preserved but hidden from the main views. Continue?"
2. On confirm:
   - Steps N through current are set to `abandoned`
   - New `AIPlanStep` records are created from step N onward (fresh plan from that point)
   - All BioIntel entities created by the abandoned steps remain in the DB with an `ai_plan_step_id` link — they are not deleted, just filtered out of default views
3. The timeline re-renders: abandoned steps shown as greyed out with a branch indicator
4. Step N transitions to `in_progress`

### Context Compression

The plan's discussion threads are stored as `AIPlanDiscussion` records. When the total message count across the plan exceeds 100, a background process triggers compression:

- `generate_once()` is called with a pharmaceutical-domain compression prompt
- The output is a structured summary covering: decisions made, entities created, key constraints surfaced, experiment outcomes
- Stored in `AIPlan.conversation_context`
- All subsequent AI calls prepend this summary + the last 10 messages (not the full history)

Scientists never see the compression event — the conversation continues seamlessly.

### Plan Step Coverage — Small Molecule (15 steps)

| Step | Phase | Title | Key AI Actions |
|---|---|---|---|
| 1 | Discovery | Disease & Target Identification | `search_disease`, `get_disease_targets`; ranks targets by druggability + evidence score; cites Open Targets methodology |
| 2 | Discovery | Reference Drug / Target Structure Selection | For analog: `get_drug_profile`, patent landscape review; For novel: PDB structure selection; cites Hopkins & Groom 2002 |
| 3 | Discovery | Patent Landscape & FTO Assessment | `search_patents` on target SMILES + drug name; assesses freedom-to-operate; flags active claims; cites SureChEMBL |
| 4 | Discovery | Virtual Screening / Analog Search | `search_chembl` for analogs; screens with Tanimoto similarity; runs `predict_admet` on top candidates; cites Bleicher et al. 2003 |
| 5 | Lead Optimization | ADMET Profiling & Candidate Shortlisting | Full `predict_admet` on shortlist; applies Lipinski + Wager MPO benchmarks; flags hERG, AMES, hepatotoxicity; cites Gleeson 2008 |
| 6 | Lead Optimization | Lead Optimization Objectives | Proposes SAR goals based on ADMET gaps; suggests structural changes to improve weakest properties; cites Leeson & Springthorpe 2007 |
| 7 | Lead Optimization | Candidate Selection Gate | Side-by-side comparison of shortlisted candidates; AI recommendation with ICH Q6A criteria checklist; go/no-go readiness summary |
| 8 | Drug Substance | Synthesis Route Planning | Triggers ASKCOS retrosynthesis on selected candidate; proposes preferred route; flags buyability; cites ICH Q11 |
| 9 | Drug Substance | Salt & Polymorph Form Selection | Recommends counterion screening panel based on API pKa; proposes screening conditions; cites ICH Q6A solid form requirements |
| 10 | Drug Product | Drug Product Target Definition | Proposes dosage form + route + dose + release type based on ADMET (Caco-2, BBB, solubility); cites ICH Q8(R2) |
| 11 | Drug Product | Excipient Selection & Compatibility | Recommends excipient set for proposed dosage form; flags known API–excipient incompatibilities; checks IIG limits; cites ICH Q8(R2) |
| 12 | Drug Product | Stability Study Design | Proposes ICH Q1A(R2) study matrix (conditions + timepoints); recommends tests per material type; cites ICH Q1A(R2) |
| 13 | Analytical | Analytical Method Development Plan | Proposes methods required (HPLC purity, assay, dissolution); outlines ICH Q2(R1) validation plan; cites ICH Q2(R1) |
| 14 | Preclinical | Preclinical Study Package Design | Proposes IND-enabling study package per ICH M3(R2); recommends species; flags safety concerns from ADMET; cites ICH M3(R2), S7A, S7B |
| 15 | Preclinical | IND Package Readiness Assessment | Reviews all phase data against IND requirements; generates readiness score per ICH section; produces IND gap list |

### Plan Step Coverage — Biologic (15 steps)

| Step | Phase | Title | Key AI Actions |
|---|---|---|---|
| 1 | Discovery | Antigen / Target Identification | `get_protein_detail`; reviews UniProt sequence + structural data; assesses druggability for biologic modalities |
| 2 | Discovery | Biologic Modality Selection | Proposes modality (mAb, nanobody, Fc-fusion, ADC, peptide) based on target biology + patient population; cites Carter 2006 |
| 3 | Discovery | Sequence Design & Humanization | Reviews VH/VL germline origin; scores humanization; flags immunogenicity liabilities; cites Jain et al. 2017 |
| 4 | Lead Optimization | Developability Assessment | Scores aggregation propensity, pI, hydrophobicity, viscosity risk; cites Jarasch et al. 2015 |
| 5 | Lead Optimization | Expression System Selection | Recommends CHO / HEK293 / E. coli / yeast based on glycosylation requirements; outlines transfection strategy |
| 6 | Drug Substance | Cell Line Development Plan | Clone selection criteria, stability testing plan, productivity targets; cites ICH Q5B |
| 7 | Drug Substance | Upstream Bioprocess Development | Bioreactor parameters (pH 7.0–7.4, DO 30–50%, temperature), CPPs, PAT requirements; cites ICH Q8(R2) adapted |
| 8 | Drug Substance | Downstream Purification Train Design | Protein A capture + IEX polishing + viral clearance steps; yield criteria per step; cites ICH Q5A |
| 9 | Analytical | Drug Substance Characterization Plan | Proposes SEC-HPLC, icIEF, glycan analysis, HCP ELISA, residual DNA, bioassay; cites ICH Q6B |
| 10 | Drug Product | Formulation Screening Design | Buffer/pH matrix, surfactant (PS20/PS80), stabilizer (sucrose/trehalose) screening; stress conditions; cites ICH Q8(R2) |
| 11 | Drug Product | Container Closure Selection | Vial vs. prefilled syringe; primary package compatibility; extractables/leachables considerations; cites ICH Q8(R2) |
| 12 | Drug Product | Lyophilization Design | Fill volume, target Tg′, primary/secondary drying conditions, cake appearance criteria (if applicable) |
| 13 | Drug Product | Stability Study Design | ICH Q5C stability matrix; degradation pathways for biologics (aggregation, deamidation, oxidation); cites ICH Q5C |
| 14 | Preclinical | Preclinical Safety Package Design | Species selection for biologics (pharmacological relevance); ICH S6(R1) study design; immunogenicity monitoring |
| 15 | Preclinical | BLA Readiness Assessment | Reviews all phase data against BLA CMC requirements; produces BLA gap list per FDA/EMA expectations |

### Pages
- Plan section embedded on `ProjectPage` (not a separate route)
- `AIPlanDetailPage` (`/projects/:id/ai-plan`) — full-page view of the plan timeline and all discussions when more space is needed

---

## Module 13 — Per-Page AI Panel (NEW)

### Purpose
A contextual AI assistant visible on every project page as a collapsible right-side panel. The panel always knows what the scientist is looking at — it receives the page's full data context. For AI-Driven projects, it additionally knows the current plan step and recent plan discussion.

### Panel Design

**Always visible on:** all per-project pages (all modules 1–10 project pages, biologics pages)
**Not shown on:** global pages (Dashboard, AI Lab, Drug Discovery search pages, Document Portal, Literature)

**Panel structure:**
- Collapsible (right edge toggle button; default open for AI-Driven, default closed for Manual)
- Width: 300px when open
- Header: page-type label (e.g., "Formulation Planning AI") + collapse icon
- Body: scrollable chat thread with markdown rendering + streaming indicator
- Tool call badges: shown inline (same pattern as ChatPage — `@search_chembl`, `@predict_admet`)
- Sources: expandable at bottom of each AI response (RAG citations + API sources)
- Input: text field + send button + file attachment button (uploads to Document Portal)

### Panel Context — Manual Projects

Context package sent with every panel message:
```
{
  page_type: "FormulationPlanningPage",
  project: { id, name, phase, pathway, molecule_type },
  page_entity: { ...full current page data... },
  phase_status: { ...all phase statuses... },
  recent_experiments: [ ...last 5 experiments... ]
}
```
System prompt is page-type-specific. Example for Formulation Planning:
> "You are a pharmaceutical formulation expert assisting a scientist on BioIntel's Formulation Planning page. You have access to the scientist's current formulation plan. Reference ICH Q8(R2) and your knowledge of excipient chemistry when advising. Use tools to check FDA IIG limits and excipient incompatibilities. Always cite your sources."

Session-only history (last 20 messages). Not persisted across browser sessions for Manual projects.

### Panel Context — AI-Driven Projects

Context package additionally includes:
```
{
  ...all of the above...,
  current_plan_step: { step_number, title, status, ai_recommendation, ai_reasoning },
  plan_summary: AIPlan.conversation_context.summary,
  recent_plan_discussion: [ ...last 5 discussion messages for current step... ]
}
```

When the scientist is on a page that directly corresponds to the current plan step (e.g., on Formulation Planning page during step 10), the panel surfaces the step recommendation at the top of its thread:

> *"AI-Driven Plan — Step 10: Drug Product Target Definition"*
> *[step recommendation rendered here]*
> *"I'm here to help with questions about this step or any other formulation question."*

Discussion from the panel is saved to `AIPlanDiscussion` (same records as the plan step's discussion thread). The scientist doesn't need to go back to the project page to continue the step conversation.

### Tool Access
All 16 existing Chat Assistant tools are available in the panel, plus:
- `get_page_context(page_type, entity_id)` — fetches fresh data for the current page entity
- `get_plan_step(step_id)` — fetches the current plan step with full reasoning (AI-Driven only)

### Pages
- `AIPagePanel` component mounted in `App.vue`, conditionally rendered based on route (project pages only) and project mode

---

## Module 14 — Document Portal (NEW)

### Purpose
A central repository for scientist-uploaded documents. All uploaded documents are ingested into the RAG pipeline and become searchable by AI across all AI-Driven projects. This is where scientists bring their institutional knowledge into the AI system — prior studies, competitor analyses, regulatory submissions, internal research reports.

### Document Portal Page (`/documents`)

**Upload area:**
- Drag-and-drop zone + "Browse files" button
- Accepted formats: PDF, DOCX, TXT
- File size limit: 50 MB per file
- On upload: file stored in `MEDIA_ROOT/documents/`, `RagDocument` record created with `ingestion_status: pending`
- Background ingestion triggered immediately: PDF → text extraction → chunking → embedding → stored as `RagChunk` records

**Document metadata form** (shown after upload):
- Document name (pre-filled from filename)
- Document type: lab_report / internal_study / regulatory_submission / competitor_analysis / clinical_data / protocol / other
- Molecule type: small_molecule / biologic / both
- Phase relevance (multi-select): discovery / lead_optimization / drug_substance / drug_product / analytical / preclinical / regulatory
- Linked projects (optional, multi-select from project list)
- Notes (free text)

**Document list:**
- Card grid with: name, document type badge, upload date, ingestion status badge (processing [animated] / ready [green] / failed [red]), page count, linked project count
- Search bar: semantic search across all uploaded documents (query embedded, cosine similarity against all chunks)
- Filter by: document type, molecule type, phase relevance, linked project
- Per-document actions: Preview (opens PDF viewer showing first 3 pages), Edit metadata, Delete (with confirmation), Re-ingest (if failed)

**Ingestion status:**
- `pending`: queued
- `processing`: text extraction + chunking + embedding in progress
- `ready`: all chunks embedded and stored, document searchable
- `failed`: ingestion error (shown with error message, re-ingest button)

### RAG Retrieval Scope

When the AI (plan generation, step discussion, per-page panel, AI Lab) performs a RAG lookup, it searches:
1. **Pharmaceutical playbook corpus** — ICH guidelines + academic papers (global, always available)
2. **Project-linked documents** — all documents in the Document Portal tagged to the current project
3. **Global documents** — documents uploaded without a project tag (available to all projects)

The retrieval always returns the top 5 chunks most relevant to the query + context (phase, molecule_type). Each retrieved chunk is included in the AI's context and cited in the response: `[Source: your_internal_report.pdf, p.12]`.

### Pages
- `DocumentPortalPage` — upload, list, search, manage all documents

---

## Module 15 — Biologics Pathway (NEW)

### Purpose
A parallel development track for scientists developing biologics: antibodies (monoclonal, bispecific, nanobody), proteins, peptides, ADCs, and gene therapy constructs. The biologics pathway uses the same phase structure as small molecule but with entirely different content at each phase, guided by ICH Q5-series guidelines and S6(R1) for preclinical safety.

Activated by setting `molecule_type = biologic` on the project.

### 15A — Biologics Target & Antigen Profiling

**Purpose**: Characterize the target antigen/protein with sequence-level detail. Determine whether the biological target is amenable to a biologic modality.

**User Workflow:**

**Step 1: Antigen Identification**
- Search UniProt by gene name or protein name
- Retrieve: sequence (FASTA), known isoforms, post-translational modifications, tissue expression, disease associations
- Identify accessible epitopes: extracellular domains, known antibody binding regions from literature
- Assess target validation: genetic evidence, biomarker data, published antibody studies

**Step 2: Modality Selection**
- Based on antigen biology, AI proposes the most appropriate biologic modality:
  - Monoclonal antibody (IgG1, IgG4)
  - Bispecific antibody
  - Nanobody / single-domain antibody
  - Antibody-drug conjugate (ADC)
  - Fc-fusion protein
  - Peptide therapeutic
- Each option shown with: mechanism, typical development timeline, key development challenges, precedent examples from ChEMBL biologics

**Pages:**
- `BiologicsTargetPage` — antigen profiling, modality selection

### 15B — Antibody Design & Developability

**Purpose**: Assess the sequence-level properties of a lead antibody candidate for developability risk prior to committing to cell line development.

**User Workflow:**

**Step 1: Sequence Input**
- Paste VH/VL sequences in FASTA format
- System identifies CDR regions (Kabat/Chothia numbering)
- Germline analysis: IMGT/V-QUEST lookup (or local germline database) — shows closest human germline gene, identity %, potential immunogenicity flags

**Step 2: Developability Scoring**
For each antibody candidate, the system computes or retrieves:
- **Aggregation risk**: hydrophobic patches in CDR, TANGO/CamSol score (where available)
- **Isoelectric point (pI)**: calculated from sequence; optimal range 5.0–9.5 for most formulations
- **Viscosity risk**: high pI + hydrophobic surface area = high viscosity risk flag
- **Chemical liabilities**: Asn-Gly/Asn-Ser (deamidation), Met/Trp (oxidation), Asp-Pro (hydrolysis), N-terminal Glu (pyroglutamate)
- **Poly-specificity**: predicted non-specific binding risk
- Overall **developability score**: composite (green/amber/red)

**Step 3: Candidate Comparison**
- Side-by-side comparison of up to 4 antibody candidates across all developability metrics
- Color-coded heatmap (same pattern as SAR Tracker heatmap)
- "Select Lead" action — pins candidate to project as the development compound

**Pages:**
- `AntibodyDesignPage` — sequence input, developability scoring, candidate comparison

### 15C — Cell Line Development

**Purpose**: Plan and track the cell line development campaign for the selected biologic candidate.

**User Workflow:**

**Step 1: Expression System Selection**
- CHO (DG44, K1, CHO-S) — standard for complex glycoproteins, mAbs
- HEK293 — transient expression for rapid characterization, stable for some products
- E. coli — for non-glycosylated proteins, Fab fragments
- Yeast (Pichia pastoris) — for certain glycoproteins
- Insect (Sf9/Hi5 with baculovirus) — for VLPs, some complex proteins
- For each: AI note on typical yield range, glycan profile, regulatory precedent, recommended scale-up path

**Step 2: Transfection & Selection Strategy**
- Stable transfection: linearized plasmid, lentiviral, site-specific integration (CRISPR)
- Selection markers: G418, hygromycin, MTX amplification
- Cloning method: limiting dilution, FACS sorting, Clonepix
- Expected timeline: transfection → selection → single-cell cloning → clone screening

**Step 3: Clone Selection Criteria**
- Define: minimum productivity target (mg/L), maximum aggregation (% monomer), minimum purity (% main peak SEC), minimum growth rate
- Screening plan: how many clones to screen at each funnel stage
- GMP bank timeline: research bank → master cell bank → working cell bank

**Step 4: Genetic Stability Plan**
- Per ICH Q5B: outline stability testing timeframe (passage number or time-based)
- Define acceptance criteria for genetic stability (copy number, integration site consistency)

**Data Captured:**

| Entity | Key Fields |
|---|---|
| `CellLineDevelopment` | project, expression_system, vector_name, selection_marker, cloning_method, productivity_target_mg_l, aggregation_limit_pct, purity_target_pct, stability_plan, status |

**Pages:**
- `CellLineDevelopmentPage`

### 15D — Upstream Bioprocess Development

**Purpose**: Develop and document the bioreactor process for producing the biologic drug substance. Define critical process parameters (CPPs) and critical quality attributes (CQAs).

**User Workflow:**

**Step 1: Bioreactor Configuration**
- Scale: shake flask → ambr15/250 (microscale) → 2L bench → 50L pilot → 500L manufacturing
- Mode: batch / fed-batch / perfusion
- Vessel type: glass stirred tank / single-use bag bioreactor

**Step 2: Process Parameter Documentation**
For each scale, the scientist records:

| CPP | Typical Range | CQA Impact |
|---|---|---|
| pH | 6.8–7.4 | glycosylation, charge variants |
| Dissolved Oxygen (DO) | 20–60% | productivity, aggregation |
| Temperature | 36–37°C (growth) → 31–34°C (production) | productivity, glycan profile |
| Agitation (rpm) | scale-dependent | cell viability, dissolved oxygen |
| CO₂ | 5–10% headspace | pH control |
| Osmolality | 280–350 mOsm/kg | cell growth |
| Feed additions | schedule, volume, composition | productivity, impurity profile |

**Step 3: Media Development**
- Basal media selection: proprietary or commercial (CD CHO, EX-CELL Advanced)
- Feed strategy: glucose-limited fed-batch, concentrated nutrient feed
- Supplements: anti-clumping agent, growth factors (where applicable)

**Step 4: Process Analytics (PAT)**
- Inline sensors: pH, DO, temperature, capacitance (biomass)
- At-line: cell viability (Vi-Cell), glucose/lactate (BioProfile)
- Off-line at harvest: titer (Protein A HPLC), aggregation (SEC-HPLC), charge variants (icIEF)

**Data Captured:**

| Entity | Key Fields |
|---|---|
| `BioprocessDevelopment` | project, scale, mode, vessel_type, cpps (JSON), cqas (JSON), media_name, feed_strategy, pat_requirements, status |

**Pages:**
- `UpstreamBioprocessingPage`

### 15E — Downstream Purification

**Purpose**: Design and track the purification train that takes the bioreactor harvest and produces a purified drug substance.

**User Workflow:**

**Step 1: Purification Train Design**
Standard purification train for mAbs (customizable for other modalities):

| Step | Unit Operation | Purpose | Acceptance Criteria |
|---|---|---|---|
| 1 | Clarification (depth filtration + 0.2μm) | Cell removal | Turbidity < 5 NTU |
| 2 | Protein A affinity capture (e.g., MabSelect SuRe) | Primary capture, ~1000× purification | ≥90% yield, HCP < 10,000 ppm |
| 3 | Viral inactivation (low pH, pH 3.5, 60 min) | Process-related safety | Per ICH Q5A |
| 4 | Cation exchange (bind-elute or flow-through) | Charge variant removal | Monomer ≥ 99%, HCP < 100 ppm |
| 5 | Anion exchange (flow-through) | DNA, endotoxin, HCP polishing | Endotoxin < 0.1 EU/mg |
| 6 | Viral filtration (20nm filter) | Viral clearance | Per ICH Q5A |
| 7 | Ultrafiltration / Diafiltration (UFDF) | Concentration + buffer exchange | Target concentration + formulation buffer |

For each step: entry criteria, operating conditions, pool criteria (yield, purity, key impurity limits).

**Step 2: Yield and Mass Balance**
- Per-step yield tracking: target yield %, acceptable range
- Running mass balance from harvest titer to final DS concentration
- Overall process yield target (typically 60–80% for mAbs)

**Step 3: Impurity Clearance**
- HCP (host cell proteins): target < 100 ppm at DS
- Residual DNA: target < 10 ng/mg at DS
- Protein A leachate: target < 10 ppm
- Endotoxin: target < 0.1 EU/mg
- Aggregate / fragment: target ≥ 99% monomer

**Data Captured:**

| Entity | Key Fields |
|---|---|
| `DownstreamPurification` | project, steps (JSON — array of purification step objects), overall_yield_target, hcp_target_ppm, dna_target_ng_mg, endotoxin_target, monomer_target_pct, status |

**Pages:**
- `DownstreamPurificationPage`

### 15F — Biologics Analytical Characterization

**Purpose**: Plan and track the analytical methods specific to biologic characterization. Different from small molecule analytical development — covers higher-order structure, charge variants, glycosylation, process impurities, and bioassay.

**Method Types (Biologics-Specific):**

| Method | What It Measures | ICH Basis |
|---|---|---|
| SEC-HPLC | Aggregation (% HMW), fragmentation (% LMW), monomer purity | ICH Q6B |
| icIEF (imaged capillary isoelectric focusing) | Charge heterogeneity (acidic/basic variants, pI) | ICH Q6B |
| Glycan analysis (HILIC-UPLC or CE-LIF) | N-glycan profile (G0F, G1F, G2F, afucosylation, sialylation) | ICH Q6B |
| HCP ELISA | Host cell protein concentration (ppm) | ICH Q6B, Q5A |
| Residual DNA (qPCR) | Host cell DNA (ng/mg DS) | ICH Q5A |
| Bioassay / Cell-based assay | Potency (relative to reference standard) | ICH Q6B |
| SPR (surface plasmon resonance) | Binding kinetics (kon, koff, KD) to target antigen | — |
| CD spectroscopy | Secondary structure confirmation | ICH Q6B |
| DSC / nano-DSF | Thermal stability (Tm), conformational stability | — |
| Peptide mapping (LC-MS/MS) | Sequence confirmation, PTM characterization | ICH Q6B |
| SDS-PAGE / CE-SDS (R and NR) | Molecular weight, purity under reducing/non-reducing conditions | ICH Q6B |

**Per-Method Tracking:** same structure as v2 Analytical Methods — development log, parameters, ICH Q2(R1) validation checklist.

**Data Captured:**

| Entity | Key Fields |
|---|---|
| `BiologicsCharacterizationMethod` | project, method_type, purpose, parameters (JSON), status |

**Pages:**
- `BiologicsAnalyticsPage`

### 15G — Biologics Formulation

**Purpose**: Design the drug product formulation for the biologic. Different from small molecule — focused on buffer composition, pH, surfactant, stabilizer, container closure, and lyophilization (if applicable).

**User Workflow:**

**Step 1: Formulation Target**
- Target concentration (mg/mL)
- Route: SC (subcutaneous) / IV (intravenous) / IM / intravitreal
- Volume per dose (e.g., ≤1.5 mL for SC)
- Patient population (self-injection pen → viscosity constraint < 20 cP; hospital IV → pH/osmolality tolerance)
- Presentation: liquid (vial) / liquid (PFS) / lyophilized vial

**Step 2: Buffer Screening**
- Common buffers for biologics: histidine (pH 5.5–6.5), citrate (pH 5.0–7.0), acetate (pH 4.0–5.5), phosphate (pH 6.0–8.0)
- Screening matrix: 3 buffers × 3 pH values × triplicate
- Stability indicator: thermal stress (40°C/1 week), mechanical stress (agitation), freeze-thaw
- Readout: % aggregation (SEC-HPLC), % charge variants (icIEF), appearance

**Step 3: Stabilizer Screening**
- Sugars/polyols: sucrose (typical 5–10% w/v), trehalose, sorbitol, mannitol
- For lyophilization: bulking agent selection (mannitol, glycine), collapse temperature (Tg′) measurement
- Surfactants: Polysorbate 20 (0.02–0.1% w/v), Polysorbate 80, Poloxamer 188 — protection against interface-induced aggregation

**Step 4: Container Closure**
- Vial: glass (Type I borosilicate), stopper compatibility, headspace gas (N₂ or air)
- Prefilled syringe: barrel material (glass or CoC), needle gauge, plunger stopper, tip cap
- Extractables/leachables assessment per ICH Q8(R2) and USP <661>

**Step 5: Lyophilization Design** (if applicable)
- Target Tg′ determination (DSC with formulation)
- Cycle design: loading temperature, freezing ramp, annealing (if needed), primary drying (temperature, pressure, duration), secondary drying
- Target residual moisture (< 1% w/w)
- Cake appearance criteria: elegant cake, no collapse, acceptable reconstitution time

**Data Captured:**

| Entity | Key Fields |
|---|---|
| `BiologicsFormulation` | project, target_concentration_mg_ml, route, volume_per_dose_ml, presentation, buffer_name, buffer_ph, stabilizer_name, stabilizer_pct, surfactant_name, surfactant_pct, container_type, lyo_cycle (JSON), status |

**Pages:**
- `BiologicsFormulationPage`

### External Data Sources (Biologics-Specific)

| Source | Use |
|---|---|
| UniProt REST | Antigen sequence, isoforms, PTMs, tissue expression |
| IMGT/V-QUEST (API or local germline DB) | VH/VL germline assignment, humanization scoring |
| RCSB PDB | Antigen 3D structure, known antibody–antigen complexes |
| ChEMBL biologics subset | Precedent antibodies for the same target |
| OpenFDA (BLA guidance) | BLA CMC requirements, FDA biologics guidance |
| FDA Purple Book | Licensed biological products, reference product for biosimilars |

---

## Navigation Structure

```
BioIntel
│
├── Dashboard
│
├── AI Lab (NEW)
│   └── [AI Lab session list + new intake chat]
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
│   ─── Per-Project Navigation (all projects) ───
│
│   ├── Overview (Project Page)
│   │     └── [AI-Driven Plan timeline — AI-Driven projects only]
│   │
│   ├── Lead Optimization
│   │   ├── Compound Profile
│   │   ├── SAR Tracker
│   │   └── Candidate Selection
│   │
│   ├── Drug Substance (Small Molecule)
│   │   ├── Synthesis Hub
│   │   ├── Salt & Polymorph Screening
│   │   └── Process Development
│   │
│   ├── Drug Substance (Biologic) [molecule_type = biologic]
│   │   ├── Cell Line Development
│   │   └── Upstream Bioprocessing
│   │
│   ├── Drug Product (Small Molecule)
│   │   ├── Formulation Planning
│   │   ├── Excipient Library
│   │   └── Stability Planning
│   │
│   ├── Drug Product (Biologic) [molecule_type = biologic]
│   │   ├── Downstream Purification
│   │   └── Biologics Formulation
│   │
│   ├── Analytical
│   │   ├── Methods (+ Biologics Characterization Methods for biologic projects)
│   │   └── Specifications
│   │
│   ├── Preclinical
│   │   ├── ADMET Dashboard
│   │   ├── Study Planner
│   │   └── Risk Assessment
│   │
│   └── Documents
│
├── Documents (NEW) ← Document Portal
│
├── Research
│   └── Literature & Clinical Trials
│
└── Chat Assistant (Manual projects; AI-Driven projects use per-page panel)
```

---

## Pharmaceutical AI Playbook

The AI Playbook is the corpus of peer-reviewed and regulatory documents that grounds every AI recommendation. It is ingested at deployment and never shown directly to users — it is retrieved automatically at each AI action.

### ICH Guidelines (freely available at ich.org)

**Quality (Q-series):**
| Guideline | Subject |
|---|---|
| Q1A(R2) | Stability Testing of New Drug Substances and Products |
| Q2(R1) | Validation of Analytical Procedures |
| Q3A(R2) | Impurities in New Drug Substances |
| Q3B(R2) | Impurities in New Drug Products |
| Q3C(R5) | Residual Solvents |
| Q3D(R1) | Elemental Impurities |
| Q6A | Specifications: Test Procedures and Acceptance Criteria — Chemical Substances |
| Q6B | Specifications: Test Procedures and Acceptance Criteria — Biotechnological Products |
| Q8(R2) | Pharmaceutical Development |
| Q9(R1) | Quality Risk Management |
| Q11 | Development and Manufacture of Drug Substances |

**Biologics Quality (Q5-series):**
| Guideline | Subject |
|---|---|
| Q5A(R2) | Viral Safety Evaluation of Biotechnology Products |
| Q5B | Analysis of the Expression Construct in Cells |
| Q5C | Stability Testing of Biotechnological/Biological Products |
| Q5E | Comparability of Biotechnological/Biological Products |

**Safety (S-series) and Multidisciplinary (M-series):**
| Guideline | Subject |
|---|---|
| M3(R2) | Non-Clinical Safety Studies for Clinical Trials and Marketing Authorization |
| S2(R1) | Genotoxicity Testing |
| S5(R3) | Reproductive Toxicology |
| S6(R1) | Preclinical Safety Evaluation of Biotechnology-Derived Pharmaceuticals |
| S7A | Safety Pharmacology Studies |
| S7B | The Non-Clinical Evaluation of the Potential for Delayed Ventricular Repolarization |

### Academic Papers — Small Molecule Drug Discovery

| Reference | Key Contribution | Applied At |
|---|---|---|
| Lipinski et al. (1997) *Adv. Drug Deliv. Rev.* | Rule of Five (MW ≤ 500, LogP ≤ 5, HBD ≤ 5, HBA ≤ 10) | Steps 4–7 |
| Hopkins & Groom (2002) *Nat. Rev. Drug Discov.* | Druggable genome; target assessment criteria | Step 1 |
| Bleicher et al. (2003) *Nat. Rev. Drug Discov.* | Hit and lead generation methodology; HTS vs FBDD | Steps 4–5 |
| Gleeson (2008) *J. Med. Chem.* | Simple ADMET rules; thresholds for LogP, MW, HBD | Step 5 |
| Wager et al. (2010) *ACS Chem. Neuroscience* | CNS MPO score; multi-parameter optimization | Steps 5–6 |
| Leeson & Springthorpe (2007) *Nat. Rev. Drug Discov.* | Drug-like concepts; lipophilicity optimization | Step 6 |

### Academic Papers — Biologics Development

| Reference | Key Contribution | Applied At |
|---|---|---|
| Carter (2006) *Nat. Rev. Immunol.* | Antibody therapeutics design principles; engineering for efficacy | Steps 2–3 |
| Jarasch et al. (2015) *J. Pharm. Sci.* | Developability assessment during antibody selection | Step 4 |
| Jain et al. (2017) *PNAS* | Biophysical properties of clinical-stage antibodies; developability benchmarks | Step 4 |

---

## Database Schema — New Tables (v3 Additions)

The following tables are new in v3. All v2 tables are unchanged.

### `ai_plans`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | |
| status | VARCHAR(20) | draft / active / paused / completed / archived |
| molecule_type | VARCHAR(20) | small_molecule / biologic / undetermined |
| disease_description | TEXT | free-text from intake |
| constraints | JSON | `{avoid_mechanisms, patent_constraints, patient_population, timeline}` |
| conversation_context | JSON | compressed summary; `{summary, compressed_at, message_count}` |
| step_count | INTEGER | cached total steps |
| current_step_number | INTEGER | nullable; currently active step |
| created_at | DATETIME | auto_now_add |
| updated_at | DATETIME | auto_now |

### `ai_plan_steps`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| plan_id | INTEGER FK → ai_plans | |
| step_number | INTEGER | order within plan (1-based) |
| phase | VARCHAR(30) | discovery / lead_optimization / drug_substance / drug_product / analytical / preclinical / regulatory |
| title | VARCHAR(255) | |
| description | TEXT | what this step involves |
| status | VARCHAR(30) | pending / in_progress / awaiting_approval / approved / revision_needed / completed / skipped / abandoned |
| ai_recommendation | JSON | structured recommendation output |
| ai_reasoning | TEXT | full narrative reasoning |
| scientist_feedback | TEXT | latest scientist revision request |
| entities_created | JSON | `[{type, id, display_name}]` |
| experiment_required | BOOLEAN | default False |
| experiment_id | INTEGER FK → experiments | nullable |
| rag_sources | JSON | `[{document_name, chunk_index, text_preview}]` |
| created_at | DATETIME | auto_now_add |
| updated_at | DATETIME | auto_now |

### `ai_plan_discussions`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| plan_id | INTEGER FK → ai_plans | |
| step_id | INTEGER FK → ai_plan_steps | nullable; null = plan-level discussion |
| role | VARCHAR(10) | ai / scientist |
| content | TEXT | full message text |
| tool_calls | JSON | `[{name, input, result}]` |
| sources | JSON | `[{type: rag/api, document, chunk_text, api_name}]` |
| created_at | DATETIME | auto_now_add |

### `rag_documents`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| name | VARCHAR(255) | |
| document_type | VARCHAR(30) | ich_guideline / academic_paper / lab_report / regulatory_submission / competitor_analysis / clinical_data / protocol / other |
| molecule_type | VARCHAR(20) | small_molecule / biologic / both |
| phase_relevance | JSON | list of phase names |
| file_path | VARCHAR(500) | relative path in MEDIA_ROOT |
| page_count | INTEGER | nullable |
| ingestion_status | VARCHAR(20) | pending / processing / ready / failed |
| ingestion_error | TEXT | nullable; error message if failed |
| project_id | INTEGER FK → projects | nullable; null = global |
| uploaded_by | VARCHAR(100) | username or email |
| created_at | DATETIME | auto_now_add |

### `rag_chunks`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| document_id | INTEGER FK → rag_documents | |
| chunk_index | INTEGER | 0-based position within document |
| chunk_text | TEXT | ~500 tokens of content |
| embedding | JSON | float array (384 dims, all-MiniLM-L6-v2); pgvector column in production |
| created_at | DATETIME | auto_now_add |

### Additions to Existing Models

| Model | New Field | Type | Default | Notes |
|---|---|---|---|---|
| `Project` | `mode` | VARCHAR(20) | `manual` | manual / ai_driven |
| `Project` | `molecule_type` | VARCHAR(20) | `small_molecule` | small_molecule / biologic / undetermined |
| `Compound` | `sequence` | TEXT | null | amino acid / nucleotide sequence for biologics |

### New Biologics Models

#### `cell_line_developments`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | |
| expression_system | VARCHAR(30) | cho / hek293 / ecoli / yeast / insect |
| vector_name | VARCHAR(255) | |
| selection_marker | VARCHAR(100) | |
| cloning_method | VARCHAR(50) | limiting_dilution / facs / clonepix / other |
| productivity_target_mg_l | FLOAT | |
| aggregation_limit_pct | FLOAT | |
| purity_target_pct | FLOAT | |
| stability_plan | TEXT | |
| status | VARCHAR(20) | planned / in_progress / complete |
| created_at | DATETIME | |

#### `bioprocess_developments`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | |
| scale | VARCHAR(30) | microscale / bench / pilot / manufacturing |
| mode | VARCHAR(20) | batch / fed_batch / perfusion |
| vessel_type | VARCHAR(50) | glass_stir_tank / single_use_bag |
| cpps | JSON | `{ph: {target, range}, do: {...}, temp: {...}, ...}` |
| cqas | JSON | `{titer, aggregation, charge_variants, ...}` |
| media_name | VARCHAR(255) | |
| feed_strategy | TEXT | |
| pat_requirements | TEXT | |
| status | VARCHAR(20) | planned / in_progress / complete |
| created_at | DATETIME | |

#### `downstream_purifications`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | |
| steps | JSON | array of `{order, unit_op, purpose, entry_criteria, conditions, pool_criteria, expected_yield_pct}` |
| overall_yield_target_pct | FLOAT | |
| hcp_target_ppm | FLOAT | |
| dna_target_ng_mg | FLOAT | |
| endotoxin_target_eu_mg | FLOAT | |
| monomer_target_pct | FLOAT | |
| status | VARCHAR(20) | planned / in_progress / complete |
| created_at | DATETIME | |

#### `biologics_formulations`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | |
| target_concentration_mg_ml | FLOAT | |
| route | VARCHAR(30) | sc / iv / im / intravitreal |
| volume_per_dose_ml | FLOAT | |
| presentation | VARCHAR(30) | liquid_vial / liquid_pfs / lyophilized_vial |
| buffer_name | VARCHAR(100) | |
| buffer_ph | FLOAT | |
| stabilizer_name | VARCHAR(255) | |
| stabilizer_pct | FLOAT | |
| surfactant_name | VARCHAR(100) | |
| surfactant_pct | FLOAT | |
| container_type | VARCHAR(50) | |
| lyo_cycle | JSON | nullable; `{loading_temp, freezing_ramp, anneal, primary_dry, secondary_dry, target_moisture_pct}` |
| status | VARCHAR(20) | draft / active / locked |
| created_at | DATETIME | |

#### `biologics_characterization_methods`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK → projects | |
| method_type | VARCHAR(30) | sec_hplc / icief / glycan / hcp_elisa / residual_dna / bioassay / spr / cd / dsc_nandof / peptide_mapping / ce_sds / other |
| purpose | VARCHAR(50) | aggregation / charge_variant / glycan / impurity / potency / binding / structure / purity |
| parameters | JSON | method-type-specific parameters |
| status | VARCHAR(20) | in_development / developed / validated |
| created_at | DATETIME | |

---

## Implementation Update — v3.1 (Manual AI Panel)

> **Date:** 2026-06-02  
> **Scope:** Per-page AI assistant for Manual projects — ask-then-confirm field suggestions + persistent per-page chat history.

### What Was Built

This update delivers the core UX for AI-assisted work in Manual mode. Scientists can now have a contextual conversation with the AI on any project page, ask for field recommendations, and confirm the suggested values with a single click — without needing any pharmaceutical background.

### Ask-Then-Confirm Suggestion Mechanism

The AI panel can suggest concrete values for the form fields on the current page. When it does, a **Suggestion Card** appears below the AI's response:

- Each suggested field is shown with a human-readable label and the proposed value
- Each field has a checkbox (all checked by default)
- **"Apply All"** and **"Apply Selected"** buttons apply the chosen values directly into the page form
- The scientist can mix-and-match: apply some fields, reject others, ask follow-up questions before applying
- Values are applied without a page reload — the form updates reactively

**How the AI is guided to suggest values:**

The system prompt for every per-page panel chat includes:
1. A **page-context block** listing the current page's fields, their labels, optional hints, and the field's current value (if any)
2. A **suggestion format instruction** telling the AI to append a `<suggestion>{"key": "value"}</suggestion>` block at the end of its response when it has concrete recommendations

The frontend strips the `<suggestion>` block before rendering the AI's message text, so scientists never see the raw XML.

**Pages with suggestion support (11 pages):**

| Page | Fields AI Can Suggest |
|---|---|
| Project Setup | name, description, phase, status, pathway, mode, molecule_type; TPP fields (target_patient_population, target_indication, clinical_endpoint) |
| Formulation Planning | dosage_form, route_of_administration, target_dose, excipients, ph_target, manufacturing_process, shelf_life_target, storage_conditions |
| Stability Planning | study_type, storage_conditions, time_points, analytical_tests, acceptance_criteria, oos_action_plan |
| SAR Tracker | optimization_notes, herg_ic50, solubility_um, bioavailability_pct, half_life_h, binding_affinity, selectivity_notes |
| Specification Builder | test_name, method, acceptance_criteria, frequency, reference_standard |
| Preclinical Study Planner | study_type, species, dose_levels, route, duration_weeks, endpoints, regulatory_basis |
| Analytical Method | method_name, method_type, column, mobile_phase, detection, run_time_min, lod, loq |
| Salt & Polymorph | counterion, screening_conditions, polymorph_form, stability_notes, solubility_improvement |
| Process Development | cpp_notes (process parameter and CPP narrative) |
| Synthesis Hub | display-only (shows plan count; no direct field apply) |
| ADMET Dashboard | display-only (shows molecule type; no direct field apply) |

### Per-Page Persistent Chat History

Each page in each project has its own independent chat history. The history persists as long as the browser session is open — reopening the panel, navigating away and back, or switching between pages all preserve the correct conversation thread.

**Key behaviors:**
- Navigating from Formulation Planning to Stability Planning and back restores each page's own conversation
- Switching projects also switches chat history
- The "↺" (clear) button in the panel header wipes only the current page's history
- History is scoped to: **project ID + page type** — the same page type in two different projects has separate histories

### Scope for This Update

This update covers **Manual mode only**. AI-Driven projects will receive plan-context injection into the panel in a subsequent update. The infrastructure (store, composable, suggestion parsing) is already in place and designed to support plan-aware context with no structural changes.

### Non-Scientist Usability

The design intentionally requires no domain knowledge:

1. Open any project page and click "✦ AI Assistant" in the top bar
2. Describe what you're trying to do in plain English (e.g., "I'm developing an oral tablet for hypertension, what should I fill in here?")
3. The AI responds with an explanation and a Suggestion Card showing concrete values
4. Check the fields you want and click "Apply Selected"
5. The form pre-fills; the scientist can review and adjust before saving
