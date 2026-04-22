<template>
  <div class="crawl-view">
    <div class="crawl-left">
      <CrawlForm :running="running" @submit="onSubmit" @cancel="onCancel" />
    </div>
    <div class="crawl-right">
      <ProgressLog ref="progressLog" :events="events" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import CrawlForm from '../components/CrawlForm.vue'
import ProgressLog from '../components/ProgressLog.vue'
import {
  startCrawl,
  cancelCrawl,
  createEventSource,
  type CrawlRequest,
  type CrawlEvent,
} from '../api'

const router = useRouter()
const running = ref(false)
const events = ref<CrawlEvent[]>([])
const progressLog = ref<InstanceType<typeof ProgressLog> | null>(null)
let eventSource: EventSource | null = null

async function onSubmit(req: CrawlRequest) {
  try {
    running.value = true
    events.value = []
    progressLog.value?.reset()

    const { task_id } = await startCrawl(req)

    eventSource = createEventSource()
    eventSource.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data) as CrawlEvent
        events.value.push(event)

        if (event.type === 'finished' || event.type === 'error') {
          eventSource?.close()
          eventSource = null
          running.value = false

          if (event.type === 'finished') {
            setTimeout(() => router.push('/results'), 1000)
          }
        }
      } catch {
        // ignore parse errors
      }
    }

    eventSource.onerror = () => {
      eventSource?.close()
      eventSource = null
      running.value = false
    }
  } catch (err) {
    running.value = false
    events.value.push({
      type: 'error',
      message: err instanceof Error ? err.message : '启动失败',
    })
  }
}

async function onCancel() {
  try {
    await cancelCrawl()
  } catch {
    // ignore
  }
  eventSource?.close()
  eventSource = null
  running.value = false
}
</script>

<style scoped>
.crawl-view {
  display: flex;
  gap: 24px;
  height: 100%;
}

.crawl-left {
  width: 400px;
  flex-shrink: 0;
}

.crawl-right {
  flex: 1;
  min-width: 0;
}

@media (max-width: 900px) {
  .crawl-view {
    flex-direction: column;
  }
  .crawl-left {
    width: 100%;
  }
}
</style>
