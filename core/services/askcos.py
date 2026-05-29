"""
Local retrosynthesis using RDKit reaction SMARTS transforms.
Replaces the defunct ASKCOS public API (askcos.mit.edu/api/v2 returned 404).
"""
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors

# Common medicinal-chemistry retrosynthetic transforms as reaction SMARTS.
# Each entry: (name, retro_smarts, forward_description)
RETRO_TRANSFORMS = [
    (
        'Ester hydrolysis',
        '[C:1](=[O:2])[O:3][C:4]>>[C:1](=[O:2])[OH].[C:4][OH]',
        'Esterification of carboxylic acid + alcohol',
    ),
    (
        'Amide bond formation',
        '[C:1](=[O:2])[N:3]>>[C:1](=[O:2])[OH].[N:3]',
        'Coupling of carboxylic acid + amine (HATU/DCC)',
    ),
    (
        'N-alkylation',
        '[N:1][C:2]>>[N:1].[C:2][Br]',
        'Alkylation of amine with alkyl halide',
    ),
    (
        'Aromatic acylation (Friedel-Crafts)',
        '[c:1][C:2](=[O:3])[C:4]>>[c:1].[C:2](=[O:3])([C:4])Cl',
        'Friedel-Crafts acylation',
    ),
    (
        'Boc protection removal',
        '[N:1][C](=[O])[O][C]([CH3])([CH3])[CH3]>>[N:1]',
        'Boc deprotection (TFA/HCl)',
    ),
    (
        'Aldehyde oxidation',
        '[C:1](=[O:2])[OH]>>[C:1](=[O:2])[H]',
        'Oxidation of aldehyde to carboxylic acid',
    ),
    (
        'Reductive amination',
        '[N:1][C:2]>>[N:1].[C:2]=[O]',
        'Reductive amination of amine + aldehyde/ketone (NaBH3CN)',
    ),
    (
        'Suzuki coupling',
        '[c:1][c:2]>>[c:1]Br.[c:2]B(O)O',
        'Suzuki-Miyaura cross-coupling (Pd catalyst)',
    ),
    (
        'Acetylation',
        '[O,N:1][C:2](=[O:3])[CH3:4]>>[O,N:1].[CH3:4][C:2](=[O:3])Cl',
        'Acetylation with acetic anhydride or acetyl chloride',
    ),
    (
        'Phenol ether formation (Williamson)',
        '[c:1][O:2][C:3]>>[c:1][OH].[C:3][Br]',
        "Williamson ether synthesis (base + alkyl halide)",
    ),
    (
        'Reduction of nitro to amine',
        '[c:1][N:2]>>[c:1][N+:2](=O)[O-]',
        'Reduction of aromatic nitro to amine (Fe/HCl or H2/Pd)',
    ),
    (
        'Carbamate formation',
        '[N:1][C:2](=[O:3])[O:4]>>[N:1].[O:4][C:2](=[O:3])Cl',
        'Carbamate from amine + chloroformate',
    ),
]


def _apply_retro(mol, smarts, name, description):
    """Apply a retrosynthetic SMARTS and return matched precursors."""
    try:
        rxn = AllChem.ReactionFromSmarts(smarts)
        if rxn is None:
            return None
        products = rxn.RunReactants((mol,))
        if not products:
            return None
        results = []
        seen = set()
        for prod_tuple in products[:3]:
            smiles_parts = []
            valid = True
            for p in prod_tuple:
                try:
                    Chem.SanitizeMol(p)
                    s = Chem.MolToSmiles(p)
                    smiles_parts.append(s)
                except Exception:
                    valid = False
                    break
            if valid and smiles_parts:
                key = '.'.join(sorted(smiles_parts))
                if key not in seen:
                    seen.add(key)
                    results.append({
                        'smiles': '.'.join(smiles_parts),
                        'precursors': smiles_parts,
                        'transform': name,
                        'forward_reaction': description,
                        'score': 1.0,
                    })
        return results or None
    except Exception:
        return None


def _mol_descriptors(mol):
    return {
        'mw': round(Descriptors.MolWt(mol), 2),
        'logp': round(Descriptors.MolLogP(mol), 2),
        'hbd': Descriptors.NumHDonors(mol),
        'hba': Descriptors.NumHAcceptors(mol),
        'tpsa': round(Descriptors.TPSA(mol), 1),
        'rotatable_bonds': Descriptors.NumRotatableBonds(mol),
    }


def single_step_retro(smiles: str, num_templates: int = 10) -> dict:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {'error': f'Invalid SMILES: {smiles}'}

    results = []
    for name, smarts, description in RETRO_TRANSFORMS:
        matches = _apply_retro(mol, smarts, name, description)
        if matches:
            results.extend(matches)

    return {
        'smiles': smiles,
        'descriptors': _mol_descriptors(mol),
        'results': results[:num_templates] if results else [],
        'message': None if results else 'No common retrosynthetic disconnections found for this structure.',
    }


def multi_step_tree(smiles: str, max_depth: int = 3) -> dict:
    """Recursive retrosynthesis up to max_depth steps."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {'error': f'Invalid SMILES: {smiles}'}

    def expand(s, depth):
        if depth == 0:
            return {'smiles': s, 'children': [], 'terminal': True}
        m = Chem.MolFromSmiles(s)
        if m is None:
            return {'smiles': s, 'children': [], 'terminal': True}
        node = {'smiles': s, 'children': [], 'terminal': False}
        for name, smarts_str, description in RETRO_TRANSFORMS[:6]:
            matches = _apply_retro(m, smarts_str, name, description)
            if matches:
                match = matches[0]
                child_nodes = [expand(p, depth - 1) for p in match['precursors']]
                node['children'].append({
                    'transform': name,
                    'forward_reaction': description,
                    'precursors': child_nodes,
                })
                break
        if not node['children']:
            node['terminal'] = True
        return node

    tree = expand(smiles, max_depth)
    return {'smiles': smiles, 'tree': tree}


def forward_predict(reactants: str, reagents: str = '', solvent: str = '') -> dict:
    """Predict likely products from reactants using forward reaction SMARTS."""
    mol = Chem.MolFromSmiles(reactants)
    if mol is None:
        return {'error': f'Invalid SMILES: {reactants}'}

    # Forward transforms (reverse of retro): try common reactions
    forward_transforms = [
        ('Esterification', '[C:1](=[O:2])[OH].[C:3][OH]>>[C:1](=[O:2])[O:3][C:3].[OH2]'),
        ('Amide coupling', '[C:1](=[O:2])[OH].[N:3]>>[C:1](=[O:2])[N:3].[OH2]'),
        ('Acetylation', '[O,N:1].[CH3][C](=[O])Cl>>[O,N:1][C](=[O])[CH3]'),
    ]

    results = []
    for name, smarts in forward_transforms:
        try:
            rxn = AllChem.ReactionFromSmarts(smarts)
            if rxn is None:
                continue
            parts = reactants.split('.')
            if len(parts) >= 2:
                m1 = Chem.MolFromSmiles(parts[0])
                m2 = Chem.MolFromSmiles(parts[1])
                if m1 and m2:
                    prods = rxn.RunReactants((m1, m2))
                    for pt in prods[:2]:
                        try:
                            Chem.SanitizeMol(pt[0])
                            results.append({
                                'reaction': name,
                                'product': Chem.MolToSmiles(pt[0]),
                                'score': 0.8,
                            })
                        except Exception:
                            pass
        except Exception:
            pass

    return {
        'reactants': reactants,
        'reagents': reagents,
        'solvent': solvent,
        'results': results,
        'message': None if results else 'Provide two reactants separated by "." to predict a product.',
    }


def recommend_conditions(reactants: str, products: str, reaction_type: str = '', n: int = 5) -> dict:
    conditions_db = [
        {'reaction_type': 'Esterification',       'keywords': ['ester', 'esterification'],              'reagents': 'DCC, DMAP',               'solvent': 'DCM',        'temp': '0°C → RT', 'time': '12 h'},
        {'reaction_type': 'Amide coupling',        'keywords': ['amide', 'amide bond', 'amide coupling'],'reagents': 'HATU, DIPEA',             'solvent': 'DMF',        'temp': 'RT',       'time': '2–4 h'},
        {'reaction_type': 'Suzuki coupling',       'keywords': ['suzuki', 'cross-coupling'],             'reagents': 'Pd(PPh₃)₄, K₂CO₃',       'solvent': 'DME/H₂O',   'temp': '80°C',     'time': '12 h'},
        {'reaction_type': 'Reductive amination',   'keywords': ['reductive', 'reductive amination'],     'reagents': 'NaBH₃CN, AcOH',           'solvent': 'MeOH',       'temp': 'RT',       'time': '4 h'},
        {'reaction_type': 'N-alkylation',          'keywords': ['alkylation', 'n-alkylation'],           'reagents': 'K₂CO₃, alkyl halide',     'solvent': 'DMF',        'temp': '60°C',     'time': '8 h'},
        {'reaction_type': 'Acetylation',           'keywords': ['acetyl', 'acetylation'],                'reagents': 'Ac₂O, Et₃N',              'solvent': 'DCM',        'temp': '0°C → RT', 'time': '2 h'},
        {'reaction_type': 'Boc deprotection',      'keywords': ['boc', 'deprotect', 'deprotection'],     'reagents': 'TFA (20% in DCM)',         'solvent': 'DCM',        'temp': 'RT',       'time': '1–2 h'},
        {'reaction_type': 'Friedel-Crafts',        'keywords': ['friedel', 'acylation'],                 'reagents': 'AlCl₃',                   'solvent': 'DCM',        'temp': '0°C',      'time': '2 h'},
        {'reaction_type': 'Williamson ether',      'keywords': ['williamson', 'ether', 'phenol ether'],  'reagents': 'K₂CO₃, alkyl halide',     'solvent': 'Acetone',    'temp': '60°C',     'time': '6 h'},
        {'reaction_type': 'Nitro reduction',       'keywords': ['nitro', 'reduction'],                   'reagents': 'Fe, NH₄Cl  (or H₂/Pd-C)', 'solvent': 'EtOH/H₂O',  'temp': '80°C',     'time': '2 h'},
        {'reaction_type': 'Carbamate formation',   'keywords': ['carbamate'],                            'reagents': 'Et₃N, chloroformate',      'solvent': 'DCM',        'temp': '0°C → RT', 'time': '4 h'},
        {'reaction_type': 'Oxidation',             'keywords': ['oxidation', 'oxidise'],                 'reagents': 'KMnO₄ or PCC',            'solvent': 'DCM',        'temp': 'RT',       'time': '4 h'},
    ]

    if reaction_type:
        rt_lower = reaction_type.lower()
        for entry in conditions_db:
            if any(kw in rt_lower for kw in entry['keywords']) or rt_lower in entry['reaction_type'].lower():
                return {'reactants': reactants, 'products': products, 'conditions': [entry]}

    return {'reactants': reactants, 'products': products, 'conditions': conditions_db[:n]}


def check_buyable(smiles: str) -> dict:
    """Heuristic buyability check based on molecular complexity."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {'smiles': smiles, 'buyable': False, 'reason': 'Invalid SMILES'}
    mw = Descriptors.MolWt(mol)
    rings = mol.GetRingInfo().NumRings()
    heavy = mol.GetNumHeavyAtoms()
    buyable = mw < 300 and rings <= 2 and heavy <= 20
    return {
        'smiles': smiles,
        'buyable': buyable,
        'mw': round(mw, 1),
        'rings': rings,
        'heavy_atoms': heavy,
        'reason': 'Simple building block — likely commercially available' if buyable else 'Complex structure — custom synthesis likely required',
    }
