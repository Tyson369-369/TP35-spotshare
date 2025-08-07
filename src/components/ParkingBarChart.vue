<template>
  <div>
    <h2>Parking space status statistics</h2>
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import parkingData from '../assets/on-street-parking-bay-sensors.json'

const chartRef = ref(null)

onMounted(() => {
  const statusCount = {}

  parkingData.forEach((item) => {
    const status = item.status_description || 'Unknown'
    statusCount[status] = (statusCount[status] || 0) + 1
  })

  const chart = echarts.init(chartRef.value)

  const option = {
    title: {
      text: 'Current status statistics of parking spaces',
      left: 'center',
    },
    tooltip: {},
    xAxis: {
      type: 'category',
      data: Object.keys(statusCount),
      axisLabel: {
        fontSize: 14,
        rotate: 30,
      },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        fontSize: 14,
      },
    },
    series: [
      {
        type: 'bar',
        data: Object.values(statusCount),
        barWidth: '50%',
        itemStyle: {
          borderRadius: 4,
        },
      },
    ],
  }

  chart.setOption(option)
  window.addEventListener('resize', () => chart.resize())
})
</script>

<style scoped>
.chart-container {
  width: 1200px;
  height: 600px;
  margin: 0 auto;
}
</style>
