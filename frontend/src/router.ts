import { createRouter, createWebHistory } from 'vue-router'
import CrawlView from './views/CrawlView.vue'
import ResultView from './views/ResultView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/crawl' },
    { path: '/crawl', component: CrawlView },
    { path: '/results', component: ResultView },
  ],
})
