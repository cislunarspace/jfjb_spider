<template>
  <div class="crawl-view">
    <div class="crawl-left">
      <CrawlForm :running="running" @submit="onSubmit" @cancel="onCancel" />
    </div>
    <div class="crawl-right">
      <ProgressLog ref="progressLog" :events="events" :running="running" />
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
  getStatus,
  createEventSource,
  type CrawlRequest,
  type CrawlEvent,
} from '../api'

const router = useRouter()
const running = ref(false)
const events = ref<CrawlEvent[]>([])
const progressLog = ref<InstanceType<typeof ProgressLog> | null>(null)
let eventSource: EventSource | null = null

function addEvent(event: CrawlEvent) {
  events.value = [...events.value, event]
}

async function onSubmit(req: CrawlRequest) {
  try {
    running.value = true
    events.value = []
    progressLog.value?.reset()

    const { task_id } = await startCrawl(req)
    addEvent({ type: 'log', level: 'INFO', message: `任务已启动 (ID: ${task_id})` })

    eventSource = createEventSource()
    eventSource.onopen = () => {
      addEvent({ type: 'log', level: 'INFO', message: '已连接实时进度流' })
    }

    eventSource.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data) as CrawlEvent
        addEvent(event)

        if (event.type === 'finished' || event.type === 'error') {
          eventSource?.close()
          eventSource = null
          running.value = false

          if (event.type === 'finished') {
            setTimeout(() => router.push('/results'), 1000)
          }
        }
      } catch {
        addEvent({ type: 'log', level: 'ERROR', message: '解析进度数据失败' })
      }
    }

    eventSource.onerror = async () => {
      addEvent({ type: 'log', level: 'ERROR', message: '实时进度流连接中断' })
      eventSource?.close()
      eventSource = null
      // 查询后端确认任务是否仍在运行，避免状态不一致
      try {
        const status = await getStatus()
        if (!status.running) {
          running.value = false
        }
      } catch {
        running.value = false
      }
    }
  } catch (err) {
    running.value = false
    addEvent({
      type: 'error',
      message: err instanceof Error ? err.message : '启动失败',
    })
  }
}

async function onCancel() {
  try {
    await cancelCrawl()
    addEvent({ type: 'log', level: 'INFO', message: '已发送取消请求' })
  } catch (err) {
    addEvent({
      type: 'log',
      level: 'WARNING',
      message: err instanceof Error ? err.message : '取消请求失败',
    })
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
