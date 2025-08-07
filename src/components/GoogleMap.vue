<template>
  <div class="map-container" ref="mapRef"></div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import parkingData from '../assets/on-street-parking-bay-sensors.json'

const mapRef = ref(null)

const initMap = () => {
  const map = new google.maps.Map(mapRef.value, {
    center: { lat: -37.8136, lng: 144.9631 }, // Melbourne
    zoom: 15,
  })

  // Loop data: Add Marker
  parkingData.forEach((spot) => {
    if (!spot.location) return

    const position = {
      lat: spot.location.lat,
      lng: spot.location.lon,
    }

    const marker = new google.maps.Marker({
      position,
      map,
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
  })
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
.map-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
}
</style>
