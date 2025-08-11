<template>
  <div class="wrap">
    <header class="bar">
      <strong>Melbourne Parking</strong>
      <span v-if="ts">Last fetch: {{ new Date(ts).toLocaleString() }}</span>
      <span v-if="count !== null"> · Bays: {{ count }}</span>
      <span v-if="err" class="err"> · {{ err }}</span>

      <form class="search" @submit.prevent="searchAddress">
        <div class="search-box" ref="searchBox" @keydown.stop>
          <span class="search-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
          </span>
          <input
            ref="searchInput"
            v-model="query"
            type="text"
            class="search-input pretty"
            placeholder="Search address in Melbourne..."
            @input="onInput"
            @focus="openDropdown"
            @keydown.down.prevent="moveActive(1)"
            @keydown.up.prevent="moveActive(-1)"
            @keydown.enter.prevent="confirmActive"
            @keydown.esc.prevent="hideDropdown"
          />
          <button v-if="query" type="button" class="clear-btn" @click="clearQuery">
            <svg viewBox="0 0 24 24" width="14" height="14"><path fill="currentColor" d="M18.3 5.71 12 12l6.3 6.29-1.41 1.42L10.59 13.41 4.3 19.71 2.89 18.3 9.17 12 2.89 5.71 4.3 4.29l6.29 6.3 6.29-6.3z"/></svg>
          </button>

          <div v-if="showDropdown" class="dropdown">
            <ul v-if="predictions.length">
              <li
                v-for="(p,i) in predictions"
                :key="p.place_id"
                :class="['item', { active: i === activeIndex }]"
                @mouseenter="activeIndex = i"
                @mousedown.prevent="selectPrediction(p)"
              >
                <span class="pin">
                  <svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M12 2C8.14 2 5 5.14 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.86-3.14-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5S10.62 6.5 12 6.5s2.5 1.12 2.5 2.5S13.38 11.5 12 11.5z"/></svg>
                </span>
                <div class="txt">
                  <div class="primary" v-html="formatPrimary(p)"></div>
                  <div class="secondary">{{ p.structured_formatting?.secondary_text || p.description }}</div>
                </div>
              </li>
            </ul>
            <div v-else class="empty">No suggestions</div>
            <div class="brand">
              <img src="https://developers.google.com/maps/documentation/places/web-service/images/powered-by-google-on-white.png" alt="Powered by Google">
            </div>
          </div>
        </div>

        <button class="search-btn" type="submit" :disabled="searching">
          {{ searching ? 'Searching...' : 'Search' }}
        </button>
      </form>

      <button class="loc-btn" @click="locateMe" :disabled="locating">{{ locating ? 'Locating...' : 'My location' }}</button>

      <label class="filter">
        <input type="checkbox" v-model="showOnlyFree" @change="rebuildClusterFromCache">
        Only show free
      </label>
    </header>

    <div ref="mapRef" class="map"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { MarkerClusterer } from '@googlemaps/markerclusterer'

const BACKEND = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'
const GOOGLE_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || ''
const DEFAULT_CENTER = { lat: -37.8136, lng: 144.9631 }
const DEFAULT_ZOOM = 16
const MEL_SW = { lat: -38.5, lng: 144.4 }
const MEL_NE = { lat: -37.4, lng: 145.7 }

const mapRef = ref(null)
const searchInput = ref(null)
const searchBox = ref(null)

let map = null
let clusterer = null
let geocoder = null
let placesSvc = null
let acSvc = null
let sessionToken = null
let searchMarker = null
let timer = null
let sinceISO = null
const ts = ref(null)
const count = ref(null)
const err = ref(null)
const showOnlyFree = ref(false)
const query = ref('')
const searching = ref(false)

const markersById = new Map()
let sharedIW = null
let idleTimer = null
let inflightController = null
let lastViewportKey = null
let userMarker = null
const locating = ref(false)

const predictions = ref([])
const showDropdown = ref(false)
const activeIndex = ref(-1)
let debounceId = null

function viewportKey() {
  const b = map.getBounds()
  if (!b) return ''
  const c = map.getCenter()
  const z = map.getZoom()
  return [
    c ? c.lat().toFixed(4) : '0',
    c ? c.lng().toFixed(4) : '0',
    Math.round(z || 0),
    ...(() => {
      const sw = b.getSouthWest(), ne = b.getNorthEast()
      return [sw.lat().toFixed(4), sw.lng().toFixed(4), ne.lat().toFixed(4), ne.lng().toFixed(4)]
    })()
  ].join('|')
}

function loadGoogle () {
  return new Promise((resolve, reject) => {
    if (window.google?.maps) return resolve()
    const s = document.createElement('script')
    s.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(GOOGLE_KEY)}&libraries=places&v=weekly`
    s.async = true; s.defer = true
    s.onload = resolve
    s.onerror = () => reject(new Error('Google Maps JS failed'))
    document.head.appendChild(s)
  })
}

function getUserCenter() {
  return new Promise(resolve => {
    if (!navigator.geolocation) return resolve(DEFAULT_CENTER)
    navigator.geolocation.getCurrentPosition(
      pos => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => resolve(DEFAULT_CENTER),
      { enableHighAccuracy: false, timeout: 3000, maximumAge: 60000 }
    )
  })
}

function initMap (center = DEFAULT_CENTER, zoom = DEFAULT_ZOOM) {
  map = new google.maps.Map(mapRef.value, {
    center,
    zoom,
    mapTypeControl: false,
    streetViewControl: false
  })
  sharedIW = new google.maps.InfoWindow()
  geocoder = new google.maps.Geocoder()
  placesSvc = new google.maps.places.PlacesService(map)
  acSvc = new google.maps.places.AutocompleteService()
  newSession()

  userMarker = new google.maps.Marker({
    position: center,
    map,
    icon: {
      path: google.maps.SymbolPath.CIRCLE,
      scale: 6,
      fillColor: '#3b82f6',
      fillOpacity: 1,
      strokeWeight: 2,
      strokeColor: '#1d4ed8'
    },
    zIndex: 9999
  })

  map.addListener('idle', () => {
    if (idleTimer) clearTimeout(idleTimer)
    idleTimer = setTimeout(async () => {
      const key = viewportKey()
      if (key !== lastViewportKey) {
        lastViewportKey = key
        await refresh(true)
      }
    }, 400)
  })
}

function newSession() {
  sessionToken = new google.maps.places.AutocompleteSessionToken()
}

function boundsObj() {
  const b = new google.maps.LatLngBounds(MEL_SW, MEL_NE)
  return {
    south: b.getSouthWest().lat(),
    west: b.getSouthWest().lng(),
    north: b.getNorthEast().lat(),
    east: b.getNorthEast().lng()
  }
}

function onInput() {
  if (!query.value.trim()) {
    predictions.value = []
    showDropdown.value = false
    activeIndex.value = -1
    return
  }
  if (debounceId) clearTimeout(debounceId)
  debounceId = setTimeout(fetchPredictions, 150)
}

function openDropdown() {
  if (predictions.value.length) showDropdown.value = true
}

function hideDropdown() {
  showDropdown.value = false
  activeIndex.value = -1
}

function moveActive(delta) {
  if (!predictions.value.length) return
  showDropdown.value = true
  const n = predictions.value.length
  activeIndex.value = (activeIndex.value + delta + n) % n
  scrollActiveIntoView()
}

function confirmActive() {
  if (activeIndex.value >= 0 && activeIndex.value < predictions.value.length) {
    selectPrediction(predictions.value[activeIndex.value])
  } else {
    searchAddress()
  }
}

function scrollActiveIntoView() {
  const list = searchBox.value?.querySelector('.dropdown ul')
  const li = list?.children?.[activeIndex.value]
  if (li && li.scrollIntoView) li.scrollIntoView({ block: 'nearest' })
}

function fetchPredictions() {
  const input = query.value.trim()
  if (!input) return
  const req = {
    input,
    sessionToken,
    componentRestrictions: { country: 'au' },
    bounds: new google.maps.LatLngBounds(MEL_SW, MEL_NE),
    types: []
  }
  acSvc.getPlacePredictions(req, (res, status) => {
    if (status !== google.maps.places.PlacesServiceStatus.OK || !res) {
      predictions.value = []
      showDropdown.value = false
      activeIndex.value = -1
      return
    }
    predictions.value = res
    activeIndex.value = -1
    showDropdown.value = true
  })
}

function selectPrediction(p) {
  placesSvc.getDetails(
    { placeId: p.place_id, fields: ['geometry.location', 'formatted_address', 'name'], sessionToken },
    async (place, status) => {
      if (status !== google.maps.places.PlacesServiceStatus.OK || !place?.geometry?.location) return
      const loc = place.geometry.location
      const latlng = { lat: loc.lat(), lng: loc.lng() }
      query.value = place.formatted_address || p.description
      hideDropdown()
      newSession()
      await moveToAndRefresh(latlng)
      dropOrMoveSearchMarker(latlng)
    }
  )
}

function clearQuery() {
  query.value = ''
  predictions.value = []
  hideDropdown()
  searchInput.value?.focus()
}

function formatPrimary(p) {
  const sf = p.structured_formatting
  if (!sf) return p.description
  let text = sf.main_text
  if (sf.main_text_matched_substrings?.length) {
    const [{ offset, length }] = sf.main_text_matched_substrings
    const a = text.slice(0, offset)
    const b = text.slice(offset, offset + length)
    const c = text.slice(offset + length)
    return `${a}<strong>${b}</strong>${c}`
  }
  return text
}

function dropOrMoveSearchMarker(latlng) {
  if (!searchMarker) {
    searchMarker = new google.maps.Marker({
      position: latlng,
      map,
      icon: { path: google.maps.SymbolPath.BACKWARD_CLOSED_ARROW, scale: 5 },
      zIndex: 9998
    })
  } else {
    searchMarker.setPosition(latlng)
    searchMarker.setMap(map)
  }
}

function getBBoxParam() {
  const b = map.getBounds()
  if (!b) return null
  const sw = b.getSouthWest()
  const ne = b.getNorthEast()
  return `${sw.lat()},${sw.lng()},${ne.lat()},${ne.lng()}`
}

function thinningParams() {
  const z = map.getZoom() || 12
  if (z <= 13) return { max_points: 1500, cell: 0.0012 }
  if (z <= 15) return { max_points: 2500, cell: 0.0010 }
  if (z <= 17) return { max_points: 3500, cell: 0.0008 }
  return { max_points: 6000, cell: 0.0006 }
}

async function fetchFromBackend(useBBox) {
  if (inflightController) inflightController.abort()
  inflightController = new AbortController()
  const url = new URL(`${BACKEND}/api/bays`)
  if (sinceISO) url.searchParams.set('since', sinceISO)
  if (useBBox) {
    const bbox = getBBoxParam()
    if (bbox) url.searchParams.set('bbox', bbox)
  }
  const { max_points, cell } = thinningParams()
  url.searchParams.set('max_points', max_points)
  url.searchParams.set('cell', cell)
  const res = await fetch(url.toString(), { signal: inflightController.signal })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const json = await res.json()
  sinceISO = json.next_since || sinceISO
  return json.records
}

function buildIcon(free) {
  return {
    path: google.maps.SymbolPath.CIRCLE,
    scale: 5,
    fillColor: free ? '#22c55e' : '#ef4444',
    fillOpacity: 1,
    strokeWeight: 0
  }
}

async function diffAndApply(records) {
  const incomingIds = new Set()
  for (const r of records) {
    incomingIds.add(r.id)
    const status = (r.status || '')
    const free = status.includes('unoccupied') || status.includes('vacant')
    const existing = markersById.get(r.id)
    if (existing) {
      if (existing._status !== status) {
        existing.setIcon(buildIcon(free))
        existing._status = status
      }
      existing._free = free
      existing._last = r.lastupdated
      if (!existing.getMap()) existing.setMap(map)
    } else {
      const m = new google.maps.Marker({
        position: { lat: r.lat, lng: r.lon },
        icon: buildIcon(free),
        optimized: true
      })
      m._status = status
      m._last = r.lastupdated
      m._free = free
      m.addListener('click', () => {
        const html = `<div style="font:12px system-ui">
          <b>ID:</b> ${r.id}<br>
          <b>Status:</b> ${m._free ? 'Unoccupied' : 'Occupied'}<br>
          <b>Last:</b> ${r.lastupdated ?? '-'}
        </div>`
        sharedIW.setContent(html)
        sharedIW.open({ anchor: m, map })
      })
      markersById.set(r.id, m)
    }
  }
  for (const [id, m] of markersById) {
    if (!incomingIds.has(id)) {
      markersById.delete(id)
      m.setMap(null)
    }
  }
  rebuildClusterFromCache()
}

function rebuildClusterFromCache() {
  const toShow = Array.from(markersById.values()).filter(m => !showOnlyFree.value || m._free)
  if (clusterer) clusterer.setMap(null)
  clusterer = new MarkerClusterer({ map, markers: toShow })
  count.value = toShow.length
}

async function refresh(useBBox = false) {
  try {
    err.value = null
    const rows = await fetchFromBackend(useBBox)
    await diffAndApply(rows)
    ts.value = Date.now()
  } catch (e) {
    if (e.name === 'AbortError') return
    err.value = e.message
  }
}

async function locateMe() {
  locating.value = true
  try {
    const pos = await getUserCenter()
    await moveToAndRefresh(pos)
  } finally {
    locating.value = false
  }
}

async function moveToAndRefresh(latlng) {
  map.panTo(latlng)
  if ((map.getZoom() || 0) < DEFAULT_ZOOM) map.setZoom(DEFAULT_ZOOM)
  if (userMarker) userMarker.setPosition(latlng)
  sinceISO = null
  await refresh(true)
}

async function searchAddress() {
  const q = String(query.value || '').trim()
  if (!q) return
  searching.value = true
  err.value = null
  try {
    const bounds = new google.maps.LatLngBounds(MEL_SW, MEL_NE)
    if (!geocoder) geocoder = new google.maps.Geocoder()
    const { results } = await geocoder.geocode({
      address: q,
      bounds,
      region: 'AU',
      componentRestrictions: { country: 'AU' }
    })
    if (!results || results.length === 0) { err.value = 'No results'; return }
    const loc = results[0].geometry.location
    const latlng = { lat: loc.lat(), lng: loc.lng() }
    await moveToAndRefresh(latlng)
    dropOrMoveSearchMarker(latlng)
  } catch (e) {
    err.value = e.message || 'Search failed'
  } finally {
    searching.value = false
    newSession()
  }
}

function onDocClick(e) {
  if (!searchBox.value) return
  if (!searchBox.value.contains(e.target)) hideDropdown()
}

onMounted(async () => {
  await loadGoogle()
  const center = await getUserCenter()
  initMap(center, DEFAULT_ZOOM)
  await refresh(true)
  timer = setInterval(() => refresh(true), 2 * 60 * 1000)
  document.addEventListener('click', onDocClick)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  if (idleTimer) clearTimeout(idleTimer)
  if (inflightController) inflightController.abort()
  document.removeEventListener('click', onDocClick)
})
</script>

<style scoped>
.wrap { height: 100vh; display: flex; flex-direction: column; position: relative; }
.bar { padding: 8px 12px; border-bottom: 1px solid #e5e7eb; font: 13px/1.2 system-ui; color: #374151; display: flex; gap: 12px; align-items: center; }
.bar .err { color: #ef4444; }
.search { display: inline-flex; gap: 6px; align-items: center; margin-left: 12px; position: relative; }
.search-box { position: relative; min-width: 420px; }
.search-input.pretty { height: 36px; padding: 0 34px 0 34px; border: 1px solid #e5e7eb; border-radius: 8px; outline: none; width: 100%; font: 13px system-ui; }
.search-input.pretty:focus { border-color: #cbd5e1; box-shadow: 0 0 0 3px rgba(59,130,246,.15); }
.search-icon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: #6b7280; display: inline-flex; }
.clear-btn { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); border: 0; background: transparent; color: #9ca3af; cursor: pointer; padding: 4px; }
.clear-btn:hover { color: #6b7280; }
.dropdown { position: absolute; left: 0; right: 0; top: calc(100% + 6px); background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; box-shadow: 0 12px 30px rgba(0,0,0,.12); overflow: hidden; z-index: 10001; }
.dropdown ul { list-style: none; margin: 0; padding: 6px 0; max-height: 320px; overflow: auto; }
.dropdown .item { display: flex; gap: 10px; align-items: start; padding: 10px 12px; cursor: pointer; }
.dropdown .item:hover, .dropdown .item.active { background: #f8fafc; }
.dropdown .pin { color: #64748b; margin-top: 2px; }
.dropdown .txt { line-height: 1.1; }
.dropdown .primary { font-weight: 600; color: #111827; }
.dropdown .primary strong { color: #2563eb; }
.dropdown .secondary { margin-top: 2px; font-size: 12px; color: #6b7280; }
.dropdown .empty { padding: 14px; font: 12px system-ui; color: #6b7280; }
.dropdown .brand { border-top: 1px solid #f1f5f9; padding: 6px 10px; display: flex; justify-content: flex-end; }
.dropdown .brand img { height: 14px; }
.search-btn { height: 36px; padding: 0 12px; border: 1px solid #e5e7eb; background: #fff; border-radius: 8px; cursor: pointer; }
.loc-btn { margin-left: auto; background: #fff; border: 1px solid #e5e7eb; border-radius: 9999px; padding: 6px 12px; height: 32px; font: 13px system-ui; box-shadow: 0 2px 8px rgba(0,0,0,.08); cursor: pointer; }
.loc-btn:disabled { opacity: .6; cursor: default; }
.filter { display: inline-flex; align-items: center; gap: 6px; }
.map  { flex: 1; width: 100%; }
</style>
