<template>
  <div class="dashboard-grid">
    <section class="map-section">
      <ParkingMap />
    </section>

    <section class="feed-section">
      <LiveFeed />
    </section>
  </div>
</template>

<script setup>
import ParkingMap from '@/components/ParkingMap.vue'
import LiveFeed from '@/components/LiveFeed.vue'
</script>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: 2fr 1.2fr;
  gap: 2rem;
  height: calc(100vh - 80px); /* adjust if navbar height changes */
}

.map-section, .feed-section {
  background-color: #fff;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}
</style>
