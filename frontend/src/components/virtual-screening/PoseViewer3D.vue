<script setup>
defineProps({
  pdbId: { type: String, default: null },
  hitSmiles: { type: String, default: null },
})
</script>

<template>
  <div style="background:#1e1e2e;border-radius:8px;padding:24px;text-align:center;color:#a5b4fc;min-height:180px;display:flex;flex-direction:column;align-items:center;justify-content:center">
    <div style="font-size:32px;margin-bottom:8px">⚗️</div>
    <p style="margin:0;font-size:14px">3D Pose Viewer</p>
    <p style="margin:4px 0 0;font-size:12px;opacity:0.7">
      {{ pdbId ? `PDB: ${pdbId}` : 'No structure loaded' }}
    </p>
    <p style="margin:4px 0 0;font-size:11px;opacity:0.5">Requires NGL Viewer or 3Dmol.js integration</p>
  </div>
</template>
