# Drug Development Data Sources

Reference catalog of public and commercial databases relevant to the AI Assistant's Data Integration Layer, covering all phases of drug development from target identification through manufacturing readiness.

---

## 1. Disease Databases

| Database | Description |
|---|---|
| **OMIM** (Online Mendelian Inheritance in Man) | Comprehensive catalog of human genes and genetic disorders; phenotype–genotype relationships. |
| **DisGeNET** | Curated gene–disease associations from expert-curated and text-mined sources; disease-gene network analysis. |
| **MONDO Disease Ontology** | Harmonized cross-species disease ontology integrating OMIM, Orphanet, NCIT, and others. |
| **Disease Ontology (DO)** | Standardized ontology for human disease terms; maps to MeSH, ICD, NCI, SNOMED, OMIM. |
| **ICD-10 / ICD-11** (WHO) | International classification of diseases and related health problems; the global standard for disease coding. |
| **Orphanet** | Reference portal for rare diseases and orphan drugs; prevalence data, gene panels, clinical summaries. |
| **MalaCards** | Integrated human disease database aggregating information from 70+ data sources. |
| **KEGG Disease** | Disease entries linked to molecular interaction networks, pathways, and drugs in the KEGG framework. |
| **Open Targets Platform** | Systematic evidence for target–disease associations integrating GWAS, expression, somatic mutations, and drug data. |
| **MedDRA** (Medical Dictionary for Regulatory Activities) | Internationally recognized medical terminology used for regulatory submissions and adverse event coding. |
| **CTD** (Comparative Toxicogenomics Database) | Chemical–gene/protein–disease relationships; links environmental chemicals to human disease. |

---

## 2. Drug Databases (by Disease / Therapeutic Classification)

| Database | Description |
|---|---|
| **DrugBank** | Comprehensive drug–target resource: chemical data, pharmacology, mechanisms of action, ADMET, interactions. Drugs organized by pharmacological class and indication. |
| **ChEMBL** | Manually curated database of bioactive molecules with drug-like properties; bioactivity data from literature and clinical data. |
| **DrugCentral** | Drug information resource integrating FDA/EMA approvals, drug–target relationships, indications, and pharmacology. |
| **Drugs@FDA** | Official FDA database of approved drug products; labeling, application history, approval dates. |
| **EMA Medicines** (European Medicines Agency) | Centrally authorized medicines in the EU; EPARs, product labels, CHMP opinions. |
| **WHO Essential Medicines List** | WHO model list of medicines deemed most effective and safe to meet priority health needs. |
| **PharmGKB** | Pharmacogenomics knowledge base; curated drug–gene–phenotype relationships and pathways. |
| **DailyMed** | Official NLM provider of FDA-approved drug labeling information; structured product labels (SPLs). |
| **RxNorm** | NLM normalized naming system for clinical drugs; links drug names across vocabulary systems. |
| **NCI Thesaurus** (NCIt) | Cancer-specific drug terminology; antineoplastic agents classified by mechanism and target. |
| **KEGG Drug** | Drug entries linked to targets, pathways, diseases, and interactions within the KEGG integrated knowledgebase. |
| **ATC Classification** (WHO Anatomical Therapeutic Chemical) | WHO standard for classifying drugs by their therapeutic, pharmacological, and chemical properties at five levels. |
| **OpenFDA** | FDA open data API: adverse events (FAERS), drug labels, enforcement reports, NDC directory. |

---

## 3. Molecule / Compound Databases

| Database | Description |
|---|---|
| **PubChem** | NCBI's open repository of chemical structures, properties, bioactivities, and annotations; largest free chemical database. |
| **ChemSpider** | RSC chemical structure database aggregating data from 270+ sources; includes predicted and experimental properties. |
| **ZINC Database** | Commercially available compounds in ready-to-dock, 3D formats for virtual screening; drug-like and lead-like subsets. |
| **CAS SciFinder** | Comprehensive chemical substance and reaction database from the American Chemical Society; includes CAS Registry Numbers. |
| **Reaxys** | Elsevier's database of chemical substances, reactions, and property data from patents and peer-reviewed literature. |
| **Cambridge Structural Database (CSD)** | CCDC repository of experimentally determined organic and metal-organic crystal structures; polymorph data. |
| **UniChem** | EBI cross-referencing service mapping compound identifiers across 40+ chemistry databases. |
| **BindingDB** | Measured binding affinities of small molecules and proteins; focused on drug-target interactions. |
| **ChEMBL Compounds** | Small-molecule drug candidates and approved drugs with standardized structures and bioactivity profiles. |
| **Protein Data Bank (PDB)** | Worldwide repository of 3D structures of proteins, nucleic acids, and complexes; critical for structure-based drug design. |

---

## 4. Formulation & Excipient Databases

| Database | Description |
|---|---|
| **FDA Inactive Ingredient Guide (IIG)** | List of inactive ingredients in FDA-approved drug products with maximum potency levels by route of administration. |
| **Handbook of Pharmaceutical Excipients** (Pharmpress/APhA) | Monographs for pharmaceutical excipients: function, compatibility, regulatory status, physicochemical properties. |
| **EXCIPACT** | Global excipient quality standard and supplier certification database for pharmaceutical excipients. |
| **FDA Orange Book** | Approved drug products with therapeutic equivalence evaluations; formulations, dosage forms, and patent/exclusivity data. |
| **FDA Purple Book** | FDA's list of licensed biological products (biosimilars and reference biologics) with approval and exclusivity information. |
| **NCATS Pharmaceutical Collection (NPC)** | NIH annotated library of clinically approved drugs and drug candidates; useful for formulation and repurposing. |
| **USP Excipient Monographs** | Official USP–NF standards for excipient identity, purity, and testing methods. |
| **GRAS Database (FDA)** | Generally Recognized As Safe substances allowed in food and pharmaceutical applications. |

---

## 5. Physicochemical Property Databases

| Database | Description |
|---|---|
| **PhysProp (EPISuite/EPA)** | Experimental and estimated physicochemical properties: logP, water solubility, boiling point, vapor pressure. |
| **ALOGPS** | Predicted logP and solubility values using multiple algorithms; web-based ADME property calculator. |
| **SwissADME** | Free web tool from SIB for predicting ADME and drug-likeness properties (Lipinski, TPSA, bioavailability radar). |
| **ADMET Predictor** (Simulations Plus) | Commercial tool for predicting absorption, distribution, metabolism, excretion, and toxicity from structure. |
| **EPISuite** (US EPA) | Suite of environmental fate and physicochemical property estimation tools for organic chemicals. |
| **NIST WebBook** | NIST Standard Reference Data: thermophysical, thermochemical, spectroscopic, and reaction kinetic data. |
| **HMDB** (Human Metabolome Database) | Metabolomics resource with experimental physicochemical, spectral, and biological properties of human metabolites. |
| **Solubility Challenge Dataset** | Curated experimental aqueous solubility data used to benchmark in silico solubility models. |

---

## 6. Synthesis & Reaction Databases

| Database | Description |
|---|---|
| **Reaxys** | Elsevier reaction database covering 50M+ reactions from patents and journals; retrosynthesis support. |
| **CAS SciFinder (Reactions)** | 100M+ single- and multi-step reactions with experimental conditions, yields, and references. |
| **USPTO Patent Full-Text** | US patent literature including synthetic procedures; searchable via CAS, Reaxys, or Google Patents. |
| **Organic Syntheses** | Peer-reviewed, checked procedures for the synthesis of organic compounds; high reliability benchmark procedures. |
| **SPRESI** | Infochem reaction and substance database; historically significant structure-reaction data. |
| **CSD (Cambridge Structural Database)** | Crystal structure data including polymorph screening results; supports solid-state form selection. |
| **ICSD** (Inorganic Crystal Structure Database) | Crystal structures of inorganic and metal-organic compounds relevant to drug salt and co-crystal screening. |
| **Pistachio** (NextMove Software) | Large-scale extracted reaction database from patents for machine learning and synthesis planning. |

---

## 7. Analytical & Spectroscopic Databases

| Database | Description |
|---|---|
| **SDBS** (Spectral Database for Organic Compounds, AIST) | Free database of NMR (¹H, ¹³C), IR, MS, and Raman spectra for organic compounds. |
| **NIST Mass Spectrometry Library** | Over 350,000 EI-MS spectra; the gold standard reference library for compound identification. |
| **mzCloud** | High-resolution multi-stage MS/MS spectral library from Thermo Fisher; fragmentation trees for identification. |
| **HMDB NMR / MS** | Experimental NMR and MS spectra for human metabolites; supports metabolomics and impurity identification. |
| **CCDC Crystal Form Databases** | Reference data for crystal forms, polymorphs, and co-crystals used in API solid-form characterization. |
| **NIST WebBook (Spectral)** | IR spectra, UV/Vis spectra, mass spectra for organic molecules referenced to NIST standards. |
| **BioMagResBank (BMRB)** | NMR data for proteins, nucleic acids, and metabolites; relevant to biologics characterization. |

---

## 8. Pharmacology & Target Databases

| Database | Description |
|---|---|
| **UniProt / Swiss-Prot** | Curated protein sequence and functional data; canonical reference for drug target annotations. |
| **Protein Data Bank (PDB)** | 3D structures of biological macromolecules; central resource for structure-based drug design and binding site analysis. |
| **ChEMBL (Bioactivity)** | IC50, Ki, EC50, and Kd data for small molecules against biological targets from peer-reviewed literature. |
| **KEGG DRUG / PATHWAY** | Drug–target–pathway relationships integrated with metabolic and signaling networks. |
| **Reactome** | Curated human biological pathways and reactions; identifies affected pathways for a given drug target. |
| **STRING** | Protein–protein interaction network; functional associations from experiments, databases, text, and co-expression. |
| **Guide to Pharmacology (IUPHAR/BPS)** | Authoritative pharmacological data on drug targets: receptors, ion channels, enzymes, transporters. |
| **DGIdb** (Drug–Gene Interaction Database) | Mined and curated gene–drug interactions and druggability scores from multiple sources. |
| **Open Targets Genetics** | Genetic evidence linking variants to targets and disease; prioritizes drug targets from GWAS data. |
| **HGNC** (HUGO Gene Nomenclature Committee) | Approved gene symbols and nomenclature for human genes; avoids ambiguity in target identification. |

---

## 9. Safety, Toxicity & ADMET Databases

| Database | Description |
|---|---|
| **NLM Toxicology Data Network (formerly TOXNET)** | Collection of toxicology databases: HSDB, IRIS, ITER, CCRIS, GENE-TOX, and more. |
| **DSSTox** (Distributed Structure-Searchable Toxicity) | EPA curated, structure-annotated toxicity data; underpins CompTox Chemicals Dashboard. |
| **Tox21** | NIH/EPA/FDA program providing HTS toxicology data for ~10,000 environmental chemicals and drugs. |
| **ECHA REACH Dossiers** | Regulatory toxicology data submitted under EU REACH; comprehensive safety/ecotoxicology dossiers. |
| **ACToR** (Aggregated Computational Toxicology Resource) | EPA database aggregating chemical structures and in vitro/in vivo toxicity data. |
| **CTD** (Comparative Toxicogenomics Database) | Chemical–gene–disease relationship data; supports mechanistic toxicology investigations. |
| **DART Database** (Developmental/Reproductive Toxicology) | NLM curated bibliographic database for developmental and reproductive toxicology studies. |
| **hERG Database** | Curated hERG channel inhibition data; critical for cardiac safety (QT prolongation) assessment. |
| **FAERS** (FDA Adverse Event Reporting System) | Post-market adverse event and medication error reports submitted to FDA. |
| **ProTox-II** | Free web server for predicting oral toxicity, organ toxicity, and toxicity class of small molecules. |
| **pkCSM** | Pharmacokinetic and toxicity predictions: ADME, organ toxicity, hERG inhibition. |

---

## 10. Regulatory & Pharmacopoeia Databases

| Database | Description |
|---|---|
| **Drugs@FDA** | Complete history of FDA-approved drug products; NDA/ANDA approvals, labels, review documents. |
| **FDA Orange Book** | Therapeutic equivalence evaluations for approved solid oral dosage forms; patent and exclusivity listings. |
| **FDA Purple Book** | Licensed biological products (biosimilars, interchangeable biologics); reference product designations. |
| **EMA EPAR** (European Public Assessment Reports) | Scientific evaluation reports for EMA-approved medicines; clinical and quality dossier summaries. |
| **ICH Guidelines** (Q8–Q11) | International Council for Harmonisation guidelines: Q8 Pharmaceutical Development, Q9 Quality Risk Management, Q10 Pharmaceutical Quality System, Q11 Drug Substance Development. |
| **USP** (United States Pharmacopeia) | Official compendia for drug substances, excipients, dosage forms, and analytical methods in the US. |
| **European Pharmacopoeia (EP / Ph. Eur.)** | Official standards for medicinal substances and dosage forms in Europe. |
| **Japanese Pharmacopoeia (JP)** | Official Japanese pharmaceutical standards for drug substances and preparations. |
| **WHO International Pharmacopoeia** | Recommended quality specifications for priority medicines used in low/middle-income countries. |
| **FDA Guidance Documents** | Regulatory guidance for process validation, method validation, stability testing, and CMC submissions. |
| **EudraVigilance** | European database of adverse drug reaction reports for EMA-authorized medicines. |

---

## 11. Clinical Trial & Epidemiology Databases

| Database | Description |
|---|---|
| **ClinicalTrials.gov** | US NIH registry of publicly and privately funded clinical studies; protocol, eligibility, results data. |
| **WHO ICTRP** (International Clinical Trials Registry Platform) | Meta-registry linking 17 national and regional clinical trial registries worldwide. |
| **EU Clinical Trials Register** | EudraCT-based register of phase II–IV clinical trials conducted in the European Economic Area. |
| **AACT** (Aggregate Analysis of ClinicalTrials.gov) | Relational database mirror of ClinicalTrials.gov enabling large-scale analytics and SQL queries. |
| **FDA Sentinel** | Distributed database network of electronic health records and claims data for post-market safety surveillance. |
| **SEER** (Surveillance, Epidemiology, and End Results) | NCI cancer incidence, prevalence, and survival data by site, stage, demographics. |
| **Global Burden of Disease (GBD)** | IHME database of disease burden, mortality, and risk factors across 204 countries. |
| **TriNetX** | Real-world clinical data network for feasibility assessments and trial site identification. |

---

## 12. Literature & Patent Databases

| Database | Description |
|---|---|
| **PubMed / MEDLINE** | NLM index of 36M+ biomedical literature citations; primary literature source for scientific evidence. |
| **Embase** | Elsevier biomedical and pharmacological literature database; strong coverage of European and drug-related literature. |
| **ScienceDirect** | Full-text access to Elsevier journals and books; process chemistry, pharmaceutics, analytical science. |
| **CAS SciFinder (Literature)** | Chemical literature search with structure and reaction query capabilities across patents and journals. |
| **Reaxys (Literature)** | Reaction-focused literature mining across chemistry and pharmaceutical journals and patents. |
| **USPTO PatFT / Google Patents** | Full-text US patent search; synthesis routes, formulation patents, process innovations. |
| **EPO Espacenet** | European Patent Office database covering 120M+ patent documents from 100+ countries. |
| **Lens.org** | Open patent and scholarly literature search with analytics; integrates patents with citing literature. |
| **Europe PMC** | Open-access literature repository including preprints, grants, and patents linked to PubMed records. |

---

## 13. Manufacturing & Process Development References

| Database / Standard | Description |
|---|---|
| **FDA Process Validation Guidance (2011)** | Three-stage lifecycle approach (process design, qualification, continued verification) for drug product manufacturing. |
| **ICH Q8** (Pharmaceutical Development) | Framework for quality by design (QbD): design space, critical quality attributes (CQAs), and control strategy. |
| **ICH Q9** (Quality Risk Management) | Risk management tools (FMEA, HACCP, fault tree analysis) applied to pharmaceutical manufacturing. |
| **ICH Q10** (Pharmaceutical Quality System) | Lifecycle-based pharmaceutical quality system applicable across development and commercial manufacturing. |
| **ICH Q11** (Development and Manufacture of Drug Substances) | QbD principles for chemical and biotechnological drug substance development and scale-up. |
| **ICH Q12** (Technical and Regulatory Considerations for Post-Approval CMC Changes) | Framework for managing post-approval chemistry, manufacturing, and controls changes. |
| **ISPE PQLI Guides** | ISPE Product Quality Lifecycle Implementation guides; design space, control strategy, continuous improvement. |
| **FDA PAT Guidance** (Process Analytical Technology) | Regulatory framework for real-time monitoring and control of manufacturing processes. |
| **USP <1058> Analytical Instrument Qualification** | USP general chapter for qualification of analytical instruments used in pharmaceutical testing. |
| **ICH Q2(R1)** (Validation of Analytical Procedures) | Regulatory expectations for method validation: specificity, linearity, range, accuracy, precision, robustness. |
