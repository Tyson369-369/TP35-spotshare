<template>
  <Line :data="chartData" :options="chartOptions" />
</template>

<script setup>
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Line } from 'vue-chartjs'

// Import real data
import carGrowthData from '@/assets/vic_car_growth.json'

ChartJS.register(LineElement, PointElement, CategoryScale, LinearScale, Title, Tooltip, Legend)

// Extract the year and the number of new vehicles from the JSON
const chartData = {
  labels: carGrowthData.map(item => item.year), // Year on the X-axis
  datasets: [
    {
      label: 'Vehicles Added',
      data: carGrowthData.map(item => item.vehiclesAdded), // Number of vehicles on the Y-axis
      backgroundColor: '#007aff',
      borderColor: '#007aff',
      tension: 0.3,
      fill: false,
      pointRadius: 5,
    }
  ]
}

const chartOptions = {
  responsive: true,
  plugins: {
    legend: {
      display: true
    }
  }
}
</script>

