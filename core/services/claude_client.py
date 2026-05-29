import json
import anthropic
from django.conf import settings

from . import pubchem, chembl, opentargets, uniprot, pkcsm, comptox
from . import openfda, dailymed, clinicaltrials, pubmed, askcos, nist, surechembl

MODEL = 'claude-sonnet-4-6'

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
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    system = SYSTEM_PROMPT
    if project_context:
        system += f'\n\n--- CURRENT PROJECT CONTEXT ---\n{project_context}'

    api_messages = list(messages)
    sources = []

    while True:
        with client.messages.stream(
            model=MODEL,
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


def generate_once(system: str, user_content: str):
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    with client.messages.stream(
        model=MODEL,
        max_tokens=4096,
        system=system,
        messages=[{'role': 'user', 'content': user_content}],
    ) as stream:
        for text in stream.text_stream:
            yield f'data: {json.dumps({"type": "text_delta", "text": text})}\n\n'
    yield f'data: {json.dumps({"type": "message_stop"})}\n\n'
