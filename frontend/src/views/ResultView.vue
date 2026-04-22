<template>
  <div class="result-view">
    <div class="result-left">
      <FileTree ref="fileTree" @select="onFileSelect" />
    </div>
    <div class="result-right">
      <PdfPreview :file="selectedFile" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import FileTree from '../components/FileTree.vue'
import PdfPreview from '../components/PdfPreview.vue'
import type { FileInfo } from '../api'

const selectedFile = ref<FileInfo | null>(null)
const fileTree = ref<InstanceType<typeof FileTree> | null>(null)

function onFileSelect(file: FileInfo) {
  selectedFile.value = file
}
</script>

<style scoped>
.result-view {
  display: flex;
  gap: 24px;
  height: 100%;
}

.result-left {
  width: 300px;
  flex-shrink: 0;
}

.result-right {
  flex: 1;
  min-width: 0;
}

@media (max-width: 900px) {
  .result-view {
    flex-direction: column;
  }
  .result-left {
    width: 100%;
    max-height: 300px;
  }
}
</style>
