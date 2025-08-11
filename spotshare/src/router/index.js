import { createRouter, createWebHistory } from 'vue-router'

import DashboardView from '@/views/DashboardView.vue'
import FindParkingView from '@/views/FindParkingView.vue'
import TrendsView from '@/views/TrendsView.vue'
import HistoryView from '@/views/HistoryView.vue'
import EcoScoreView from '@/views/EcoScoreView.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: DashboardView },
  { path: '/find-parking', component: FindParkingView },
  { path: '/trends', component: TrendsView },
  { path: '/history', component: HistoryView },
  { path: '/eco-score', component: EcoScoreView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
