<template>
  <div class="trends-page">
    <h1 class="heading">📊 Mobility Trends</h1>
    <p class="subheading">Learn how increasing car use and population growth impact your commute</p>

    <div class="charts-grid">
      <div class="chart-card">
        <h3>🚘 Car Ownership Over Time</h3>
        <LineChart />
        <div class="chart-note blue">
          <strong>+9% car ownership since 2018</strong><br />
          Contributing to increased parking demand in the CBD
        </div>
      </div>

      <div class="chart-card">
        <h3>📈 Population Change in CBD</h3>
        <BarChart />
        <div class="chart-note green">
          <strong>+28% CBD population since 2018</strong><br />
          Creating higher demand for parking spaces
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LineChart from '@/components/LineChart.vue'
import BarChart from '@/components/BarChart.vue'
</script>

<style scoped>
.trends-page {
  font-family: 'Segoe UI', sans-serif;
  padding: 2rem;
}

.heading,
.subheading {
  text-align: center;
}

.heading {
  font-size: 1.8rem;
  margin-bottom: 0.5rem;
}

.subheading {
  color: #555;
  margin-bottom: 2rem;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.chart-card {
  background: #fff;
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
}

.chart-note {
  margin-top: 1rem;
  font-size: 0.9rem;
  border-radius: 8px;
  padding: 0.8rem;
}

.chart-note.blue {
  background-color: #eaf6ff;
  color: #007aff;
}

.chart-note.green {
  background-color: #eafaf1;
  color: #2ecc71;
}
</style>
