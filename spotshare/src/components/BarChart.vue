<template>
  <Bar :data="chartData" :options="chartOptions" />
</template>

<script setup>
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Bar } from 'vue-chartjs'

// Import Melbourne population trend data
import melbourneTrend from '@/assets/melbourne_trend.json'

// Register required Chart.js components
ChartJS.register(BarElement, CategoryScale, LinearScale, Title, Tooltip, Legend)

// Filter data for year >= 2017
const filteredData = melbourneTrend.filter(item => item.year >= 2017)

// Prepare chart data using filtered records
const chartData = {
  labels: filteredData.map(item => item.year), // X-axis: years
  datasets: [
    {
      label: 'CBD Population',
      data: filteredData.map(item => item.melbourneCBD), // Y-axis: CBD population
      backgroundColor: '#2ecc71'
    }
  ]
}

// Chart display options
const chartOptions = {
  responsive: true,
  plugins: {
    legend: {
      display: true
    }
  }
}
</script>

