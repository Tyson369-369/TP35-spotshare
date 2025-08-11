<template>
  <section class="page">
    <h1>Find a Bay</h1>
    <p class="sub">Search by KerbsideID to see the chance of finding a park each hour (next 12 hours).</p>

    <div class="row">
      <input v-model="kerb" placeholder="e.g. 41006" @keyup.enter="search"/>
      <button @click="search">Search</button>
      <select v-model.number="horizon">
        <option :value="6">Next 6h</option>
        <option :value="12">Next 12h</option>
        <option :value="24">Next 24h</option>
      </select>
    </div>

    <p v-if="loading" class="hint">Loading…</p>
    <p v-if="error" class="warn">{{ error }}</p>

    <article v-if="rows.length" class="card">
      <header class="head">
        <strong>Bay {{ selectedId }}</strong>
        <small :class="confClass">{{ confLabel }}</small>
      </header>

      <div class="stats">
        <span class="chip">Expected chance: <b>{{ expectedPct }}%</b></span>
        <span class="chip" v-if="best">Best time: <b>{{ best.time }}</b> ({{ best.pct }}%)</span>
        <span class="chip warn" v-if="coverage < 0.4">Limited history — results may be off</span>
      </div>

      <table class="list">
        <thead><tr><th>Time</th><th>Chance</th></tr></thead>
        <tbody>
          <tr v-for="r in rows" :key="r.iso">
            <td>{{ r.time }}</td>
            <td>{{ r.pct === null ? 'No data' : r.pct + '%' }}</td>
          </tr>
        </tbody>
      </table>
    </article>

    <p v-else-if="selectedId && !loading" class="hint">No upcoming points for that bay in this window.</p>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'

const API_BASE = 'http://localhost:8001' // change if needed
const URL = `${API_BASE}/web_data/bay_forecasts.json`

const kerb = ref('')
const selectedId = ref('')
const horizon = ref(12)
const all = ref(null)
const loading = ref(false)
const error = ref('')

async function ensureData() {
  if (all.value) return
  loading.value = true
  try {
    const r = await fetch(URL, { cache: 'no-store' })
    all.value = await r.json()
  } catch {
    error.value = 'Could not load forecast data.'
  } finally {
    loading.value = false
  }
}

async function search() {
  error.value = ''
  await ensureData()
  const id = kerb.value.trim()
  if (!id || !all.value?.bays) return
  if (!all.value.bays[id]) {
    selectedId.value = id
    rows.value = []
    error.value = 'No forecast for that KerbsideID.'
    return
  }
  selectedId.value = id
}

const windowed = computed(() => {
  const list = all.value?.bays?.[selectedId.value] || []
  const now = Date.now()
  const cutoff = now + horizon.value * 3600 * 1000
  return list
    .map(p => ({ ...p, t: new Date(p.timeISO).getTime() }))
    .filter(p => p.t <= cutoff)
    .sort((a, b) => a.t - b.t)
})

const rows = computed(() =>
  windowed.value.map(p => ({
    iso: p.timeISO,
    time: new Date(p.t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    pct: p.prob == null ? null : Math.round(p.prob * 100)
  }))
)

const coverage = computed(() => rows.value.length
  ? rows.value.filter(r => r.pct !== null).length / rows.value.length
  : 0)

const confLabel = computed(() =>
  coverage.value >= 0.7 ? 'High confidence'
  : coverage.value >= 0.4 ? 'Medium confidence'
  : 'Low confidence'
)

const confClass = computed(() =>
  coverage.value >= 0.7 ? 'badge good'
  : coverage.value >= 0.4 ? 'badge ok'
  : 'badge warn'
)

const expectedPct = computed(() => {
  if (!rows.value.length) return 0
  const sum = rows.value.reduce((a, r) => a + (r.pct ?? 0), 0)
  return Math.round(sum / rows.value.length)
})

const best = computed(() => {
  const known = rows.value.filter(r => r.pct !== null)
  if (!known.length) return null
  return known.reduce((a, b) => (a.pct >= b.pct ? a : b))
})
</script>

<style scoped>
.page { max-width: 900px; margin: 0 auto; padding: 28px 16px; }
.sub { color: #6b7280; margin: 4px 0 12px; }
.row { display: flex; gap: 8px; align-items: center; margin-bottom: 14px; }
.row input { flex: 1; padding: 10px 12px; border: 1px solid #e5e7eb; border-radius: 10px; }
.row button { padding: 10px 14px; border-radius: 10px; border: 0; background: #0ea5e9; color: #fff; cursor: pointer; }
.row select { padding: 10px 12px; border-radius: 10px; border: 1px solid #e5e7eb; }

.card { border: 1px solid #e5e7eb; border-radius: 16px; padding: 14px; background: #fff; }
.head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.badge { padding: 2px 8px; border-radius: 999px; font-size: 12px; border: 1px solid transparent; }
.badge.good { background: #ecfdf5; color: #047857; border-color: #a7f3d0; }
.badge.ok   { background: #fffbeb; color: #92400e; border-color: #fde68a; }
.badge.warn { background: #fef2f2; color: #b91c1c; border-color: #fecaca; }

.stats { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.chip { font-size: 12px; padding: 4px 8px; border-radius: 999px; background: #f3f4f6; color: #374151; }
.chip.warn { background: #fff1f2; color: #9f1239; }

.list { width: 100%; border-collapse: collapse; }
.list th, .list td { padding: 8px 10px; border-bottom: 1px solid #f1f5f9; text-align: left; }
.hint { color: #6b7280; }
.warn { color: #b91c1c; }
</style>
