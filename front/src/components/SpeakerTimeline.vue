<template>
  <!-- 说话人时间轴：ECharts 自定义系列渲染句级色块（gantt 风格） -->
  <div class="timeline-card card">
    <div class="timeline-head">
      <h2>Speaker 时间轴</h2>
      <div class="legend">
        <span v-for="(s, i) in speakers" :key="i" class="legend-item">
          <span class="legend-dot" :style="{ background: colorOf(i) }"></span>
          {{ s }}
        </span>
      </div>
    </div>
    <div ref="chartEl" class="chart"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  // final 事件列表：[{ speaker: '01', startTime, endTime }]
  events: { type: Array, default: () => [] },
  // 当前会话时间（毫秒）
  now: { type: Number, default: 0 },
})

// 3 个说话人轨道（与转写列表圆点颜色一致）
const speakers = ['Speaker 01', 'Speaker 02', 'Speaker 03']
const COLORS = ['#6366f1', '#10a37f', '#d97706']

function colorOf(index) {
  return COLORS[index % 3]
}

// speaker '01'/'02'/'03' → 轨道序号 0/1/2
function speakerIndex(speaker) {
  const n = parseInt(speaker, 10)
  return isNaN(n) ? 0 : (n - 1) % 3
}

const chartEl = ref(null)
let chart = null

function buildOption() {
  // 把 final 事件转成 ECharts 数据：[开始ms, 轨道序号, 结束ms]
  const data = props.events.map((e) => ({
    value: [e.startTime, speakerIndex(e.speaker), e.endTime],
    itemStyle: { color: colorOf(speakerIndex(e.speaker)) },
  }))

  // 视图范围：随会话时间推进（30 秒档位平滑滚动，最少 30 秒）
  const windowMax = Math.max(Math.ceil((props.now + 5000) / 30000) * 30000, 30000)
  const lastEnd = props.events.reduce((m, e) => Math.max(m, e.endTime), 0)
  const xMax = Math.max(windowMax, Math.ceil(lastEnd / 30000) * 30000)

  return {
    grid: { left: 70, right: 20, top: 10, bottom: 30 },
    xAxis: {
      type: 'value',
      min: 0,
      max: xMax,
      axisLabel: {
        formatter: (v) => {
          const s = Math.floor(v / 1000)
          return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
        },
      },
      splitLine: { lineStyle: { color: 'rgba(0,0,0,0.06)' } },
    },
    yAxis: {
      type: 'category',
      data: speakers,
      axisLabel: { color: '#888', fontSize: 12 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'custom',
        // 自定义渲染：每个数据画一段圆角色块
        renderItem(params, api) {
          const row = api.value(1)
          // category 轴必须传类目名（传数字索引会算出 NaN 导致坐标无效）
          const category = speakers[row]
          const start = api.coord([api.value(0), category])
          const end = api.coord([api.value(2), category])
          // params.coordSys 是对象 {x, y, width, height}（不是数组）
          const cs = params.coordSys
          // category 离散轴 api.size 返回 0，行高改用坐标系高度均分
          const rowHeight = cs.height / speakers.length
          const height = Math.min(16, rowHeight * 0.55)
          const rect = echarts.graphic.clipRectByRect(
            {
              x: start[0],
              y: start[1] - height / 2,
              width: Math.max(end[0] - start[0], 3),
              height,
            },
            { x: cs.x, y: cs.y, width: cs.width, height: cs.height }
          )
          return (
            rect && {
              type: 'rect',
              shape: rect,
              style: api.style(),
            }
          )
        },
        encode: { x: [0, 2], y: 1 },
        data,
      },
    ],
    tooltip: {
      show: true,
      formatter: (p) => {
        const e = props.events[p.dataIndex]
        if (!e) return ''
        const fmt = (ms) => {
          const s = Math.floor(ms / 1000)
          return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
        }
        return `<b>${speakers[speakerIndex(e.speaker)]}</b><br/>${fmt(e.startTime)} ~ ${fmt(e.endTime)}`
      },
    },
  }
}

function render() {
  if (!chart) return
  chart.setOption(buildOption())
}

onMounted(() => {
  chart = echarts.init(chartEl.value)
  render()
  // 窗口变化时重绘
  window.addEventListener('resize', handleResize)
})

function handleResize() {
  chart?.resize()
}

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})

// 事件或时间推进时刷新（页面每秒更新 now，final 事件随时追加）
watch(() => [props.events, props.now], () => nextTick(render), { deep: true })
</script>

<style scoped>
.timeline-card {
  margin-top: 24px;
}

.timeline-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.timeline-head h2 {
  margin: 0;
  font-size: 18px;
}

.legend {
  display: flex;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-muted);
}

.legend-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.chart {
  height: 150px;
}
</style>
