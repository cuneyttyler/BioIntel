import json
import anthropic
from django.conf import settings

from . import pubchem, chembl, opentargets, uniprot, pkcsm, comptox
from . import openfda, dailymed, clinicaltrials, pubmed, askcos, nist, surechembl, pdb

MODEL = 'claude-sonnet-4-6'

# ─── Provider configuration ───────────────────────────────────────────────────

MISTRAL_BASE_URL = 'https://api.mistral.ai/v1'

def get_active_llm_config():
    """Returns (provider, model, api_key, custom_endpoint) from DB settings, falling back to env."""
    try:
        from core.models import AppSettings
        s = AppSettings.objects.filter(pk=1).first()
        if s:
            if s.provider == 'claude':
                key = s.anthropic_api_key or settings.ANTHROPIC_API_KEY
            elif s.provider == 'openai':
                key = s.openai_api_key or getattr(settings, 'OPENAI_API_KEY', '')
            elif s.provider == 'mistral':
                key = s.mistral_api_key or getattr(settings, 'MISTRAL_API_KEY', '')
            else:
                key = s.custom_api_key
            return s.provider, s.model or MODEL, key, s.custom_endpoint
    except Exception:
        pass
    return 'claude', MODEL, settings.ANTHROPIC_API_KEY, ''


def _stream_openai_text(system: str, messages: list, model: str, api_key: str, base_url: str = ''):
    """Text-only streaming for OpenAI-compatible providers (OpenAI, Mistral, Custom)."""
    from openai import OpenAI
    kwargs = {'api_key': api_key}
    if base_url:
        kwargs['base_url'] = base_url
    client = OpenAI(**kwargs)

    oai_messages = [{'role': 'system', 'content': system}] + [
        {'role': m['role'], 'content': m['content'] if isinstance(m['content'], str) else json.dumps(m['content'])}
        for m in messages
    ]

    with client.chat.completions.create(
        model=model,
        messages=oai_messages,
        max_tokens=4096,
        stream=True,
    ) as stream:
        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield f'data: {json.dumps({"type": "text_delta", "text": delta.content})}\n\n'

    yield f'data: {json.dumps({"type": "message_stop"})}\n\n'

SYSTEM_PROMPT = """You are BioIntel, an expert AI assistant for drug development scientists. \
You help with synthesis planning, formulation development, risk analysis, regulatory strategy, \
and experimental design across the pre-clinical and clinical development pipeline.

When answering, always:
1. Use the available tools to fetch real data when the question involves a specific compound, disease, or clinical trial.
2. Cite every data source you use with the format [Source: <api_name>].
3. Be concise and actionable — scientists need clear next steps, not textbook summaries.
4. Highlight risks and uncertainties explicitly.

You have access to the following data sources via tools: PubChem, ChEMBL, Open Targets, UniProt, \
pkCSM (ADMET), EPA CompTox (toxicity), OpenFDA, DailyMed, ClinicalTrials.gov, PubMed, ASKCOS \
(synthesis), NIST WebBook (spectra), and FDA Guidance documents."""

TOOL_DEFINITIONS = [
    {
        'name': 'search_pubchem',
        'description': 'Search PubChem for a compound by name. Returns CID, SMILES, molecular weight, formula, XLogP, TPSA.',
        'input_schema': {
            'type': 'object',
            'properties': {'name': {'type': 'string', 'description': 'Compound name or synonym'}},
            'required': ['name'],
        },
    },
    {
        'name': 'search_chembl',
        'description': 'Search ChEMBL for a drug/compound by name. Returns mechanisms of action, approval status, bioactivity data.',
        'input_schema': {
            'type': 'object',
            'properties': {'name': {'type': 'string', 'description': 'Drug or compound name'}},
            'required': ['name'],
        },
    },
    {
        'name': 'search_disease',
        'description': 'Search Open Targets for a disease by name. Returns disease EFO ID, description, and associated drug targets.',
        'input_schema': {
            'type': 'object',
            'properties': {'term': {'type': 'string', 'description': 'Disease name (e.g. "type 2 diabetes")'}},
            'required': ['term'],
        },
    },
    {
        'name': 'get_disease_targets',
        'description': 'Get protein targets associated with a disease from Open Targets. Returns ranked target list with association scores.',
        'input_schema': {
            'type': 'object',
            'properties': {'efo_id': {'type': 'string', 'description': 'EFO ID of the disease (e.g. "EFO_0000400")'}},
            'required': ['efo_id'],
        },
    },
    {
        'name': 'get_protein_detail',
        'description': 'Get protein function, disease associations, and tissue expression from UniProt.',
        'input_schema': {
            'type': 'object',
            'properties': {'uniprot_id': {'type': 'string', 'description': 'UniProt accession (e.g. "P00533")'}},
            'required': ['uniprot_id'],
        },
    },
    {
        'name': 'predict_admet',
        'description': 'Predict ADMET profile for a compound from its SMILES string using pkCSM. Returns solubility, permeability, CYP inhibition, hERG, AMES, hepatotoxicity.',
        'input_schema': {
            'type': 'object',
            'properties': {'smiles': {'type': 'string', 'description': 'Isomeric SMILES string of the compound'}},
            'required': ['smiles'],
        },
    },
    {
        'name': 'get_safety_data',
        'description': 'Get toxicity and hazard data for a compound from EPA CompTox Dashboard.',
        'input_schema': {
            'type': 'object',
            'properties': {'compound_name': {'type': 'string', 'description': 'Compound name for CompTox lookup'}},
            'required': ['compound_name'],
        },
    },
    {
        'name': 'search_fda_labels',
        'description': 'Search FDA drug labels (OpenFDA) for drug information including inactive ingredients, dosage forms.',
        'input_schema': {
            'type': 'object',
            'properties': {'drug_name': {'type': 'string', 'description': 'Drug brand or generic name'}},
            'required': ['drug_name'],
        },
    },
    {
        'name': 'get_drug_label',
        'description': 'Get authoritative drug label from DailyMed with indications, warnings, and clinical pharmacology.',
        'input_schema': {
            'type': 'object',
            'properties': {'drug_name': {'type': 'string', 'description': 'Drug name for DailyMed lookup'}},
            'required': ['drug_name'],
        },
    },
    {
        'name': 'search_clinical_trials',
        'description': 'Search ClinicalTrials.gov for trials by condition and/or intervention.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'condition': {'type': 'string', 'description': 'Medical condition or disease'},
                'intervention': {'type': 'string', 'description': 'Drug or intervention name'},
                'phase': {'type': 'string', 'description': 'Trial phase: PHASE1, PHASE2, PHASE3, or PHASE4'},
            },
            'required': [],
        },
    },
    {
        'name': 'search_pubmed',
        'description': 'Search PubMed for biomedical literature. Returns article titles, authors, journals, and abstracts.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'query': {'type': 'string', 'description': 'PubMed search query'},
                'max_results': {'type': 'integer', 'description': 'Maximum number of results (default 10)', 'default': 10},
            },
            'required': ['query'],
        },
    },
    {
        'name': 'plan_synthesis',
        'description': 'Run single-step retrosynthesis for a target compound using ASKCOS. Returns precursor candidates with confidence scores.',
        'input_schema': {
            'type': 'object',
            'properties': {'smiles': {'type': 'string', 'description': 'Target molecule SMILES'}},
            'required': ['smiles'],
        },
    },
    {
        'name': 'get_nist_spectrum',
        'description': 'Get IR or MS reference spectrum from NIST WebBook for a compound by CAS number.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'cas': {'type': 'string', 'description': 'CAS registry number'},
                'spec_type': {'type': 'string', 'description': 'Spectrum type: IR or MS', 'enum': ['IR', 'MS']},
            },
            'required': ['cas'],
        },
    },
    {
        'name': 'search_fda_guidance',
        'description': 'Search FDA guidance documents for process validation, CMC, PAT, and regulatory topics.',
        'input_schema': {
            'type': 'object',
            'properties': {'topic': {'type': 'string', 'description': 'Guidance topic (e.g. "process validation", "ICH Q8")'}},
            'required': ['topic'],
        },
    },
    {
        'name': 'search_patents',
        'description': 'Search SureChEMBL for patents covering a drug by name or SMILES structure. Use when asked about patent landscape, freedom-to-operate, or patent expiry for a compound.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'query': {'type': 'string', 'description': 'Drug name or SMILES string to search patents for'},
                'mode': {'type': 'string', 'enum': ['name', 'smiles'], 'description': 'Whether to search by drug name or SMILES structure'},
            },
            'required': ['query', 'mode'],
        },
    },
    {
        'name': 'get_drug_profile',
        'description': 'Get the full profile of an existing approved drug by ChEMBL ID: molecular structure, mechanism of action, and approval status.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'chembl_id': {'type': 'string', 'description': 'ChEMBL ID of the drug, e.g. CHEMBL1431 for metformin'},
            },
            'required': ['chembl_id'],
        },
    },
    {
        'name': 'get_pdb_structure',
        'description': 'Retrieve protein structure data from RCSB PDB by PDB ID. Returns resolution, experimental method, organism, and bound ligands.',
        'input_schema': {
            'type': 'object',
            'properties': {'pdb_id': {'type': 'string', 'description': 'PDB ID (4-character code, e.g. "3ERT")'}},
            'required': ['pdb_id'],
        },
    },
    {
        'name': 'get_excipient_info',
        'description': 'Look up pharmaceutical excipient data including FDA IIG limits, incompatibilities, and GRAS status.',
        'input_schema': {
            'type': 'object',
            'properties': {'excipient_name': {'type': 'string', 'description': 'Excipient name (e.g. "microcrystalline cellulose", "povidone")'}},
            'required': ['excipient_name'],
        },
    },
    {
        'name': 'get_stability_guidelines',
        'description': 'Retrieve ICH Q1A(R2) stability testing conditions and acceptance criteria for a material type.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'material_type': {'type': 'string', 'enum': ['api', 'dp', 'intermediate'], 'description': 'Material type: api (drug substance), dp (drug product), or intermediate'},
            },
            'required': ['material_type'],
        },
    },
]


def _dispatch_tool(name: str, inputs: dict) -> dict:
    try:
        if name == 'search_pubchem':
            return {'results': pubchem.search_compound(inputs['name'])}
        elif name == 'search_chembl':
            molecules = chembl.search_molecule(inputs['name'])
            if molecules:
                chembl_id = molecules[0].get('molecule_chembl_id', '')
                mechanisms = chembl.get_mechanisms(chembl_id) if chembl_id else []
                return {'molecules': molecules[:3], 'mechanisms': mechanisms}
            return {'molecules': []}
        elif name == 'search_disease':
            return {'results': opentargets.search_disease(inputs['term'])}
        elif name == 'get_disease_targets':
            return opentargets.get_disease_targets(inputs['efo_id'])
        elif name == 'get_protein_detail':
            return uniprot.get_protein(inputs['uniprot_id'])
        elif name == 'predict_admet':
            return pkcsm.predict_admet(inputs['smiles'])
        elif name == 'get_safety_data':
            details = comptox.get_chemical_details(inputs['compound_name'])
            dtxsid = ''
            if isinstance(details, list) and details:
                dtxsid = details[0].get('dtxsid', '')
            hazard = comptox.get_hazard_data(dtxsid) if dtxsid else {}
            return {'details': details, 'hazard': hazard}
        elif name == 'search_fda_labels':
            return {'results': openfda.search_labels(generic_name=inputs['drug_name'])}
        elif name == 'get_drug_label':
            return {'results': dailymed.search_spls(inputs['drug_name'])}
        elif name == 'search_clinical_trials':
            return clinicaltrials.search_trials(
                condition=inputs.get('condition'),
                intervention=inputs.get('intervention'),
                phase=inputs.get('phase'),
            )
        elif name == 'search_pubmed':
            pmids = pubmed.search_articles(inputs['query'], inputs.get('max_results', 10))
            summaries = pubmed.get_summaries(pmids)
            return {'articles': summaries}
        elif name == 'plan_synthesis':
            return askcos.single_step_retro(inputs['smiles'])
        elif name == 'get_nist_spectrum':
            spectrum = nist.get_spectrum(inputs['cas'], inputs.get('spec_type', 'IR'))
            return {'jcamp': spectrum[:500] if spectrum else '', 'available': bool(spectrum)}
        elif name == 'search_fda_guidance':
            return {'results': openfda.search_guidance(inputs['topic'])}
        elif name == 'search_patents':
            if inputs.get('mode') == 'smiles':
                return {'results': surechembl.search_by_smiles(inputs['query'])}
            return {'results': surechembl.search_compound(inputs['query'])}
        elif name == 'get_drug_profile':
            mol = chembl.get_molecule(inputs['chembl_id'])
            mech = chembl.get_mechanisms(inputs['chembl_id'])
            return {'molecule': mol, 'mechanisms': mech}
        elif name == 'get_pdb_structure':
            return pdb.get_structure(inputs['pdb_id'])
        elif name == 'get_excipient_info':
            from core.models import Excipient
            try:
                exc = Excipient.objects.get(name__iexact=inputs['excipient_name'])
                return {
                    'name': exc.name, 'iig_limit': exc.iig_limit, 'iig_unit': exc.iig_unit,
                    'function': exc.function, 'route': exc.route, 'gras_status': exc.gras_status,
                    'incompatibilities': exc.incompatibilities,
                }
            except Excipient.DoesNotExist:
                return {'error': f'Excipient not found: {inputs["excipient_name"]}'}
        elif name == 'get_stability_guidelines':
            guidelines = {
                'api': {
                    'long_term': {'condition': '25°C/60% RH', 'duration': '12 months minimum', 'reference': 'ICH Q1A(R2)'},
                    'accelerated': {'condition': '40°C/75% RH', 'duration': '6 months', 'reference': 'ICH Q1A(R2)'},
                    'attributes': ['appearance', 'assay', 'related substances', 'water content', 'microbial limits'],
                },
                'dp': {
                    'long_term': {'condition': '25°C/60% RH or 30°C/65% RH', 'duration': '12 months minimum', 'reference': 'ICH Q1A(R2)'},
                    'accelerated': {'condition': '40°C/75% RH', 'duration': '6 months', 'reference': 'ICH Q1A(R2)'},
                    'attributes': ['appearance', 'assay', 'degradation products', 'dissolution', 'hardness', 'water activity'],
                },
                'intermediate': {
                    'long_term': {'condition': '25°C/60% RH', 'duration': 'processing time + margin', 'reference': 'ICH Q1A(R2)'},
                    'attributes': ['appearance', 'assay', 'microbial limits'],
                },
            }
            return guidelines.get(inputs['material_type'], {'error': 'Unknown material type'})
        else:
            return {'error': f'Unknown tool: {name}'}
    except Exception as e:
        return {'error': str(e)}


def build_project_context(project_id: int) -> str:
    try:
        from core.models import Project
        project = Project.objects.prefetch_related('compounds', 'experiments').get(pk=project_id)
        compounds = project.compounds.all()
        experiments = project.experiments.order_by('-created_at')[:5]

        lines = [
            f'PROJECT: {project.name}',
            f'Phase: {project.get_phase_display()} | Status: {project.get_status_display()}',
        ]
        if project.description:
            lines.append(f'Description: {project.description}')
        if compounds:
            c = compounds[0]
            lines.append(f'\nCOMPOUND: {c.name}')
            if c.smiles:
                lines.append(f'SMILES: {c.smiles}')
            if c.molecular_weight:
                lines.append(f'MW: {c.molecular_weight} Da')
            if c.chembl_id:
                lines.append(f'ChEMBL ID: {c.chembl_id}')
        if experiments:
            lines.append('\nRECENT EXPERIMENTS:')
            for e in experiments:
                lines.append(f'- [{e.experiment_type}] {e.title} ({e.get_status_display()})')
        return '\n'.join(lines)
    except Exception:
        return ''


def stream_chat(messages: list, project_context: str = ''):
    provider, model, api_key, custom_endpoint = get_active_llm_config()

    system = SYSTEM_PROMPT
    if project_context:
        system += f'\n\n--- CURRENT PROJECT CONTEXT ---\n{project_context}'

    if provider != 'claude':
        base_url = MISTRAL_BASE_URL if provider == 'mistral' else custom_endpoint
        yield from _stream_openai_text(system, list(messages), model, api_key, base_url)
        return

    client = anthropic.Anthropic(api_key=api_key)
    api_messages = list(messages)
    sources = []

    while True:
        with client.messages.stream(
            model=model,
            max_tokens=4096,
            system=system,
            messages=api_messages,
            tools=TOOL_DEFINITIONS,
        ) as stream:
            tool_use_blocks = []
            current_text = ''

            for event in stream:
                if hasattr(event, 'type'):
                    if event.type == 'content_block_delta':
                        if hasattr(event.delta, 'text'):
                            current_text += event.delta.text
                            yield f'data: {json.dumps({"type": "text_delta", "text": event.delta.text})}\n\n'
                    elif event.type == 'content_block_start':
                        if hasattr(event.content_block, 'type') and event.content_block.type == 'tool_use':
                            tool_use_blocks.append({
                                'id': event.content_block.id,
                                'name': event.content_block.name,
                                'input': {},
                            })
                    elif event.type == 'content_block_stop':
                        pass

            final_message = stream.get_final_message()

        if final_message.stop_reason == 'end_turn':
            if sources:
                yield f'data: {json.dumps({"type": "sources", "sources": sources})}\n\n'
            yield f'data: {json.dumps({"type": "message_stop"})}\n\n'
            break

        if final_message.stop_reason == 'tool_use':
            tool_use_content = [b for b in final_message.content if b.type == 'tool_use']
            api_messages.append({'role': 'assistant', 'content': final_message.content})

            tool_results = []
            for tool_block in tool_use_content:
                tool_name = tool_block.name
                tool_input = tool_block.input

                yield f'data: {json.dumps({"type": "tool_use", "name": tool_name, "input": tool_input})}\n\n'

                result = _dispatch_tool(tool_name, tool_input)
                sources.append({'api': tool_name, 'query': tool_input})

                yield f'data: {json.dumps({"type": "tool_result", "name": tool_name, "result": result})}\n\n'

                tool_results.append({
                    'type': 'tool_result',
                    'tool_use_id': tool_block.id,
                    'content': json.dumps(result),
                })

            api_messages.append({'role': 'user', 'content': tool_results})
        else:
            yield f'data: {json.dumps({"type": "message_stop"})}\n\n'
            break


def generate_once(system: str, user_content: str) -> str:
    """Blocking (non-streaming) single-turn generation. Returns the full response text."""
    provider, model, api_key, _ = get_active_llm_config()
    if provider != 'claude':
        from openai import OpenAI
        from openai import OpenAI as _OAI
        kwargs = {'api_key': api_key}
        if provider == 'mistral':
            kwargs['base_url'] = MISTRAL_BASE_URL
        client = _OAI(**kwargs)
        resp = client.chat.completions.create(
            model=model,
            messages=[{'role': 'system', 'content': system}, {'role': 'user', 'content': user_content}],
            max_tokens=4096,
        )
        return resp.choices[0].message.content or ''
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system,
        messages=[{'role': 'user', 'content': user_content}],
    )
    return response.content[0].text if response.content else ''


# ─── v3: Plan system prompts ─────────────────────────────────────────────────

PLAN_SYSTEM_PROMPT = """You are the BioIntel AI Plan Advisor, an expert pharmaceutical scientist and \
regulatory strategist embedded in BioIntel's AI-Driven project mode.

Your role is to co-author and guide the drug development plan for the project, grounded in \
peer-reviewed methodology and ICH guidelines. You operate step-by-step with scientist approval \
at every gate.

## Scientific grounding
Every recommendation must cite at least one source using this format: [Source: ICH Q6A, Section 4.1]
Key references you must apply:
- **ICH Q1A(R2)**: Stability testing conditions and timepoints (25°C/60% RH long-term; 40°C/75% RH accelerated)
- **ICH Q2(R1)**: Analytical method validation parameters (accuracy, precision, specificity, LOD, LOQ, linearity, range, robustness)
- **ICH Q6A**: Drug substance and drug product specifications (identification, assay, purity, dissolution)
- **ICH Q8(R2)**: Pharmaceutical development (design space, QbD approach, critical quality attributes)
- **ICH Q9(R1)**: Quality risk management (FMEA, risk ranking, control strategy)
- **ICH Q11**: Drug substance development and manufacture (process understanding, design space)
- **ICH M3(R2)**: Non-clinical safety studies for IND (study duration, species selection, GLP)
- **ICH S7A/S7B**: Safety pharmacology studies and hERG assays
- **ICH S2(R1)**: Genotoxicity testing battery
- **Lipinski et al. 1997** (Rule of Five): MW ≤500, LogP ≤5, HBD ≤5, HBA ≤10 for oral absorption
- **Wager et al. 2010** (CNS MPO score): 6 properties scored 0-1, CNS MPO ≥4 preferred for CNS drugs
- **Gleeson 2008**: ADMET flags — LogP >4 raises metabolic risk; TPSA >140 reduces absorption
- **Leeson & Springthorpe 2007**: Drug-likeness beyond Rule of Five

## Boundaries
- You **recommend**; scientists **decide**. Never say "you must" or "this is required" — say "I recommend" or "based on ICH guidance, consider"
- Never claim a compound will succeed clinically — probability statements only
- Distinguish your AI reasoning from established regulatory guidance
- When a scientist rejects your recommendation, incorporate their feedback and revise without arguing

## RAG citations
When context includes retrieved pharmaceutical references (marked ## Relevant Pharmaceutical References), \
cite the specific document and section in your response. These are authoritative sources — prioritize them \
over your general training knowledge.

## Plan step format
For each plan step recommendation, structure your response as:
1. **Summary** (2-3 sentences): What this step achieves and why it matters at this stage
2. **Key activities**: Bulleted list of concrete scientific actions
3. **Decision criteria**: Measurable go/no-go thresholds (cite ICH guideline if applicable)
4. **Risk flags**: What could derail this step and mitigation strategies
5. **Sources**: All citations in [Source: ...] format

## Suggested actions (REQUIRED)
After every recommendation, you MUST include a `suggested_actions` list in the `update_plan_step` call. \
These are concrete one-click data changes the scientist can apply to BioIntel — \
turn your recommendations into real project data. Examples:
- If you recommend ML335 as a reference compound → action_type: add_drug_investigation, data: {name, smiles, disease_name, notes}
- If you suggest an analog candidate → action_type: add_analog_candidate, data: {smiles, similarity_score, patent_status, notes}
- If you define SAR objectives → action_type: add_sar_entry, data: {r_group, activity_type, notes}
- If you specify an analytical method → action_type: add_analytical_method, data: {method_name, method_type, analyte}
- If you design a preclinical study → action_type: add_preclinical_study, data: {study_type, species, dose_route}
- If you define a formulation → action_type: add_formulation_plan, data: {dosage_form, route_of_administration, rationale}
- If you design a stability plan → action_type: add_stability_plan, data: {material_type, intended_storage_condition}
Always include 1-4 specific, immediately actionable suggestions grounded in your recommendation."""

BIOLOGIC_PLAN_SYSTEM_PROMPT = """You are the BioIntel AI Plan Advisor, an expert in biopharmaceutical \
development and regulatory strategy for biologics (monoclonal antibodies, fusion proteins, ADCs, nanobodies, \
gene therapy vectors).

Your role is to co-author and guide the biologics development plan for the project, grounded in \
peer-reviewed methodology and ICH biologics guidelines.

## Scientific grounding
Every recommendation must cite at least one source using this format: [Source: ICH Q5C, Section 2]
Key references you must apply:
- **ICH Q5A(R2)**: Viral safety evaluation of biotechnology products
- **ICH Q5C**: Stability testing of biotechnological/biological products (real-time and accelerated)
- **ICH Q5E**: Comparability of biotechnological products (post-change characterization)
- **ICH Q6B**: Specifications for biotechnological products (identity, purity, potency)
- **ICH S6(R1)**: Preclinical safety evaluation for biotechnology-derived pharmaceuticals (species selection, dose selection, immunogenicity)
- **ICH Q8(R2)**: Pharmaceutical development principles (applicable to biologics formulation)
- **Carter 2006** (Nat. Rev. Immunol.): Antibody therapeutics design principles — Fc engineering, effector functions
- **Jarasch et al. 2015** (J. Pharm. Sci.): Developability assessment — aggregation, pI, hydrophobicity, viscosity
- **Jain et al. 2017** (PNAS): Biophysical properties predicting clinical success — PSH, PPC, CamSol scores

## Boundaries
- You **recommend**; scientists **decide**. Never say "you must" — say "I recommend" or "per ICH S6(R1), consider"
- For immunogenicity risk, always note species relevance and flag non-human relevant sequences
- Distinguish in-silico developability prediction from experimental data

## Biologics-specific considerations
- For mAbs: always assess Fc region engineering, effector function requirements, and deimmunization
- For expression systems: CHO preferred for complex glycosylation; note glycosylation site analysis
- For upstream: always flag CPPs (pH, DO, temperature, agitation) and link to CQAs
- For purification: Protein A capture is standard for IgG; always include viral clearance in the train
- For formulation: polysorbate 80 or 20 at 0.01-0.05%; sucrose/trehalose as stabilizers; note oxidation risk

## Suggested actions (REQUIRED)
After every recommendation, you MUST include a `suggested_actions` list in the `update_plan_step` call. \
These are concrete one-click data changes the scientist can apply to BioIntel — \
turn your recommendations into real project data. Examples:
- If you recommend a reference biologic → action_type: add_drug_investigation, data: {name, smiles, disease_name, notes}
- If you specify an analytical method → action_type: add_analytical_method, data: {method_name, method_type, analyte}
- If you design a preclinical study → action_type: add_preclinical_study, data: {study_type, species, dose_route}
- If you define a formulation → action_type: add_formulation_plan, data: {dosage_form, route_of_administration, rationale}
- If you design a stability plan → action_type: add_stability_plan, data: {material_type, intended_storage_condition}
Always include 1-4 specific, immediately actionable suggestions grounded in your recommendation.

## Plan step format
For each plan step recommendation, structure your response as:
1. **Summary** (2-3 sentences): What this step achieves and why it matters for biologics development
2. **Key activities**: Bulleted list of concrete scientific actions
3. **Decision criteria**: Measurable go/no-go thresholds (cite ICH guideline if applicable)
4. **Risk flags**: Biologics-specific risks (immunogenicity, aggregation, manufacturing scalability)
5. **Sources**: All citations in [Source: ...] format"""

PLAN_STEP_TOOLS = [
    {
        'name': 'create_analog_candidate',
        'description': 'Create a new analog candidate in the BioIntel database for this project.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'project_id': {'type': 'integer'},
                'smiles': {'type': 'string', 'description': 'SMILES string of the candidate'},
                'similarity_score': {'type': 'number', 'description': 'Tanimoto similarity to reference (0-1)'},
                'patent_status': {'type': 'string', 'enum': ['free', 'covered', 'unknown']},
                'notes': {'type': 'string'},
            },
            'required': ['project_id', 'smiles'],
        },
    },
    {
        'name': 'create_synthesis_plan',
        'description': 'Create a synthesis plan entry and optionally trigger ASKCOS retrosynthesis.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'project_id': {'type': 'integer'},
                'target_smiles': {'type': 'string'},
                'plan_type': {'type': 'string', 'enum': ['retro', 'tree'], 'default': 'retro'},
            },
            'required': ['project_id', 'target_smiles'],
        },
    },
    {
        'name': 'update_plan_step',
        'description': 'Store the structured recommendation and suggested actions for the current plan step.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'step_id': {'type': 'integer'},
                'recommendation': {'type': 'object', 'description': 'Structured recommendation JSON'},
                'entities_created': {
                    'type': 'array',
                    'items': {'type': 'object'},
                    'description': 'List of {type, id} for entities created in this step',
                },
                'rag_sources': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'List of source citation strings',
                },
                'suggested_actions': {
                    'type': 'array',
                    'description': 'List of concrete data changes to suggest to the scientist as one-click actions',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string', 'description': 'Unique slug for this action, e.g. add_ml335_investigation'},
                            'label': {'type': 'string', 'description': 'Human-readable button label, e.g. "Add ML335 as reference drug"'},
                            'action_type': {
                                'type': 'string',
                                'enum': [
                                    'add_drug_investigation',
                                    'add_analog_candidate',
                                    'add_sar_entry',
                                    'add_analytical_method',
                                    'add_preclinical_study',
                                    'add_formulation_plan',
                                    'add_stability_plan',
                                    'update_project_description',
                                ],
                            },
                            'data': {'type': 'object', 'description': 'Field values for the entity to create/update'},
                        },
                        'required': ['id', 'label', 'action_type', 'data'],
                    },
                },
            },
            'required': ['step_id', 'recommendation'],
        },
    },
    {
        'name': 'mark_step_complete',
        'description': 'Mark a plan step as completed and record a summary.',
        'input_schema': {
            'type': 'object',
            'properties': {
                'step_id': {'type': 'integer'},
                'summary': {'type': 'string', 'description': 'One-paragraph summary of what was accomplished'},
            },
            'required': ['step_id', 'summary'],
        },
    },
]

ALL_PLAN_TOOLS = TOOL_DEFINITIONS + PLAN_STEP_TOOLS


def _dispatch_plan_tool(name: str, inputs: dict) -> dict:
    """Dispatch the 4 plan-write tools. Falls back to existing tools for data lookups."""
    if name == 'create_analog_candidate':
        from core.models import AnalogCandidate, DrugInvestigation
        investigation = DrugInvestigation.objects.filter(project_id=inputs['project_id']).first()
        if not investigation:
            return {'error': 'No drug investigation found for this project'}
        candidate = AnalogCandidate.objects.create(
            investigation=investigation,
            project_id=inputs['project_id'],
            smiles=inputs['smiles'],
            similarity_score=inputs.get('similarity_score', 0.0),
            patent_status=inputs.get('patent_status', 'unknown'),
            notes=inputs.get('notes', ''),
        )
        return {'id': candidate.id, 'smiles': candidate.smiles}

    elif name == 'create_synthesis_plan':
        from core.models import SynthesisPlan
        plan = SynthesisPlan.objects.create(
            project_id=inputs['project_id'],
            target_smiles=inputs['target_smiles'],
            plan_type=inputs.get('plan_type', 'retro'),
        )
        return {'id': plan.id, 'target_smiles': plan.target_smiles}

    elif name == 'update_plan_step':
        from core.models import AIPlanStep
        try:
            step = AIPlanStep.objects.get(id=inputs['step_id'])
        except AIPlanStep.DoesNotExist:
            return {'error': f"step_id {inputs['step_id']} not found — use the exact step_id provided in the prompt"}
        step.ai_recommendation = inputs.get('recommendation', {})
        step.entities_created = inputs.get('entities_created', [])
        step.rag_sources = inputs.get('rag_sources', [])
        step.suggested_actions = inputs.get('suggested_actions', [])
        step.status = 'awaiting_approval'
        step.save(update_fields=['ai_recommendation', 'entities_created', 'rag_sources', 'suggested_actions', 'status', 'updated_at'])
        return {'step_id': step.id, 'status': step.status}

    elif name == 'mark_step_complete':
        from core.models import AIPlanStep
        try:
            step = AIPlanStep.objects.get(id=inputs['step_id'])
        except AIPlanStep.DoesNotExist:
            return {'error': f"step_id {inputs['step_id']} not found"}
        step.ai_reasoning = inputs.get('summary', '')
        step.status = 'awaiting_approval'
        step.save(update_fields=['ai_reasoning', 'status', 'updated_at'])
        return {'step_id': step.id, 'status': step.status}

    else:
        return _dispatch_tool(name, inputs)


def _get_plan_system_prompt(molecule_type: str) -> str:
    return BIOLOGIC_PLAN_SYSTEM_PROMPT if molecule_type == 'biologic' else PLAN_SYSTEM_PROMPT


def _stream_with_tools(system: str, messages: list, tools: list, rag_context: str = ''):
    """Core streaming loop shared by all plan/panel streaming functions."""
    provider, model, api_key, custom_endpoint = get_active_llm_config()

    if rag_context:
        system = system + '\n\n' + rag_context

    if provider != 'claude':
        base_url = MISTRAL_BASE_URL if provider == 'mistral' else custom_endpoint
        yield from _stream_openai_text(system, list(messages), model, api_key, base_url)
        return

    client = anthropic.Anthropic(api_key=api_key)

    api_messages = list(messages)
    sources = []

    while True:
        with client.messages.stream(
            model=model,
            max_tokens=8192,
            system=system,
            messages=api_messages,
            tools=tools,
        ) as stream:
            tool_use_blocks = []

            for event in stream:
                if hasattr(event, 'type'):
                    if event.type == 'content_block_delta':
                        if hasattr(event.delta, 'text'):
                            yield f'data: {json.dumps({"type": "text_delta", "text": event.delta.text})}\n\n'
                        elif hasattr(event.delta, 'partial_json'):
                            if tool_use_blocks:
                                current_input_str = tool_use_blocks[-1].get('_input_str', '')
                                tool_use_blocks[-1]['_input_str'] = current_input_str + event.delta.partial_json
                    elif event.type == 'content_block_start':
                        if hasattr(event.content_block, 'type') and event.content_block.type == 'tool_use':
                            tool_use_blocks.append({
                                'id': event.content_block.id,
                                'name': event.content_block.name,
                                'input': {},
                                '_input_str': '',
                            })

            final_message = stream.get_final_message()

        if final_message.stop_reason == 'end_turn':
            if sources:
                yield f'data: {json.dumps({"type": "sources", "sources": sources})}\n\n'
            yield f'data: {json.dumps({"type": "message_stop"})}\n\n'
            break

        if final_message.stop_reason == 'tool_use':
            tool_use_content = [b for b in final_message.content if b.type == 'tool_use']
            api_messages.append({'role': 'assistant', 'content': final_message.content})

            tool_results = []
            for tool_block in tool_use_content:
                tool_name = tool_block.name
                tool_input = tool_block.input

                yield f'data: {json.dumps({"type": "tool_use", "name": tool_name, "input": tool_input})}\n\n'
                result = _dispatch_plan_tool(tool_name, tool_input)
                sources.append({'api': tool_name, 'query': tool_input})

                yield f'data: {json.dumps({"type": "tool_result", "name": tool_name, "result": result})}\n\n'
                tool_results.append({
                    'type': 'tool_result',
                    'tool_use_id': tool_block.id,
                    'content': json.dumps(result),
                })

            api_messages.append({'role': 'user', 'content': tool_results})
        else:
            yield f'data: {json.dumps({"type": "message_stop"})}\n\n'
            break


def stream_plan_generation(project_id: int, plan_id: int):
    """Regenerate the full plan from scratch.

    Deletes all existing steps, recreates blank templates, then generates a
    recommendation for each step sequentially. Emits a plan_step progress event
    before each step so the frontend can show "Generating step X of Y".
    """
    from core.models import AIPlan, AIPlanStep
    from core.services.ai_plan import create_plan_steps

    plan = AIPlan.objects.select_related('project').get(id=plan_id)

    # Wipe all existing steps and start fresh from the step template
    AIPlanStep.objects.filter(plan=plan).delete()
    steps = create_plan_steps(plan_id, plan.molecule_type)

    plan.step_count = len(steps)
    plan.current_step_number = None
    plan.status = 'active'
    plan.save(update_fields=['step_count', 'current_step_number', 'status', 'updated_at'])

    # Tell the frontend to replace its local steps with the new blank set
    steps_payload = [
        {'id': s.id, 'step_number': s.step_number, 'phase': s.phase,
         'title': s.title, 'status': s.status, 'ai_reasoning': '',
         'ai_recommendation': {}, 'rag_sources': [], 'description': s.description or ''}
        for s in steps
    ]
    yield f'data: {json.dumps({"type": "steps_reset", "steps": steps_payload, "total": len(steps)})}\n\n'
    yield f'data: {json.dumps({"type": "plan_complete"})}\n\n'


def stream_step_recommendation(plan_id: int, step_id: int):
    """Generate or regenerate a detailed recommendation for a single plan step."""
    from core.models import AIPlan, AIPlanStep
    from core.services.rag import retrieve, format_rag_context
    from core.services.ai_plan import build_plan_messages
    from core.services.project_context import build_project_context

    plan = AIPlan.objects.select_related('project').get(id=plan_id)
    step = AIPlanStep.objects.get(id=step_id)

    rag_chunks = retrieve(
        query=f"{step.title} {step.description}",
        phase=step.phase,
        molecule_type=plan.molecule_type,
        project_id=plan.project_id,
    )
    rag_context = format_rag_context(rag_chunks)
    if rag_chunks:
        yield f'data: {json.dumps({"type": "rag_citation", "chunks": rag_chunks})}\n\n'

    feedback_note = ''
    if step.scientist_feedback and step.status == 'revision_needed':
        feedback_note = f"\n\nScientist revision request: {step.scientist_feedback}"

    project_context = build_project_context(plan.project_id)

    messages = build_plan_messages(plan_id, step_id=step_id)
    if not messages:
        messages = []

    user_content = (
        f"Please provide a detailed recommendation for plan step {step.step_number} "
        f"(step_id={step.id}): **{step.title}** (Phase: {step.phase})\n"
        f"Step description: {step.description or 'N/A'}{feedback_note}\n\n"
    )
    if project_context:
        user_content += f"{project_context}\n\n"
    user_content += (
        "Write your recommendation now using your pharmaceutical expertise and the project data above. "
        "Do NOT call any external search tools — write directly from your knowledge and the data provided. "
        "Reference specific values from the project data (SMILES, assay results, formulation components, etc.) "
        "rather than generic placeholders. If critical data for this step is missing, "
        "identify it explicitly so the scientist knows what to enter first.\n\n"
        f"Once your recommendation text is complete, call update_plan_step with step_id={step.id} to save it."
    )

    messages.append({'role': 'user', 'content': user_content})

    system = _get_plan_system_prompt(plan.molecule_type)

    # Collect text_delta chunks to persist as ai_reasoning in the DB
    collected_text: list[str] = []
    for chunk in _stream_with_tools(system, messages, PLAN_STEP_TOOLS, rag_context):
        if chunk.startswith('data: '):
            try:
                evt = json.loads(chunk[6:].strip())
                if evt.get('type') == 'text_delta':
                    collected_text.append(evt.get('text', ''))
            except (json.JSONDecodeError, ValueError):
                pass
        yield chunk

    # Save streaming narrative as ai_reasoning so it persists on the server
    ai_reasoning = ''.join(collected_text)
    step.refresh_from_db()
    if ai_reasoning and not step.ai_reasoning:
        step.ai_reasoning = ai_reasoning
        step.save(update_fields=['ai_reasoning', 'updated_at'])

    yield f'data: {json.dumps({"type": "step_complete", "step_id": step_id, "status": step.status})}\n\n'


def stream_step_discussion(plan_id: int, step_id: int, message: str):
    """Per-step discussion thread — scientist asks a question or provides feedback."""
    from core.models import AIPlan, AIPlanStep
    from core.services.rag import retrieve, format_rag_context
    from core.services.ai_plan import build_plan_messages, save_discussion_message

    plan = AIPlan.objects.select_related('project').get(id=plan_id)
    step = AIPlanStep.objects.get(id=step_id)

    save_discussion_message(plan_id, step_id, 'scientist', message)

    rag_chunks = retrieve(
        query=message,
        phase=step.phase,
        molecule_type=plan.molecule_type,
        project_id=plan.project_id,
    )
    rag_context = format_rag_context(rag_chunks)
    if rag_chunks:
        yield f'data: {json.dumps({"type": "rag_citation", "chunks": rag_chunks})}\n\n'

    messages = build_plan_messages(plan_id, step_id=step_id, new_message=message)
    system = _get_plan_system_prompt(plan.molecule_type)

    full_response = []
    for chunk in _stream_with_tools(system, messages, ALL_PLAN_TOOLS, rag_context):
        yield chunk
        try:
            data = json.loads(chunk.replace('data: ', '', 1).strip())
            if data.get('type') == 'text_delta':
                full_response.append(data.get('text', ''))
        except Exception:
            pass

    response_text = ''.join(full_response)
    if response_text:
        save_discussion_message(
            plan_id, step_id, 'ai', response_text,
            sources=[c['document'] for c in rag_chunks],
        )


def stream_result_analysis(plan_id: int, step_id: int, experiment_results: dict):
    """Post-experiment AI analysis. Compares results to plan recommendation and proposes next action."""
    from core.models import AIPlan, AIPlanStep
    from core.services.rag import retrieve, format_rag_context
    from core.services.ai_plan import build_plan_messages, save_discussion_message

    plan = AIPlan.objects.select_related('project').get(id=plan_id)
    step = AIPlanStep.objects.get(id=step_id)

    rag_chunks = retrieve(
        query=f"analysis {step.title} experiment results",
        phase=step.phase,
        molecule_type=plan.molecule_type,
        project_id=plan.project_id,
    )
    rag_context = format_rag_context(rag_chunks)
    if rag_chunks:
        yield f'data: {json.dumps({"type": "rag_citation", "chunks": rag_chunks})}\n\n'

    messages = build_plan_messages(plan_id, step_id=step_id)
    messages.append({
        'role': 'user',
        'content': (
            f"Experiment results are now available for step {step.step_number}: {step.title}\n\n"
            f"Original recommendation summary:\n{json.dumps(step.ai_recommendation, indent=2)}\n\n"
            f"Experiment results:\n{json.dumps(experiment_results, indent=2)}\n\n"
            "Please analyze whether these results meet the decision criteria in the plan. "
            "End your response with one of:\n"
            "<action>proceed</action> — results acceptable, move to next step\n"
            "<action>revise</action> — results need further work at this step\n"
            "<action>go_back_to_step:N</action> — results indicate we must revisit step N"
        ),
    })

    system = _get_plan_system_prompt(plan.molecule_type)
    full_response = []
    for chunk in _stream_with_tools(system, messages, ALL_PLAN_TOOLS, rag_context):
        yield chunk
        try:
            data = json.loads(chunk.replace('data: ', '', 1).strip())
            if data.get('type') == 'text_delta':
                full_response.append(data.get('text', ''))
        except Exception:
            pass

    response_text = ''.join(full_response)
    if response_text:
        save_discussion_message(plan_id, step_id, 'ai', response_text)

    import re
    action_match = re.search(r'<action>(.*?)</action>', response_text)
    if action_match:
        action = action_match.group(1).strip()
        yield f'data: {json.dumps({"type": "result_action", "action": action})}\n\n'


PAGE_CONTEXTS = {
    'ProjectEdit': {
        'label': 'Project Overview',
        'guidance': (
            'Help the scientist define their project scope, therapeutic rationale, development pathway, and Target Product Profile (TPP). '
            'The TPP fields (tpp_*) define the intended clinical product: indication, patient population, dosage form, dose, '
            'frequency, comparator, efficacy/safety endpoints, target claims, special populations, and contraindications. '
            'Use competitive landscape data, disease biology, and regulatory precedent to recommend TPP values.'
        ),
        'fields': [
            # Project-level fields
            ('description', 'Project Description', 'Text summarising goals and rationale'),
            ('pathway', 'Development Pathway', 'analog_based or novel_design'),
            ('phase', 'Development Phase', 'preclinical / phase1 / phase2 / phase3'),
            ('molecule_type', 'Molecule Type', 'small_molecule / biologic / undetermined'),
            # Target Product Profile (TPP) fields
            ('tpp_indication', 'TPP — Target Indication', 'e.g., Type 2 diabetes mellitus, influenza A and B treatment'),
            ('tpp_patient_population', 'TPP — Patient Population', 'e.g., Adults ≥18 with HbA1c 7.5–10%; all ages ≥1 year'),
            ('tpp_route', 'TPP — Route of Administration', 'e.g., Oral, IV, SC, Inhaled'),
            ('tpp_dosage_form', 'TPP — Dosage Form', 'e.g., Tablet, Capsule, Solution, Lyophilizate'),
            ('tpp_dose', 'TPP — Target Dose', 'e.g., 100 mg once daily; single 40 mg dose'),
            ('tpp_frequency', 'TPP — Dosing Frequency', 'e.g., Once daily (QD), Single dose, Twice daily (BID)'),
            ('tpp_comparator', 'TPP — Comparator / Standard of Care', 'e.g., Oseltamivir 75 mg BID × 5 days; metformin 1000 mg BID'),
            ('tpp_primary_efficacy', 'TPP — Primary Efficacy Endpoint', 'e.g., Time to alleviation of illness ≤65h; HbA1c reduction ≥1%'),
            ('tpp_primary_safety', 'TPP — Primary Safety Target', 'e.g., No psychiatric AEs; hERG IC50 > 30× Cmax; AMES negative'),
            ('tpp_target_claims', 'TPP — Target Label Claims', 'e.g., Active against oseltamivir-resistant strains; QD dosing'),
            ('tpp_special_populations', 'TPP — Special Populations', 'e.g., Pediatric ≥1 year; renally impaired; pregnancy category'),
            ('tpp_contraindications', 'TPP — Contraindications', 'e.g., Severe hepatic impairment; known hypersensitivity'),
        ],
    },
    'SARTracker': {
        'label': 'SAR Tracker',
        'guidance': 'Apply Lipinski Rule-of-Five, Wager CNS MPO, and Gleeson ADMET rules. Ground SAR recommendations in published lead optimisation methodology.',
        'fields': [
            ('activity_type', 'Activity Type', 'e.g., IC50, Ki, EC50'),
            ('activity_unit', 'Activity Unit', 'e.g., nM, µM'),
            ('assay_description', 'Assay Description', 'How the activity is measured'),
            ('r_group', 'R-Group Annotation', 'Structural position being modified, e.g., 4-fluoro benzyl at C3'),
            ('notes', 'SAR Notes / Optimisation Goals', 'Structural trends, next steps, and property targets'),
        ],
    },
    'SynthesisHub': {
        'label': 'Synthesis Hub',
        'guidance': 'Recommend ICH Q11-aligned route selection criteria. Consider step count, solvent class (ICH Q3C), atom economy, and safety.',
        'fields': [
            ('plan_type', 'Route Strategy', 'e.g., linear, convergent, retrosynthetic'),
            ('notes', 'Synthesis Notes', 'Key considerations, hazards, scale-up flags'),
        ],
    },
    'SaltPolymorphScreening': {
        'label': 'Salt & Polymorph Screening',
        'guidance': 'Guide solid form selection to optimise solubility, stability, and processability. Reference ICH Q6A and Q11 principles.',
        'fields': [
            ('screen_type', 'Screen Type', 'salt / polymorph / cocrystal'),
            ('objective', 'Screening Objective', 'What property improvement is targeted'),
            ('baseline_pka', 'API pKa', 'Numeric value'),
            ('baseline_logp', 'API LogP', 'Numeric value'),
            ('baseline_solubility_mgml', 'Baseline Solubility mg/mL', 'Numeric value'),
            ('baseline_hygroscopicity', 'Hygroscopicity Observation', 'Qualitative or DVS result'),
            ('baseline_melting_point_c', 'Melting Point °C', 'Numeric value'),
        ],
    },
    'ProcessDevelopment': {
        'label': 'Process Development',
        'guidance': 'Apply ICH Q8 design space and Q11 development principles. Identify CPPs and CQAs systematically.',
        'fields': [
            ('cppNotes', 'Critical Process Parameters', 'Free-text description of CPPs and their ranges'),
            ('yield_target', 'Target Yield %', 'Numeric percentage'),
            ('purity_target', 'Purity Target %', 'Numeric percentage'),
        ],
    },
    'FormulationPlanning': {
        'label': 'Formulation Planning',
        'guidance': (
            'Apply ICH Q8(R2) quality-by-design principles. Consider BCS classification, dose, route, patient population, '
            'and stability when recommending dosage form and excipients.'
        ),
        'fields': [
            ('dosage_form', 'Dosage Form', 'e.g., oral_tablet, capsule, iv_solution, topical_cream'),
            ('route_of_administration', 'Route of Administration', 'e.g., oral, intravenous, subcutaneous, topical'),
            ('target_dose_mg', 'Target Dose mg', 'Numeric value'),
            ('release_type', 'Release Profile', 'immediate_release / modified_release / extended_release / delayed_release'),
            ('manufacturing_process', 'Manufacturing Process', 'e.g., wet_granulation, direct_compression, hot_melt_extrusion'),
            ('rationale', 'Formulation Rationale', 'Scientific justification for choices made'),
        ],
    },
    'StabilityPlanning': {
        'label': 'Stability Planning',
        'guidance': (
            'Design stability programmes per ICH Q1A(R2) for drug substance and drug product. '
            'Recommend appropriate storage conditions, time points, and container closure systems.'
        ),
        'fields': [
            ('material_type', 'Material Type', 'drug_substance or drug_product'),
            ('intended_storage_condition', 'Intended Storage Condition', 'e.g., 25°C/60%RH, 2–8°C, -20°C'),
            ('condition_label', 'Study Condition Label', 'e.g., Long-Term, Accelerated, Intermediate'),
            ('temperature_c', 'Temperature °C', 'Numeric value'),
            ('humidity_rh', 'Humidity %RH', 'Numeric value'),
            ('light_exposure', 'Light Exposure Condition', 'e.g., Protected from light / ICH Q1B / Dark'),
            ('ich_category', 'ICH Climatic Zone / Category', 'e.g., Zone IVb, Accelerated'),
            ('timepoints_months', 'Time Points months', 'Comma-separated e.g. 0,3,6,9,12,18,24'),
        ],
    },
    'AnalyticalMethod': {
        'label': 'Analytical Methods',
        'guidance': 'Recommend methods per ICH Q2(R1) validation requirements. Align method type with analyte and intended purpose (identity, assay, impurities).',
        'fields': [
            ('method_name', 'Method Name', 'Descriptive name for the method'),
            ('method_type', 'Method Type', 'e.g., hplc_uv, lc_ms, gc, nmr, dissolution, karl_fischer'),
            ('analyte', 'Analyte', 'What is being measured'),
            ('instrument', 'Instrument / Platform', 'e.g., HPLC, GC-MS, NMR spectrometer'),
            ('principle', 'Method Principle', 'Brief description of how it works'),
            ('validation_status', 'Validation Status', 'development / validated / compendial'),
        ],
    },
    'SpecificationBuilder': {
        'label': 'Specifications',
        'guidance': 'Set specifications per ICH Q6A (small molecule) or Q6B (biologic). Acceptance criteria must be justified by safety, efficacy, and manufacturing capability.',
        'fields': [
            ('spec_type', 'Spec Type', 'drug_substance or drug_product'),
            ('attribute', 'Attribute Name', 'e.g., Appearance, Assay, Related Substances, Dissolution, Water Content'),
            ('criteria_type', 'Criteria Type', 'release or shelf_life'),
            ('acceptance_criteria', 'Acceptance Criteria', 'e.g., 98.0–102.0% label claim, NMT 0.15%'),
            ('test_method', 'Test Method', 'e.g., HPLC-UV per validated method, USP <711>'),
            ('basis', 'Specification Basis', 'e.g., ICH Q6A limit, clinical batch data, pharmacopoeia'),
        ],
    },
    'ADMETDashboard': {
        'label': 'ADMET Dashboard',
        'guidance': 'Apply Lipinski Rule-of-Five, Wager CNS MPO, Gleeson ADMET rules, and relevant safety pharmacology thresholds (hERG, CYP). Cite sources explicitly.',
        'fields': [
            ('mw_target', 'Target MW Da', 'Lipinski: ≤500'),
            ('logp_range', 'Target LogP Range', 'Lipinski: ≤5; CNS: 1–3'),
            ('tpsa_target', 'Target TPSA Å²', 'Oral <140; CNS <90'),
            ('solubility_target', 'Solubility Target µg/mL', 'Numeric value'),
            ('herg_safety_limit', 'hERG Safety Limit µM', '>10 µM preferred for safety'),
            ('bioavailability_target', 'Oral Bioavailability Target %', 'Numeric value'),
            ('half_life_target', 'Half-Life Target h', 'Numeric value'),
        ],
    },
    'PreclinicalStudyPlanner': {
        'label': 'Preclinical Study Planner',
        'guidance': 'Design IND-enabling studies per ICH M3(R2) and S7A/S7B. Match study type, species, duration, and route to the clinical development plan.',
        'fields': [
            ('study_type', 'Study Type', 'single_dose_tox / repeat_dose_tox / genotoxicity / safety_pharmacology / pk'),
            ('title', 'Study Title', 'Descriptive title'),
            ('species', 'Species', 'e.g., rat, mouse, dog, cynomolgus monkey'),
            ('dose_route', 'Dose Route', 'e.g., oral, intravenous, subcutaneous'),
            ('dose_levels', 'Dose Levels', 'e.g., 10, 50, 200 mg/kg'),
            ('duration_days', 'Duration days', 'ICH M3: 28 days minimum for Phase I'),
            ('objective', 'Study Objective', 'What the study is designed to determine'),
            ('primary_endpoints', 'Primary Endpoints', 'Key measurements'),
            ('success_criteria', 'Success Criteria', 'What constitutes a passing result'),
        ],
    },
}

_SUGGESTION_INSTRUCTION = """
## Suggestion Format
When you have concrete, evidence-based values to recommend for the form fields listed above, append the following block at the VERY END of your response — after all explanation:

<suggestion>{"field_key": "value"}</suggestion>

Rules:
- Use only the exact field keys listed above.
- Include only fields you are genuinely recommending (do not pad with uncertain values).
- All values must be strings (no raw numbers or booleans).
- The JSON must be valid — one flat object, no nesting.
- If you have no concrete field suggestions for this message, omit the <suggestion> block entirely.
"""


def stream_ai_panel_chat(
    project_id: int,
    page_type: str,
    page_entity: dict,
    message: str,
    session_messages: list | None = None,
):
    """Per-page AI panel chat. Injects page context and plan context for AI-Driven projects."""
    from core.models import Project
    from core.services.rag import retrieve, format_rag_context

    project = Project.objects.get(id=project_id)
    project_ctx = build_project_context(project_id)

    plan_ctx = ''
    if project.mode == 'ai_driven':
        try:
            plan = project.ai_plan
            current_step = None
            if plan.current_step_number:
                current_step = plan.steps.filter(step_number=plan.current_step_number).first()
            if current_step:
                plan_ctx = (
                    f"\n\n## Current Plan Step\n"
                    f"Step {current_step.step_number}: {current_step.title} (Phase: {current_step.phase})\n"
                    f"Status: {current_step.status}\n"
                    f"AI Recommendation: {json.dumps(current_step.ai_recommendation)}"
                )
        except Exception:
            pass

    # Build page-specific context block
    page_ctx_def = PAGE_CONTEXTS.get(page_type, {})
    if page_ctx_def:
        fields_desc = '\n'.join(
            f'  - {key}: {label} — {hint}'
            for key, label, hint in page_ctx_def.get('fields', [])
        )
        current_vals = (
            '\n'.join(f'  - {k}: {v}' for k, v in page_entity.items() if v)
            if page_entity else '  (none set yet)'
        )
        page_block = (
            f"\n\n## Current Page: {page_ctx_def['label']}\n"
            f"{page_ctx_def.get('guidance', '')}\n\n"
            f"### Suggestable Fields:\n{fields_desc}\n\n"
            f"### Current Values:\n{current_vals}\n"
            f"{_SUGGESTION_INSTRUCTION}"
        )
    else:
        page_block = (
            f"\n\nYou are assisting on the {page_type} page. "
            f"Current data: {json.dumps(page_entity)}"
        )

    panel_system = (
        f"{SYSTEM_PROMPT}\n\n"
        f"You are the per-page AI assistant for BioIntel. "
        f"Your role is to help scientists — including non-experts — understand their options "
        f"and suggest concrete values for the form fields on the current page.\n"
        f"{page_block}"
        f"{plan_ctx}"
    )

    rag_chunks = retrieve(
        query=message,
        project_id=project_id,
        molecule_type=project.molecule_type,
    )
    rag_context = format_rag_context(rag_chunks)
    if rag_chunks:
        yield f'data: {json.dumps({"type": "rag_citation", "chunks": rag_chunks})}\n\n'

    messages = list(session_messages or [])
    messages.append({'role': 'user', 'content': message})

    if project_ctx:
        panel_system += f'\n\n--- PROJECT CONTEXT ---\n{project_ctx}'

    yield from _stream_with_tools(panel_system, messages, TOOL_DEFINITIONS, rag_context)


def stream_ai_lab_intake(session_id: int, message: str, session_messages: list):
    """AI Lab intake chat. Conducts structured intake interview and generates project proposal."""
    from core.services.rag import retrieve, format_rag_context

    rag_chunks = retrieve(query=message, top_k=3)
    rag_context = format_rag_context(rag_chunks)

    intake_system = """You are the BioIntel AI Lab advisor, helping a scientist define their drug development project.

Your goal is to conduct a structured intake interview and ultimately propose a complete project plan.

## Intake topics to cover (one or two at a time, conversationally):
1. Target disease or condition
2. Development pathway preference (analog-based vs novel design vs biologic)
3. Known constraints (IP, mechanism avoidance, patient population, safety concerns)
4. Existing internal data (prior studies, known hits, sequence data)
5. Timeline and phase entry point

## When you have enough information, generate a project proposal:
Structure your proposal as:
<proposal>
{
  "project_name": "...",
  "description": "...",
  "pathway": "analog_based|novel_design",
  "molecule_type": "small_molecule|biologic|undetermined",
  "phase": "preclinical|phase1|phase2|phase3",
  "disease_description": "...",
  "constraints": {"avoid_mechanisms": [], "patent_constraints": "", "patient_population": "", "timeline": ""},
  "first_steps": ["Step 1 title", "Step 2 title", "Step 3 title"]
}
</proposal>

Only generate the proposal tag when you are confident you have covered all five intake topics.
Until then, ask focused questions to gather the missing information."""

    messages = list(session_messages)
    messages.append({'role': 'user', 'content': message})

    yield from _stream_with_tools(intake_system, messages, [], rag_context)
