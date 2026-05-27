# Drug Development Data Source APIs — MVP Selection

One API selected per category from `data_source.md`. Selection criteria: free or low-cost access, well-documented REST/GraphQL interface, machine-readable responses (JSON/XML), and sufficient coverage for a drug development AI assistant MVP.

---

## 1. Disease Databases → Open Targets Platform

**Description:** GraphQL API with free access; covers target–disease associations, genetic evidence, clinical data, and drug linkages in a single query surface. Best all-in-one disease context for MVP.

| Field | Detail |
|---|---|
| **API Type** | GraphQL |
| **Base URL** | `https://api.platform.opentargets.org/api/v4/graphql` |
| **Authentication** | None (public) |
| **Rate Limit** | No hard limit; fair-use policy |
| **Data Format** | JSON |

**Key MVP Queries:**
```graphql
# Disease summary + associated targets
query {
  disease(efoId: "EFO_0000400") {
    name
    description
    associatedTargets(page: { index: 0, size: 10 }) {
      rows { target { approvedSymbol } score }
    }
  }
}

# Drug indications for a disease
query {
  disease(efoId: "EFO_0000400") {
    knownDrugs(size: 10) {
      rows { drug { name } phase status }
    }
  }
}
```

---

## 2. Drug Databases → ChEMBL

**Description:** Free REST API; largest open-access database of bioactive molecules with pharmacology, mechanisms of action, drug approval status, and ADMET properties. No registration required.

| Field | Detail |
|---|---|
| **API Type** | REST |
| **Base URL** | `https://www.ebi.ac.uk/chembl/api/data` |
| **Authentication** | None (public) |
| **Rate Limit** | ~10 req/sec |
| **Data Format** | JSON or XML |

**Key MVP Endpoints:**
```
# Drug by name / ChEMBL ID
GET /molecule/CHEMBL25.json

# Drugs by indication (disease)
GET /drug_indication.json?efo_term=diabetes&limit=20

# Approved drugs with mechanism of action
GET /mechanism.json?molecule_chembl_id=CHEMBL25

# Bioactivity data for a compound
GET /activity.json?molecule_chembl_id=CHEMBL25&limit=20
```

---

## 3. Molecule / Compound Databases → PubChem (PUG REST)

**Description:** NCBI's free, highest-coverage chemical database. PUG REST API accepts name, SMILES, InChI, or CID and returns structures, synonyms, computed properties, and cross-references.

| Field | Detail |
|---|---|
| **API Type** | REST (PUG REST) |
| **Base URL** | `https://pubchem.ncbi.nlm.nih.gov/rest/pug` |
| **Authentication** | None (public); optional API key for higher rate limits |
| **Rate Limit** | 5 req/sec without key |
| **Data Format** | JSON, XML, SDF, PNG |

**Key MVP Endpoints:**
```
# Compound by name → CID
GET /compound/name/aspirin/cids/JSON

# Compound properties (logP, MW, TPSA, HBD/HBA, rotatable bonds)
GET /compound/cid/2244/property/MolecularFormula,MolecularWeight,XLogP,TPSA/JSON

# 2D structure image
GET /compound/cid/2244/PNG

# SMILES
GET /compound/cid/2244/property/IsomericSMILES/JSON

# Similar compounds (fingerprint similarity)
GET /compound/fastsimilarity_2d/smiles/CC(=O)Oc1ccccc1C(=O)O/cids/JSON?Threshold=90
```

---

## 4. Formulation & Excipient Databases → OpenFDA (Drug Labels / NDC)

**Description:** Free government API covering FDA-approved drug product labeling (inactive ingredients, dosage forms, routes of administration) and the NDC directory. No key required for low-volume use.

| Field | Detail |
|---|---|
| **API Type** | REST |
| **Base URL** | `https://api.fda.gov` |
| **Authentication** | None for ≤1,000 req/day; free API key for 120,000/day |
| **Rate Limit** | 40 req/min without key |
| **Data Format** | JSON |

**Key MVP Endpoints:**
```
# Drug label: inactive ingredients, dosage form, route
GET /drug/label.json?search=openfda.brand_name:"aspirin"&limit=1

# NDC directory: formulation details for a product
GET /drug/ndc.json?search=generic_name:"metformin"&limit=10

# Inactive ingredients list across all products
GET /drug/label.json?search=inactive_ingredient:"microcrystalline+cellulose"&limit=5

# Drug product by NDC code
GET /drug/ndc.json?search=product_ndc:"0069-3060"
```

---

## 5. Physicochemical Property Databases → pkCSM

**Description:** Free REST API for predicting ADME and toxicity endpoints (solubility, permeability, CYP metabolism, hERG inhibition, organ toxicity) from SMILES. No registration required for basic use.

| Field | Detail |
|---|---|
| **API Type** | REST (POST) |
| **Base URL** | `https://biosig.lab.uq.edu.au/pkcsm/api` |
| **Authentication** | None (public) |
| **Rate Limit** | Fair-use |
| **Data Format** | JSON |

**Key MVP Endpoints:**
```
# Predict full ADMET profile from SMILES
POST /predict
Content-Type: application/json
{
  "smiles": "CC(=O)Oc1ccccc1C(=O)O"
}

# Returns: water solubility, Caco-2 permeability, BBB penetration,
#          CYP inhibition, T1/2, VD, renal clearance, hERG, AMES,
#          hepatotoxicity, skin sensitization
```

---

## 6. Synthesis & Reaction Databases → Reaxys (Elsevier)

**Description:** Most comprehensive reaction database for pharmaceutical synthesis; supports retrosynthesis queries and experimental condition lookup. Commercial subscription required — standard in pharma R&D environments.

| Field | Detail |
|---|---|
| **API Type** | REST |
| **Base URL** | `https://www.reaxys.com/api` (institutional access) |
| **Authentication** | API key (institutional subscription) |
| **Rate Limit** | Per subscription tier |
| **Data Format** | JSON / XML |

**Key MVP Endpoints:**
```
# Authenticate and get session token
POST /reaxys/api/rx/session/v1/api_key/{api_key}

# Search reactions by product SMILES
POST /reaxys/api/rx/reaction/v1/search
{ "query": { "structures": [{ "structure": "SMILES", "mode": "SUBSTRUCTURE" }] } }

# Retrieve reaction details (conditions, yield, reference)
GET /reaxys/api/rx/reaction/v1/{reactionId}

# Retrosynthesis (transform API)
POST /reaxys/api/rx/transform/v1/retrosynthesis
{ "smiles": "target_molecule_SMILES", "maxSteps": 3 }
```

> **MVP note:** If institutional Reaxys access is unavailable, use the free alternatives below.

### Free Alternative A — ASKCOS (MIT)

**Description:** MIT's open-source Computer-Aided Synthesis Planning (CASP) tool with a public REST API. Provides retrosynthesis tree generation, forward reaction prediction, and reaction condition recommendation — covers the core synthesis planning use cases without any subscription.

| Field | Detail |
|---|---|
| **API Type** | REST |
| **Base URL** | `https://askcos.mit.edu/api/v2` |
| **Authentication** | None (public demo); self-hostable via Docker for production |
| **Rate Limit** | Fair-use on public instance; unlimited if self-hosted |
| **Data Format** | JSON |
| **Source** | github.com/ASKCOS/ASKCOS |

**Key MVP Endpoints:**
```
# Single-step retrosynthesis: top precursor candidates for a target SMILES
POST /retro/
{ "smiles": "CC(=O)Oc1ccccc1C(=O)O", "num_templates": 10, "max_cum_prob": 0.999 }

# Multi-step retrosynthesis tree (MCTS-based)
POST /tree-builder/
{ "smiles": "target_SMILES", "max_depth": 5, "max_branching": 5,
  "expansion_time": 60, "buyables_source": ["reaxys", "sigma"] }

# Forward reaction prediction (predict product from reactants)
POST /forward/
{ "reactants": "CC(=O)O.c1ccccc1O", "reagents": "", "solvent": "" }

# Reaction condition recommendation (solvent, reagent, temperature)
POST /context/
{ "reactants": "CCO", "products": "CC=O", "n_conditions": 5 }

# Check if a compound is commercially available (buyable)
GET /buyables/?q=CC(=O)Oc1ccccc1C(=O)O&limit=5
```

### Free Alternative B — Open Reaction Database (ORD)

**Description:** Industry-wide open-source reaction database (Google, MIT, Merck, Pfizer) with 1M+ reactions in a standardized schema. Data is freely downloadable from GitHub and queryable via Google BigQuery free tier — no subscription needed.

| Field | Detail |
|---|---|
| **API Type** | BigQuery SQL + GitHub download |
| **Base URL** | `https://client.open-reaction-database.org` (web UI) |
| **Authentication** | Google account for BigQuery free tier |
| **Rate Limit** | BigQuery free tier: 1 TB/month of queries |
| **Data Format** | Protocol Buffer (`.pb`), JSON, BigQuery tables |
| **Source** | github.com/Open-Reaction-Database/ord-data |

**Key MVP Access Patterns:**
```sql
-- BigQuery: reactions involving a specific reagent
SELECT reaction_id, inputs, outcomes
FROM `ord-data.ord.reactions`
WHERE EXISTS (
  SELECT 1 FROM UNNEST(inputs) AS inp
  WHERE LOWER(inp.description) LIKE '%palladium%'
)
LIMIT 50;

-- Reactions by reaction type (e.g., Suzuki coupling)
SELECT reaction_id, reaction_smarts, conditions
FROM `ord-data.ord.reactions`
WHERE reaction_type = 'CROSS_COUPLING'
LIMIT 20;
```

```bash
# Bulk download all reaction data (Protocol Buffer files) from GitHub
git clone https://github.com/Open-Reaction-Database/ord-data
# Each .pb file is one dataset; parse with the ord-schema Python library:
pip install ord-schema
python -c "from ord_schema.proto import reaction_pb2; ..."
```

---

## 7. Analytical & Spectroscopic Databases → NIST WebBook

**Description:** Free, authoritative NIST spectral and thermophysical data accessible via stable URL patterns. Provides IR, MS, and UV/Vis spectra plus thermodynamic constants for reference compounds.

| Field | Detail |
|---|---|
| **API Type** | REST (URL-based, not a formal API) |
| **Base URL** | `https://webbook.nist.gov/cgi-bin` |
| **Authentication** | None (public) |
| **Rate Limit** | Fair-use |
| **Data Format** | JSON (thermophysical), JCAMP-DX (spectra), HTML |

**Key MVP Endpoints:**
```
# Compound data by CAS number (JSON)
GET https://webbook.nist.gov/cgi-bin/cbook.cgi?ID=50-78-2&Units=SI&cIR=on&cMS=on&Type=IR&Index=0&JCAMP=on

# Thermophysical properties
GET https://webbook.nist.gov/cgi-bin/cbook.cgi?ID=50-78-2&Type=JANAFG&Table=on

# Search by molecular formula
GET https://webbook.nist.gov/cgi-bin/cbook.cgi?Formula=C9H8O4&NoIon=on&Units=SI

# Mass spectrum as JCAMP-DX
GET https://webbook.nist.gov/cgi-bin/cbook.cgi?ID=50-78-2&Type=MassSpec&Index=0&JCAMP=on
```

> **MVP note:** For structured programmatic access to spectral data, pair NIST with the **NIST Mass Spectral Library (NISTMS)** local database or use **mzCloud REST API** (Thermo Fisher; requires license) for MS/MS fragmentation matching.

---

## 8. Pharmacology & Target Databases → UniProt REST API

**Description:** Canonical protein database with a mature, well-documented REST API. Returns protein function, tissue expression, pathways, disease associations, and 3D structure links — essential context for any drug target.

| Field | Detail |
|---|---|
| **API Type** | REST |
| **Base URL** | `https://rest.uniprot.org` |
| **Authentication** | None (public) |
| **Rate Limit** | No hard limit; polite crawling expected |
| **Data Format** | JSON, TSV, FASTA, XML |

**Key MVP Endpoints:**
```
# Protein entry by UniProt accession
GET /uniprotkb/P00533.json

# Search by gene name + organism
GET /uniprotkb/search?query=gene:EGFR+AND+organism_id:9606&format=json

# Protein function, disease associations, tissue expression
GET /uniprotkb/P00533?fields=protein_name,gene_names,function,disease,tissue_specificity&format=json

# Proteins associated with a pathway
GET /uniprotkb/search?query=pathway:"MAPK+signaling"&reviewed=true&format=json

# Cross-references to PDB, ChEMBL, DrugBank
GET /uniprotkb/P00533?fields=xref_pdb,xref_chembl,xref_drugbank&format=json
```

---

## 9. Safety, Toxicity & ADMET Databases → EPA CompTox Dashboard

**Description:** Free REST API from US EPA backed by DSSTox; returns experimental and predicted physicochemical, toxicological, and hazard data. Excellent ADMET and safety endpoint coverage without subscription.

| Field | Detail |
|---|---|
| **API Type** | REST |
| **Base URL** | `https://comptox.epa.gov/dashboard-api` |
| **Authentication** | Free API key (register at EPA CompTox) |
| **Rate Limit** | 100 req/min with key |
| **Data Format** | JSON |

**Key MVP Endpoints:**
```
# Chemical details by DTXSID or name
GET /ccdapp1/search/chemical/equal/aspirin/?projection=chemicaldetailall

# Toxicity data (acute, chronic, developmental, carcinogenicity)
GET /ccdapp1/hazard/search/by-dtxsid/DTXSID5020108/?projection=hazardall

# Physicochemical properties (experimental + predicted)
GET /ccdapp1/chemical/detail/search/by-dtxsid/DTXSID5020108/?projection=chem-detail-exp-prop

# Bioassay summary (Tox21 / ToxCast results)
GET /ccdapp1/bioactivity/search/by-dtxsid/DTXSID5020108/

# Batch lookup by SMILES list
POST /ccdapp1/chemical/search/equal/
["InChIKey=BSYNRYMUTXBXSQ-UHFFFAOYSA-N"]
```

---

## 10. Regulatory & Pharmacopoeia Databases → DailyMed (NLM)

**Description:** Official NLM service for FDA-approved Structured Product Labels (SPLs); free REST and FHIR R4 APIs. Provides authoritative drug labeling: indications, contraindications, warnings, dosage, and clinical pharmacology — distinct from OpenFDA's adverse event focus.

| Field | Detail |
|---|---|
| **API Type** | REST + FHIR R4 |
| **Base URL** | `https://dailymed.nlm.nih.gov/dailymed/services` |
| **Authentication** | None (public) |
| **Rate Limit** | Fair-use |
| **Data Format** | JSON, XML |

**Key MVP Endpoints:**
```
# Search SPLs by drug name
GET /spls.json?drug_name=metformin

# Full SPL document (indications, warnings, dosage, clinical pharmacology)
GET /spls/{set_id}.json

# All SPLs for an active ingredient
GET /spls.json?ingredient=metformin+hydrochloride

# NDC codes for a product
GET /ndcs.json?drug_name=metformin&limit=10

# FHIR MedicationKnowledge resource
GET https://dailymed.nlm.nih.gov/dailymed/fhir/v1/MedicationKnowledge?code=metformin
```

---

## 11. Clinical Trial & Epidemiology Databases → ClinicalTrials.gov API v2

**Description:** Official US NIH registry with a modern REST API (v2, launched 2023). Returns structured protocol data, eligibility criteria, interventions, outcomes, and results — directly relevant to understanding the development landscape for a compound or indication.

| Field | Detail |
|---|---|
| **API Type** | REST |
| **Base URL** | `https://clinicaltrials.gov/api/v2` |
| **Authentication** | None (public) |
| **Rate Limit** | ~10 req/sec |
| **Data Format** | JSON |

**Key MVP Endpoints:**
```
# Search trials by condition and intervention
GET /studies?query.cond=type+2+diabetes&query.intr=metformin&pageSize=20

# Trial details by NCT ID
GET /studies/NCT00000000

# Studies by phase and status
GET /studies?filter.advanced=AREA[Phase]PHASE3+AND+AREA[OverallStatus]RECRUITING

# Aggregate statistics (trial counts by phase for an indication)
GET /stats/field/values?types=AREA[Phase]&query.cond=breast+cancer

# Results data for completed trials
GET /studies?query.intr=pembrolizumab&filter.advanced=AREA[HasResults]true
```

---

## 12. Literature & Patent Databases → PubMed E-utilities (NCBI)

**Description:** Free NCBI API covering 36M+ biomedical citations. E-utilities (ESearch, EFetch, ELink) are standard in bioinformatics pipelines and integrate with other NCBI resources (PubChem, Gene, Protein).

| Field | Detail |
|---|---|
| **API Type** | REST (E-utilities) |
| **Base URL** | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils` |
| **Authentication** | Free API key recommended (10 req/sec vs 3 req/sec) |
| **Rate Limit** | 3 req/sec without key; 10 req/sec with key |
| **Data Format** | JSON, XML |

**Key MVP Endpoints:**
```
# Search PubMed: returns PMIDs
GET /esearch.fcgi?db=pubmed&term=metformin+diabetes&retmax=20&retmode=json

# Fetch abstracts by PMID list
GET /efetch.fcgi?db=pubmed&id=33472028,33472029&rettype=abstract&retmode=json

# Link PubChem CID → PubMed articles
GET /elink.fcgi?dbfrom=pccompound&db=pubmed&id=4091&cmd=neighbor_score&retmode=json

# Summary records (title, authors, journal, date)
GET /esummary.fcgi?db=pubmed&id=33472028&retmode=json

# Fetch full record as PubMed XML
GET /efetch.fcgi?db=pubmed&id=33472028&rettype=full&retmode=xml
```

---

## 13. Manufacturing & Process Development → FDA Guidance Documents API

**Description:** FDA publishes all guidance documents (process validation, CMC, PAT, method validation) via a structured REST API on api.fda.gov and as indexed PDFs on FDA.gov. For an MVP, these documents are ingested as a static knowledge base rather than queried live; the API supports retrieving the latest versions programmatically.

| Field | Detail |
|---|---|
| **API Type** | REST |
| **Base URL** | `https://api.fda.gov/other/guidance` |
| **Authentication** | None for ≤1,000 req/day; free API key for 120,000/day |
| **Rate Limit** | 40 req/min without key |
| **Data Format** | JSON (metadata + PDF links) |

**Key MVP Endpoints:**
```
# Search guidance documents by topic
GET https://api.fda.gov/other/guidance.json?search=process+validation&limit=10

# ICH Q-series guidances
GET https://api.fda.gov/other/guidance.json?search=ICH+Q8&limit=5

# PAT-related guidance
GET https://api.fda.gov/other/guidance.json?search=process+analytical+technology&limit=5

# Most recent CMC guidances
GET https://api.fda.gov/other/guidance.json?search=chemistry+manufacturing+controls&sort=date:desc&limit=10
```

**MVP knowledge base approach:** Fetch PDFs at startup using the `pdf_url` field in responses, extract text (e.g., via `pdfminer` / `pypdf`), chunk, embed, and store in a vector database for retrieval-augmented generation (RAG).

---

## Summary Table

| # | Category | Selected API | Access | Type |
|---|---|---|---|---|
| 1 | Disease | Open Targets Platform | Free | GraphQL |
| 2 | Drug Databases | ChEMBL | Free | REST |
| 3 | Molecule / Compound | PubChem PUG REST | Free | REST |
| 4 | Formulation & Excipient | OpenFDA (Drug Labels / NDC) | Free | REST |
| 5 | Physicochemical Properties | pkCSM | Free | REST |
| 6 | Synthesis & Reaction | Reaxys | Commercial | REST |
| 7 | Analytical & Spectroscopic | NIST WebBook | Free | REST (URL) |
| 8 | Pharmacology & Target | UniProt REST | Free | REST |
| 9 | Safety, Toxicity & ADMET | EPA CompTox Dashboard | Free (key) | REST |
| 10 | Regulatory & Pharmacopoeia | DailyMed (NLM) | Free | REST / FHIR |
| 11 | Clinical Trials | ClinicalTrials.gov API v2 | Free | REST |
| 12 | Literature & Patent | PubMed E-utilities (NCBI) | Free (key) | REST |
| 13 | Manufacturing & Process | FDA Guidance Documents | Free | REST + PDF |
