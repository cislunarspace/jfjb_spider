<template>
  <div class="crawl-form">
    <h2>抓取配置</h2>

    <div class="form-group">
      <label>报纸类型</label>
      <select v-model="form.paper_type" @change="onPaperTypeChange">
        <option value="jfjb">解放军报</option>
        <option value="rmrb">人民日报</option>
      </select>
    </div>

    <div class="form-group">
      <label>抓取模式</label>
      <div class="radio-group">
        <label>
          <input type="radio" value="single" v-model="mode" /> 单日
        </label>
        <label v-if="form.paper_type === 'jfjb'">
          <input type="radio" value="batch" v-model="mode" /> 批量
        </label>
      </div>
    </div>

    <div class="form-group" v-if="mode === 'single'">
      <label>日期</label>
      <input type="date" v-model="form.paper_date" />
    </div>

    <template v-if="mode === 'batch'">
      <div class="form-group">
        <label>起始日期</label>
        <input type="date" v-model="form.start_date" />
      </div>
      <div class="form-group">
        <label>结束日期</label>
        <input type="date" v-model="form.end_date" />
      </div>
    </template>

    <div class="form-group">
      <label>输出目录</label>
      <input type="text" v-model="form.output_dir" placeholder="output" />
    </div>

    <div class="form-group">
      <label>导出选项</label>
      <div class="checkbox-group">
        <label>
          <input type="checkbox" v-model="form.export_individual" /> 单篇 PDF
        </label>
        <label>
          <input type="checkbox" v-model="form.export_combined" /> 合集 PDF
        </label>
      </div>
    </div>

    <div class="form-group">
      <label>字体目录 <span class="optional">（可选）</span></label>
      <input type="text" v-model="form.font_dir" placeholder="留空则自动发现系统字体" />
    </div>

    <div class="form-actions">
      <button class="btn-primary" :disabled="running || !isValid" @click="onSubmit">
        {{ running ? '抓取中...' : '开始抓取' }}
      </button>
      <button class="btn-secondary" :disabled="!running" @click="onCancel">
        停止
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import type { CrawlRequest } from '../api'

const emit = defineEmits<{
  submit: [req: CrawlRequest]
  cancel: []
}>()

defineProps<{ running: boolean }>()

const mode = ref<'single' | 'batch'>('single')

const form = reactive({
  paper_type: 'jfjb' as 'jfjb' | 'rmrb',
  paper_date: new Date().toISOString().slice(0, 10),
  start_date: '',
  end_date: '',
  output_dir: 'output',
  export_individual: true,
  export_combined: true,
  font_dir: '',
})

const isValid = computed(() => {
  if (mode.value === 'single') {
    return !!form.paper_date
  }
  return !!form.start_date && !!form.end_date
})

function onPaperTypeChange() {
  if (form.paper_type === 'rmrb') {
    mode.value = 'single'
    form.output_dir = 'output/rmrb'
  } else {
    form.output_dir = 'output'
  }
}

function onSubmit() {
  const req: CrawlRequest = {
    paper_type: form.paper_type,
    output_dir: form.output_dir,
    export_individual: form.export_individual,
    export_combined: form.export_combined,
  }
  if (mode.value === 'single') {
    req.paper_date = form.paper_date
  } else {
    req.start_date = form.start_date
    req.end_date = form.end_date
  }
  if (form.font_dir) {
    req.font_dir = form.font_dir
  }
  emit('submit', req)
}

function onCancel() {
  emit('cancel')
}
</script>

<style scoped>
.crawl-form {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 24px;
  border: 1px solid var(--border);
}

.crawl-form h2 {
  font-size: 18px;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group > label {
  display: block;
  font-weight: 600;
  margin-bottom: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.optional {
  font-weight: 400;
  color: var(--text-secondary);
}

input[type='text'],
input[type='date'],
select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s;
}

input:focus,
select:focus {
  border-color: var(--accent);
}

.radio-group,
.checkbox-group {
  display: flex;
  gap: 16px;
}

.radio-group label,
.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 400;
  cursor: pointer;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.btn-primary {
  background: var(--accent);
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 600;
  transition: background 0.15s;
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border);
  padding: 10px 24px;
  border-radius: var(--radius);
  font-size: 14px;
  transition: all 0.15s;
}

.btn-secondary:hover:not(:disabled) {
  background: var(--bg);
  color: var(--text);
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
