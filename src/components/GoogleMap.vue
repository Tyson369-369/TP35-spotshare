<template>
  <div class="map-container" ref="mapRef"></div>
</template>

<script setup>
import { onMounted, ref } from 'vue'

const mapRef = ref(null)

const initMap = () => {
  const map = new google.maps.Map(mapRef.value, {
    center: { lat: -37.8136, lng: 144.9631 }, // Melbourne, Australia
    zoom: 14,
  })

  // Optional: Add a tag Melbourne CBD
  new google.maps.Marker({
    position: { lat: -37.8136, lng: 144.9631 },
    map,
    title: 'Melbourne Center',
  })
}

onMounted(() => {
  if (typeof google !== 'undefined') {
    initMap()
  } else {
    // Dynamically load Google Maps scripts
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
