<template>
  <div class="pdf-preview">
    <div v-if="!file" class="preview-empty">
      从左侧选择 PDF 文件预览
    </div>
    <div v-else class="preview-content">
      <div class="preview-header">
        <h3>{{ file.name }}</h3>
        <div class="preview-meta">
          {{ file.modified }} | {{ formatSize(file.size) }}
        </div>
        <div class="preview-actions">
          <a :href="fileUrl" target="_blank" class="btn-small">新窗口打开</a>
          <button class="btn-small" @click="copyLink">复制链接</button>
        </div>
      </div>
      <iframe :src="fileUrl" class="preview-frame"></iframe>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getFileUrl, type FileInfo } from '../api'

const props = defineProps<{ file: FileInfo | null }>()

const fileUrl = computed(() => (props.file ? getFileUrl(props.file.path) : ''))

function copyLink() {
  if (props.file) {
    navigator.clipboard.writeText(fileUrl.value)
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>

<style scoped>
.pdf-preview {
  background: var(--surface);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.preview-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary);
  font-size: 15px;
}

.preview-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.preview-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.preview-header h3 {
  font-size: 16px;
  margin-bottom: 4px;
}

.preview-meta {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.preview-actions {
  display: flex;
  gap: 8px;
}

.btn-small {
  padding: 4px 12px;
  font-size: 12px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
  text-decoration: none;
}

.btn-small:hover {
  background: var(--bg);
}

.preview-frame {
  flex: 1;
  border: none;
  width: 100%;
}
</style>
