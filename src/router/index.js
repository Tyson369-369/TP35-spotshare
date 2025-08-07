// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import GoogleMap from '../components/GoogleMap.vue'
import ParkingBarChart from '../components/ParkingBarChart.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: GoogleMap,
  },
  {
    path: '/chart',
    name: 'Chart',
    component: ParkingBarChart,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
