"""
Serialize a project's current BioIntel data into a plain-text block
that can be injected into AI plan/recommendation prompts.

Only non-empty fields are included so the AI isn't confused by nulls.
"""

from __future__ import annotations


def _line(label: str, value) -> str | None:
    if value is None or value == '' or value == [] or value == {}:
        return None
    return f"  {label}: {value}"


def build_project_context(project_id: int) -> str:
    """Return a structured text summary of the project's current data."""
    from core.models import (
        Project, AnalogCandidate, SAREntry,
        AnalyticalMethod, PreclinicalStudy,
    )

    try:
        project = Project.objects.prefetch_related(
            'investigations', 'compounds', 'formulation_plans__components',
            'salt_screens', 'stability_plans', 'synthesis_plans',
            'analytical_methods', 'preclinical_studies',
        ).get(id=project_id)
    except Project.DoesNotExist:
        return ''

    sections: list[str] = []

    # ── Project basics ────────────────────────────────────────────────────────
    proj_lines = [
        f"  Name: {project.name}",
        f"  Pathway: {project.get_pathway_display()}",
        f"  Molecule type: {project.get_molecule_type_display()}",
        f"  Current phase: {project.get_phase_display()}",
    ]
    if project.description:
        proj_lines.append(f"  Description: {project.description}")
    sections.append("### Project\n" + "\n".join(proj_lines))

    # ── Target Product Profile ────────────────────────────────────────────────
    tpp = project.tpp_data or {}
    tpp_lines = [f"  {k}: {v}" for k, v in tpp.items() if v not in (None, '', [], {})]
    if tpp_lines:
        sections.append("### Target Product Profile (TPP)\n" + "\n".join(tpp_lines))

    # ── Drug Investigation (reference drug) ──────────────────────────────────
    investigations = list(project.investigations.all())
    if investigations:
        inv_lines = []
        for inv in investigations:
            parts = [inv.name]
            if inv.chembl_id:
                parts.append(f"ChEMBL: {inv.chembl_id}")
            if inv.smiles:
                parts.append(f"SMILES: {inv.smiles}")
            if inv.disease_name:
                parts.append(f"disease: {inv.disease_name}")
            if inv.notes:
                parts.append(f"notes: {inv.notes}")
            inv_lines.append("  - " + ", ".join(parts))
        sections.append("### Reference Drug Investigations\n" + "\n".join(inv_lines))

    # ── Analog Candidates ─────────────────────────────────────────────────────
    candidates = list(
        AnalogCandidate.objects.filter(project=project)
        .order_by('-similarity_score')[:15]
    )
    if candidates:
        cand_lines = []
        for c in candidates:
            tags = []
            if c.similarity_score:
                tags.append(f"sim={c.similarity_score:.2f}")
            if c.patent_status:
                tags.append(f"patent={c.patent_status}")
            if c.shortlisted:
                tags.append("shortlisted")
            if c.selected:
                tags.append("SELECTED")
            smiles_repr = c.smiles[:50] + ("…" if len(c.smiles) > 50 else "")
            line = f"  - {smiles_repr}"
            if tags:
                line += f" ({', '.join(tags)})"
            if c.notes:
                line += f" — {c.notes}"
            cand_lines.append(line)
        sections.append("### Analog Candidates\n" + "\n".join(cand_lines))

    # ── Compounds ─────────────────────────────────────────────────────────────
    compounds = list(project.compounds.all()[:10])
    if compounds:
        comp_lines = []
        for comp in compounds:
            parts = [comp.name]
            if comp.molecular_weight:
                parts.append(f"MW={comp.molecular_weight:.1f}")
            if comp.molecular_formula:
                parts.append(comp.molecular_formula)
            if comp.smiles:
                parts.append(f"SMILES: {comp.smiles[:50]}")
            comp_lines.append("  - " + ", ".join(parts))
        sections.append("### Compounds\n" + "\n".join(comp_lines))

    # ── SAR Entries ───────────────────────────────────────────────────────────
    sar_entries = list(
        SAREntry.objects.filter(project=project).order_by('-created_at')[:20]
    )
    if sar_entries:
        sar_lines = []
        for e in sar_entries:
            parts = []
            if e.r_group:
                parts.append(f"R-group: {e.r_group}")
            if e.activity_value is not None:
                parts.append(f"{e.activity_type}: {e.activity_value} {e.activity_unit}")
            if e.logp is not None:
                parts.append(f"logP={e.logp}")
            if e.mw is not None:
                parts.append(f"MW={e.mw}")
            if e.selectivity_value is not None:
                parts.append(f"selectivity vs {e.selectivity_target}: {e.selectivity_value}")
            if e.notes:
                parts.append(e.notes)
            sar_lines.append("  - " + ", ".join(parts) if parts else f"  - {e.smiles[:40]}")
        sections.append("### SAR Tracker\n" + "\n".join(sar_lines))

    # ── Salt / Polymorph Screens ──────────────────────────────────────────────
    salt_screens = list(project.salt_screens.prefetch_related('candidates').all())
    if salt_screens:
        ss_lines = []
        for ss in salt_screens:
            ss_lines.append(f"  - Type: {ss.screen_type}, Status: {ss.status}")
            if ss.baseline_pka is not None:
                ss_lines.append(f"    pKa: {ss.baseline_pka}")
            if ss.baseline_logp is not None:
                ss_lines.append(f"    logP: {ss.baseline_logp}")
            if ss.baseline_solubility_mgml is not None:
                ss_lines.append(f"    Solubility: {ss.baseline_solubility_mgml} mg/mL")
            if ss.baseline_melting_point_c is not None:
                ss_lines.append(f"    Melting point: {ss.baseline_melting_point_c} °C")
            if ss.selected_form:
                ss_lines.append(f"    Selected form: {ss.selected_form} — {ss.selection_rationale}")
            candidates = list(ss.candidates.filter(selected=True))
            if candidates:
                ss_lines.append(f"    Selected candidates: {', '.join(c.name for c in candidates)}")
        sections.append("### Salt / Polymorph Screens\n" + "\n".join(ss_lines))

    # ── Synthesis Plans ───────────────────────────────────────────────────────
    synthesis_plans = list(project.synthesis_plans.all()[:10])
    if synthesis_plans:
        synth_lines = []
        for sp in synthesis_plans:
            synth_lines.append(
                f"  - Target: {sp.target_smiles[:50]}, Type: {sp.plan_type}, Status: {sp.status}"
            )
        sections.append("### Synthesis Plans\n" + "\n".join(synth_lines))

    # ── Formulation Plans ─────────────────────────────────────────────────────
    formulation_plans = list(project.formulation_plans.prefetch_related('components').all())
    if formulation_plans:
        fp_lines = []
        for fp in formulation_plans:
            fp_lines.append(
                f"  - Form: {fp.dosage_form}, Route: {fp.route_of_administration}, "
                f"Status: {fp.status}"
            )
            if fp.target_dose_mg is not None:
                fp_lines.append(f"    Target dose: {fp.target_dose_mg} mg")
            if fp.release_type:
                fp_lines.append(f"    Release: {fp.release_type}")
            if fp.manufacturing_process:
                fp_lines.append(f"    Manufacturing: {fp.manufacturing_process}")
            if fp.rationale:
                fp_lines.append(f"    Rationale: {fp.rationale}")
            comps = list(fp.components.all())
            if comps:
                fp_lines.append(
                    f"    Components: {', '.join(f'{c.name} ({c.component_type})' for c in comps)}"
                )
        sections.append("### Formulation Plans\n" + "\n".join(fp_lines))

    # ── Stability Plans ───────────────────────────────────────────────────────
    stability_plans = list(project.stability_plans.all())
    if stability_plans:
        stab_lines = []
        for sp in stability_plans:
            stab_lines.append(f"  - Material: {sp.material_type}, Status: {sp.status}")
            if sp.intended_storage_condition:
                stab_lines.append(f"    Storage: {sp.intended_storage_condition}")
        sections.append("### Stability Plans\n" + "\n".join(stab_lines))

    # ── Analytical Methods ────────────────────────────────────────────────────
    analytical_methods = list(project.analytical_methods.all()[:15])
    if analytical_methods:
        am_lines = []
        for am in analytical_methods:
            am_lines.append(
                f"  - {am.method_name} ({am.method_type}), "
                f"analyte: {am.analyte or 'N/A'}, validation: {am.validation_status}"
            )
        sections.append("### Analytical Methods\n" + "\n".join(am_lines))

    # ── Preclinical Studies ───────────────────────────────────────────────────
    preclinical_studies = list(project.preclinical_studies.all()[:10])
    if preclinical_studies:
        pc_lines = []
        for ps in preclinical_studies:
            pc_lines.append(
                f"  - {ps.study_type}: species={ps.species or 'TBD'}, "
                f"route={ps.dose_route or 'TBD'}, status={ps.status}"
            )
            if ps.noael_mgkg is not None:
                pc_lines.append(f"    NOAEL: {ps.noael_mgkg} mg/kg")
            if ps.mtd_mgkg is not None:
                pc_lines.append(f"    MTD: {ps.mtd_mgkg} mg/kg")
            if ps.results_summary:
                pc_lines.append(f"    Results: {ps.results_summary}")
        sections.append("### Preclinical Studies\n" + "\n".join(pc_lines))

    if not sections:
        return ''

    header = (
        "The following is the current state of this project in BioIntel. "
        "Your recommendation must reference these actual project values — "
        "not generic pharmaceutical examples. "
        "If a field that your recommendation depends on is missing or empty, "
        "tell the scientist exactly what data they need to enter first.\n\n"
    )
    return header + "\n\n".join(sections)
