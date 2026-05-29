import { defineStore } from 'pinia'
import { analogs as analogsApi, investigations as investApi, projects as projectsApi, compounds as compoundsApi, analogCandidates as analogCandidatesApi } from '@/services/api'

export const useAnalogsStore = defineStore('analogs', {
  state: () => ({
    investigation: null,
    referenceDrug: null,   // { chembl_id, name, smiles }
    threshold: 0.7,
    candidates: [],        // [{ smiles, cid, score, patentStatus, patentRefs, admet, shortlisted, id }]
    shortlisted: [],
    loading: {
      candidates: false,
      patents: false,
      admet: false,
    },
  }),

  actions: {
    setReference(drug) {
      this.referenceDrug = drug
      this.candidates = []
      this.shortlisted = []
    },

    async loadInvestigation(id) {
      try {
        this.investigation = await investApi.get(id)
        this.referenceDrug = {
          chembl_id: this.investigation.chembl_id,
          name: this.investigation.name,
          smiles: this.investigation.smiles,
        }
        const saved = await investApi.candidates(id)
        this.candidates = saved.filter(c => c.shortlisted).map(c => ({
          smiles: c.smiles,
          cid: c.pubchem_cid,
          score: c.similarity_score,
          patentStatus: c.patent_status,
          patentRefs: c.patent_refs,
          admet: c.admet_data,
          shortlisted: true,
          id: c.id,
        }))
        this.shortlisted = [...this.candidates]
      } catch (e) {
        console.error(e)
      }
    },

    async searchAnalogs() {
      if (!this.referenceDrug?.smiles) return
      this.loading.candidates = true
      // Snapshot existing candidates by SMILES so we can merge state after the search
      const existingMap = new Map(this.candidates.map(c => [c.smiles, c]))
      try {
        const results = await analogsApi.search(this.referenceDrug.smiles, this.threshold)
        const seen = new Set()
        const merged = results.map(r => {
          const smiles = r.smiles || ''
          seen.add(smiles)
          const existing = existingMap.get(smiles)
          return {
            smiles,
            cid: r.cid ?? existing?.cid,
            score: r.similarity_score || r.score || this.threshold,
            // Preserve enriched data from previous runs
            patentStatus: existing?.patentStatus || 'unknown',
            patentRefs: existing?.patentRefs || [],
            admet: existing?.admet || {},
            // Preserve shortlist state and DB id — prevents duplicates on save
            shortlisted: existing?.shortlisted ?? false,
            id: existing?.id ?? null,
          }
        })
        // Keep shortlisted candidates that the new search didn't return (e.g. threshold changed)
        for (const [smiles, c] of existingMap) {
          if (!seen.has(smiles) && c.shortlisted) merged.push(c)
        }
        this.candidates = merged
        this.shortlisted = this.candidates.filter(c => c.shortlisted)
      } catch (e) {
        console.error(e)
      } finally {
        this.loading.candidates = false
      }
    },

    async checkPatents() {
      if (!this.candidates.length) return
      this.loading.patents = true
      try {
        const candidates = this.candidates
          .filter(c => c.cid || c.smiles)
          .map(c => ({ cid: c.cid, smiles: c.smiles }))
        const results = await analogsApi.patentCheck(candidates)
        results.forEach(r => {
          const c = this.candidates.find(c => c.cid === r.cid || c.smiles === r.smiles)
          if (c) {
            c.patentStatus = r.patent_status
            c.patentRefs = r.patent_refs || []
          }
        })
      } catch (e) {
        console.error(e)
      } finally {
        this.loading.patents = false
      }
    },

    async runADMET() {
      const free = this.candidates.filter(c => c.patentStatus === 'free' && c.smiles)
      if (!free.length) return
      this.loading.admet = true
      try {
        const results = await analogsApi.admet(free.map(c => c.smiles))
        results.forEach(r => {
          const c = this.candidates.find(c => c.smiles === r.smiles)
          if (c) c.admet = r.admet || {}
        })
      } catch (e) {
        console.error(e)
      } finally {
        this.loading.admet = false
      }
    },

    toggleShortlist(candidate) {
      const idx = this.candidates.findIndex(c => c.smiles === candidate.smiles)
      if (idx !== -1) {
        this.candidates[idx].shortlisted = !this.candidates[idx].shortlisted
        this.shortlisted = this.candidates.filter(c => c.shortlisted)
      }
    },

    // Toggle shortlist and immediately persist the change (used in project mode)
    async toggleShortlistPersisted(candidate, projectId) {
      const idx = this.candidates.findIndex(c => c.smiles === candidate.smiles)
      if (idx === -1) return
      const isShortlisted = this.candidates[idx].shortlisted
      const candidateId = this.candidates[idx].id

      if (isShortlisted) {
        // Removing — drop from candidates entirely
        this.candidates.splice(idx, 1)
        this.shortlisted = this.candidates.filter(c => c.shortlisted)
        if (candidateId) {
          await analogCandidatesApi.update(candidateId, { shortlisted: false, project: null })
        }
      } else {
        // Adding to shortlist
        this.candidates[idx].shortlisted = true
        this.shortlisted = this.candidates.filter(c => c.shortlisted)
        if (candidateId) {
          await analogCandidatesApi.update(candidateId, { shortlisted: true, project: projectId })
        }
      }
    },

    /**
     * Save shortlisted analogs to a project and return the project.
     * Navigation is handled by the calling component.
     */
    async saveToProject({ projectId, projectName, compoundAction = 'replace' }) {
      let project
      if (projectId) {
        project = await projectsApi.get(projectId)
        if (compoundAction === 'replace') {
          const existing = await compoundsApi.list(projectId)
          if (existing?.length) {
            await Promise.all(existing.map(c => compoundsApi.delete?.(c.id).catch(() => {})))
          }
        }
      } else {
        project = await projectsApi.create({
          name: projectName,
          phase: 'preclinical',
          status: 'active',
          description: `Analog of ${this.referenceDrug?.name || 'reference drug'}`,
        })
      }

      // Ensure an investigation exists. In drug-search mode (coming from DrugProfilePage)
      // no investigation is created upfront — create one now so candidates can be persisted.
      let investigation = this.investigation
      if (!investigation && this.referenceDrug) {
        investigation = await investApi.create({
          chembl_id: this.referenceDrug.chembl_id || '',
          name: this.referenceDrug.name || 'Unknown',
          smiles: this.referenceDrug.smiles || '',
        })
        this.investigation = investigation
      }

      // Persist all shortlisted candidates that don't yet have a DB id
      if (investigation?.id) {
        for (const c of this.shortlisted) {
          if (!c.id) {
            try {
              const created = await investApi.addCandidate(investigation.id, {
                investigation: investigation.id,
                smiles: c.smiles,
                pubchem_cid: c.cid || null,
                similarity_score: c.score || 0,
                patent_status: c.patentStatus || 'unknown',
                patent_refs: c.patentRefs || [],
                admet_data: c.admet || {},
                shortlisted: true,
              })
              const idx = this.candidates.findIndex(x => x.smiles === c.smiles)
              if (idx !== -1) this.candidates[idx].id = created.id
            } catch (e) {
              console.error('Failed to save candidate', e)
            }
          }
        }
        await investApi.linkProject(investigation.id, project.id, true)
      }

      // Add first shortlisted analog as the project compound
      const candidate = this.shortlisted[0]
      if (candidate) {
        await compoundsApi.create({
          project: project.id,
          name: `Analog of ${this.referenceDrug?.name || 'reference'}`,
          smiles: candidate.smiles,
          pubchem_cid: candidate.cid || null,
          chembl_id: candidate.chembl_id || '',
        })
      }

      return project
    },

    // Save new shortlisted candidates (those without an id) in project mode
    async saveNewCandidatesToProject(projectId) {
      const invId = this.investigation?.id
      if (!invId) return
      const newOnes = this.candidates.filter(c => c.shortlisted && !c.id)
      for (const c of newOnes) {
        try {
          const created = await investApi.addCandidate(invId, {
            investigation: invId,
            smiles: c.smiles,
            pubchem_cid: c.cid || null,
            similarity_score: c.score || 0,
            patent_status: c.patentStatus || 'unknown',
            patent_refs: c.patentRefs || [],
            admet_data: c.admet || {},
            shortlisted: true,
          })
          // Assign the id so future patches work
          const idx = this.candidates.findIndex(x => x.smiles === c.smiles)
          if (idx !== -1) this.candidates[idx].id = created.id
        } catch (e) {
          console.error('Failed to save candidate', e)
        }
      }
      // Link all shortlisted to project
      await investApi.linkProject(invId, projectId, true)
    },
  },
})
