<!-- src/components/ParkingMap.vue-->
<template>
  <div class="parking-map">
    <h2 class="map-heading">
      <img src="@/assets/direction-icon.png" alt="Direction Icon" class="icon" />
      Live Parking Map
    </h2>

    <p>Melbourne CBD · Updated every 30s</p>

    <!-- Map container -->
    <div ref="mapRef" class="map-container"></div>
  </div>
</template>

<script setup>
import { onMounted, ref, onBeforeUnmount } from 'vue'
import { MarkerClusterer } from '@googlemaps/markerclusterer'

const mapRef = ref(null)
let map = null
let markerCluster = null
let refreshTimer = null

// API config
const API_BASE =
  'https://data.melbourne.vic.gov.au/api/explore/v2.1/catalog/datasets/on-street-parking-bay-sensors/records'
const BATCH_SIZE = 20 // load 200 points per batch
let offset = 0

// Initialize the Google Map
const initMap = () => {
  map = new google.maps.Map(mapRef.value, {
    center: { lat: -37.8136, lng: 144.9631 },
    zoom: 15,
  })

  // Load first batch immediately
  fetchParkingData()

  // Refresh every 30 seconds
  refreshTimer = setInterval(() => {
    offset = 0
    if (markerCluster) {
      markerCluster.clearMarkers()
    }
    fetchParkingData()
  }, 30000)
}

// Fetch parking data in batches
const fetchParkingData = async () => {
  try {
    const url = `${API_BASE}?limit=${BATCH_SIZE}&offset=${offset}`
    const response = await fetch(url)
    const data = await response.json()
    const records = data.results || []

    const newMarkers = records
      .filter((spot) => spot.location && spot.location.lat && spot.location.lon)
      .map((spot) => {
        const marker = new google.maps.Marker({
          position: {
            lat: spot.location.lat,
            lng: spot.location.lon,
          },
          title: `Status: ${spot.status_description}`,
          icon: {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 5,
            fillColor:
              spot.status_description === 'Unoccupied' ? 'green' : 'red',
            fillOpacity: 1,
            strokeWeight: 0,
          },
        })

        const infoWindow = new google.maps.InfoWindow({
          content: `
            <div>
              <strong>Status:</strong> ${spot.status_description}<br/>
              <strong>Zone:</strong> ${spot.zone_number}<br/>
              <strong>ID:</strong> ${spot.kerbsideid}<br/>
              <strong>Last updated:</strong> ${spot.lastupdated}
            </div>
          `,
        })

        marker.addListener('click', () => {
          infoWindow.open(map, marker)
        })

        return marker
      })

    if (!markerCluster) {
      markerCluster = new MarkerClusterer({ markers: newMarkers, map })
    } else {
      markerCluster.addMarkers(newMarkers)
    }

    // Load next batch if more data available
    offset += BATCH_SIZE
    if (records.length === BATCH_SIZE) {
      setTimeout(fetchParkingData, 200) // slight delay to avoid blocking UI
    }
  } catch (error) {
    console.error('Error fetching parking data:', error)
  }
}

onMounted(() => {
  if (typeof google !== 'undefined') {
    initMap()
  } else {
    const script = document.createElement('script')
    script.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyAa9l6c33RjLRQWkazpGuvY7pFct5AfLo8`
    script.async = true
    script.defer = true
    script.onload = initMap
    document.head.appendChild(script)
  }
})

onBeforeUnmount(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.map-heading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.5rem;
}

.icon {
  height: 24px;
  width: 24px;
}

.parking-map {
  font-family: 'Segoe UI', sans-serif;
}

.map-container {
  margin-top: 1rem;
  height: 500px;
  background-color: #eaf2f8;
  border-radius: 8px;
}
</style>
