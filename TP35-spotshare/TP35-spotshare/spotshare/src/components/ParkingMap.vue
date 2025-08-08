<!-- src/components/ParkingMap.vue -->
<template>
  <div class="parking-map">
    <h2 class="map-heading">
      <img src="@/assets/direction-icon.png" alt="Direction Icon" class="icon" />
      Live Parking Map
    </h2>

    <p>Melbourne CBD · Updated 30s ago</p>

    <!-- Map container -->
    <div ref="mapRef" class="map-container"></div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import parkingData from '@/assets/on-street-parking-bay-sensors.json'
import { MarkerClusterer } from "@googlemaps/markerclusterer"

const mapRef = ref(null)

const initMap = () => {
  // Initialize the map
  const map = new google.maps.Map(mapRef.value, {
    center: { lat: -37.8136, lng: 144.9631 },
    zoom: 15,
  })

  // Generate all markers
  const markers = parkingData
    .filter(spot => spot.location) // Filter out the records without coordinates
    .map((spot) => {
      const marker = new google.maps.Marker({
        position: { lat: spot.location.lat, lng: spot.location.lon },
        title: `Status: ${spot.status_description}`,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 5,
          fillColor: spot.status_description === 'Unoccupied' ? 'green' : 'red',
          fillOpacity: 1,
          strokeWeight: 0,
        },
      })

      const infoWindow = new google.maps.InfoWindow({
        content: `
          <div>
            <strong>Status:</strong> ${spot.status_description}<br/>
            <strong>Zone:</strong> ${spot.zone_number}<br/>
            <strong>ID:</strong> ${spot.kerbsideid}
          </div>
        `,
      })

      marker.addListener('click', () => {
        infoWindow.open(map, marker)
      })

      return marker
    })

  // Use Marker Clusterer to aggregate markers
  new MarkerClusterer({ markers, map })
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
