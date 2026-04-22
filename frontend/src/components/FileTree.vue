<template>
  <div class="file-tree">
    <div class="tree-header">
      <h2>输出文件</h2>
      <button class="btn-small" @click="loadFiles">刷新</button>
    </div>

    <div class="tree-content">
      <div v-if="loading" class="tree-loading">加载中...</div>
      <div v-else-if="dirs.length === 0" class="tree-empty">暂无输出文件</div>

      <div v-for="dir in dirs" :key="dir.path" class="dir-group">
        <div class="dir-header" @click="toggleDir(dir.path)">
          <span class="dir-arrow">{{ expanded.has(dir.path) ? '&#9660;' : '&#9654;' }}</span>
          <span class="dir-name">{{ dir.name }}</span>
        </div>
        <div v-if="expanded.has(dir.path)" class="dir-files">
          <div
            v-for="file in dirFiles.get(dir.path) || []"
            :key="file.path"
            class="file-item"
            :class="{ selected: selectedFile === file.path }"
            @click="selectFile(file)"
          >
            <span class="file-name">{{ file.name }}</span>
            <span class="file-size">{{ formatSize(file.size) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listFiles, type FileInfo } from '../api'

const emit = defineEmits<{
  select: [file: FileInfo]
}>()

const loading = ref(false)
const dirs = ref<FileInfo[]>([])
const dirFiles = ref<Map<string, FileInfo[]>>(new Map())
const expanded = ref(new Set<string>())
const selectedFile = ref('')

async function loadFiles() {
  loading.value = true
  try {
    const entries = await listFiles()
    dirs.value = entries.filter((e) => e.is_dir).sort((a, b) => b.name.localeCompare(a.name))

    for (const dir of dirs.value) {
      const files = await listFiles(dir.name)
      dirFiles.value.set(
        dir.path,
        files.filter((f) => !f.is_dir && f.name.endsWith('.pdf'))
      )
    }

    // Auto-expand latest dir
    if (dirs.value.length > 0 && expanded.value.size === 0) {
      expanded.value.add(dirs.value[0].path)
    }
  } finally {
    loading.value = false
  }
}

function toggleDir(path: string) {
  if (expanded.value.has(path)) {
    expanded.value.delete(path)
  } else {
    expanded.value.add(path)
  }
  expanded.value = new Set(expanded.value)
}

function selectFile(file: FileInfo) {
  selectedFile.value = file.path
  emit('select', file)
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

onMounted(loadFiles)

defineExpose({ loadFiles })
</script>

<style scoped>
.file-tree {
  background: var(--surface);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.tree-header h2 {
  font-size: 16px;
}

.btn-small {
  padding: 4px 12px;
  font-size: 12px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
}

.btn-small:hover {
  background: var(--bg);
}

.tree-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.tree-loading,
.tree-empty {
  text-align: center;
  padding: 40px 16px;
  color: var(--text-secondary);
}

.dir-group {
  margin-bottom: 2px;
}

.dir-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
  user-select: none;
}

.dir-header:hover {
  background: var(--bg);
}

.dir-arrow {
  font-size: 10px;
  width: 12px;
  color: var(--text-secondary);
}

.dir-files {
  padding-left: 32px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  padding: 6px 16px;
  cursor: pointer;
  border-radius: var(--radius);
  margin: 0 8px;
  font-size: 13px;
}

.file-item:hover {
  background: var(--bg);
}

.file-item.selected {
  background: #eff6ff;
  color: var(--accent);
}

.file-size {
  color: var(--text-secondary);
  font-size: 12px;
}
</style>
