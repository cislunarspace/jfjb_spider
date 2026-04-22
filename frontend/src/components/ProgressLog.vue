<template>
  <div class="progress-log">
    <h2>抓取进度</h2>

    <div class="progress-bar-container">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: percent + '%' }"></div>
      </div>
      <div class="progress-text">{{ statusText }}</div>
    </div>

    <div class="log-area" ref="logArea">
      <div
        v-for="(entry, i) in logs"
        :key="i"
        class="log-line"
        :class="'log-' + entry.level"
      >
        <span class="log-time">{{ entry.time }}</span>
        <span class="log-level">[{{ entry.level }}]</span>
        {{ entry.message }}
      </div>
      <div v-if="logs.length === 0" class="log-empty">
        等待抓取任务...
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import type { CrawlEvent } from '../api'

interface LogEntry {
  time: string
  level: string
  message: string
}

const props = defineProps<{ events: CrawlEvent[] }>()

const logArea = ref<HTMLElement | null>(null)

const current = ref(0)
const total = ref(0)
const logs = ref<LogEntry[]>([])

const percent = computed(() => {
  if (total.value === 0) return 0
  return Math.round((current.value / total.value) * 100)
})

const statusText = computed(() => {
  if (total.value === 0) return '空闲'
  if (current.value >= total.value && total.value > 0) return '已完成'
  return `${current.value} / ${total.value}`
})

function now(): string {
  return new Date().toLocaleTimeString('zh-CN', { hour12: false })
}

watch(
  () => props.events,
  (newEvents) => {
    const last = newEvents[newEvents.length - 1]
    if (!last) return

    switch (last.type) {
      case 'progress':
        current.value = last.current ?? 0
        total.value = last.total ?? 0
        logs.value.push({ time: now(), level: 'INFO', message: last.message ?? '' })
        break
      case 'log':
        logs.value.push({
          time: now(),
          level: last.level ?? 'INFO',
          message: last.message ?? '',
        })
        break
      case 'finished':
        logs.value.push({
          time: now(),
          level: 'SUCCESS',
          message: `完成: 成功 ${last.success} | 跳过 ${last.skip} | 失败 ${last.fail} / 共 ${last.total}`,
        })
        current.value = last.total ?? 0
        total.value = last.total ?? 0
        break
      case 'error':
        logs.value.push({ time: now(), level: 'ERROR', message: last.message ?? '' })
        break
    }

    nextTick(() => {
      if (logArea.value) {
        logArea.value.scrollTop = logArea.value.scrollHeight
      }
    })
  },
  { deep: true }
)

function reset() {
  current.value = 0
  total.value = 0
  logs.value = []
}

defineExpose({ reset })
</script>

<style scoped>
.progress-log {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 24px;
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
}

.progress-log h2 {
  font-size: 18px;
  margin-bottom: 16px;
}

.progress-bar-container {
  margin-bottom: 16px;
}

.progress-bar {
  height: 8px;
  background: var(--border);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 6px;
}

.progress-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 13px;
  color: var(--text-secondary);
}

.log-area {
  flex: 1;
  min-height: 200px;
  max-height: 400px;
  overflow-y: auto;
  background: var(--log-bg);
  border-radius: var(--radius);
  padding: 12px;
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.6;
}

.log-line {
  color: var(--log-text);
  white-space: pre-wrap;
  word-break: break-all;
}

.log-time {
  color: #94a3b8;
  margin-right: 8px;
}

.log-level {
  margin-right: 8px;
  font-weight: 600;
}

.log-ERROR .log-level,
.log-ERROR {
  color: var(--error);
}

.log-WARNING .log-level {
  color: var(--warning);
}

.log-SUCCESS .log-level,
.log-SUCCESS {
  color: var(--success);
}

.log-empty {
  color: #64748b;
  text-align: center;
  padding: 40px 0;
}
</style>
