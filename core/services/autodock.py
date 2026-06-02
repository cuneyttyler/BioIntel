"""
AutoDock Vina integration for virtual screening.

Prerequisites (must be installed on the server):
  - AutoDock Vina: `vina` executable in PATH
  - Open Babel: `obabel` executable in PATH

The run_screening() function is designed to be called from a background
thread so the HTTP request can return immediately with status=pending.
"""

import os
import shutil
import subprocess
import tempfile
import threading
from typing import Optional

import requests


def _is_tool_available(name: str) -> bool:
    return shutil.which(name) is not None


def prepare_receptor(pdb_id: str, binding_site: dict, work_dir: str) -> Optional[str]:
    """Download PDB, convert to PDBQT. Returns path or None on failure."""
    pdb_id = pdb_id.upper()
    pdb_url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    pdb_path = os.path.join(work_dir, f"{pdb_id}.pdb")
    pdbqt_path = os.path.join(work_dir, f"{pdb_id}_receptor.pdbqt")

    try:
        resp = requests.get(pdb_url, timeout=30)
        resp.raise_for_status()
        with open(pdb_path, "w") as f:
            f.write(resp.text)
    except Exception:
        return None

    if not _is_tool_available("obabel"):
        return None

    result = subprocess.run(
        ["obabel", pdb_path, "-O", pdbqt_path, "--partialcharge", "gasteiger", "-xr"],
        capture_output=True, timeout=60,
    )
    return pdbqt_path if result.returncode == 0 and os.path.exists(pdbqt_path) else None


def prepare_ligands(smiles_list: list[str], work_dir: str) -> list[tuple[str, str]]:
    """Convert SMILES to PDBQT files. Returns list of (smiles, pdbqt_path)."""
    if not _is_tool_available("obabel"):
        return []

    results = []
    for i, smi in enumerate(smiles_list):
        sdf_path = os.path.join(work_dir, f"lig_{i}.sdf")
        pdbqt_path = os.path.join(work_dir, f"lig_{i}.pdbqt")
        result = subprocess.run(
            ["obabel", f"-:{smi}", "-O", sdf_path, "--gen3d"],
            capture_output=True, timeout=30,
        )
        if result.returncode != 0 or not os.path.exists(sdf_path):
            continue
        result2 = subprocess.run(
            ["obabel", sdf_path, "-O", pdbqt_path, "--partialcharge", "gasteiger"],
            capture_output=True, timeout=30,
        )
        if result2.returncode == 0 and os.path.exists(pdbqt_path):
            results.append((smi, pdbqt_path))
    return results


def parse_results(output_pdbqt: str, smiles: str) -> Optional[float]:
    """Parse best binding affinity (kcal/mol) from Vina PDBQT output."""
    try:
        with open(output_pdbqt) as f:
            for line in f:
                if line.startswith("REMARK VINA RESULT"):
                    parts = line.split()
                    return float(parts[3])
    except Exception:
        pass
    return None


def run_docking(receptor_path: str, ligand_path: str, box_center: list, box_size: list, exhaustiveness: int = 4) -> Optional[float]:
    """Run a single Vina docking job. Returns best affinity or None."""
    if not _is_tool_available("vina"):
        return None

    work_dir = os.path.dirname(ligand_path)
    out_path = ligand_path.replace(".pdbqt", "_out.pdbqt")

    cx, cy, cz = box_center
    sx, sy, sz = box_size

    cmd = [
        "vina",
        "--receptor", receptor_path,
        "--ligand", ligand_path,
        "--out", out_path,
        "--center_x", str(cx), "--center_y", str(cy), "--center_z", str(cz),
        "--size_x", str(sx), "--size_y", str(sy), "--size_z", str(sz),
        "--exhaustiveness", str(exhaustiveness),
        "--num_modes", "1",
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=120)
    if result.returncode != 0 or not os.path.exists(out_path):
        return None
    return parse_results(out_path, "")


def run_screening(run_id: int, smiles_list: list[str], receptor_pdb_id: str, binding_site: dict) -> None:
    """
    Background thread entry point. Runs a full virtual screening job:
    - prepares receptor and ligands
    - docks each ligand
    - saves VirtualScreeningHit records for top results
    - updates VirtualScreeningRun status
    """
    from django.utils import timezone
    from core.models import VirtualScreeningRun, VirtualScreeningHit

    def _run():
        run = None
        try:
            run = VirtualScreeningRun.objects.get(pk=run_id)
            run.status = "running"
            run.save(update_fields=["status"])

            work_dir = tempfile.mkdtemp(prefix="vscreen_")
            try:
                box_center = binding_site.get("center", [0, 0, 0])
                box_size = binding_site.get("size", [20, 20, 20])

                receptor_path = prepare_receptor(receptor_pdb_id, binding_site, work_dir)
                if not receptor_path:
                    run.status = "failed"
                    run.error_message = "Failed to prepare receptor (check obabel installation)"
                    run.save(update_fields=["status", "error_message"])
                    return

                ligands = prepare_ligands(smiles_list, work_dir)
                hits = []
                for smiles, lig_path in ligands:
                    score = run_docking(receptor_path, lig_path, box_center, box_size)
                    if score is not None:
                        hits.append({"smiles": smiles, "score": score})

                # Sort by score (lower = better binding)
                hits.sort(key=lambda h: h["score"])
                top_hits = hits[:500]

                VirtualScreeningHit.objects.filter(run=run).delete()
                VirtualScreeningHit.objects.bulk_create([
                    VirtualScreeningHit(run=run, smiles=h["smiles"], docking_score=h["score"])
                    for h in top_hits
                ])

                run.status = "complete"
                run.result_count = len(top_hits)
                run.completed_at = timezone.now()
                run.save(update_fields=["status", "result_count", "completed_at"])
            finally:
                shutil.rmtree(work_dir, ignore_errors=True)

        except VirtualScreeningRun.DoesNotExist:
            pass
        except Exception as e:
            if run:
                run.status = "failed"
                run.error_message = str(e)[:500]
                run.save(update_fields=["status", "error_message"])

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
