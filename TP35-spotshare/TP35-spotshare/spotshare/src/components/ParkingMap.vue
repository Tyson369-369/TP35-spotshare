<!-- src/components/ParkingMap.vue -->
<template>
  <div class="parking-map">
    <h2 class="map-heading">
      <img src="@/assets/direction-icon.png" alt="Direction Icon" class="icon" />
      Live Parking Map
    </h2>

    <p>Melbourne CBD · Updated 30s ago</p>
    <div class="map-placeholder">[Map Here]</div>
  </div>
</template>

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

.map-placeholder {
  margin-top: 1rem;
  height: 300px;
  background-color: #eaf2f8;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #888;
}
</style>
