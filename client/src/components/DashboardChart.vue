<template>
  <div ref="chartEl" style="width:100%;height:100%"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  type: { type: String, default: 'bar' }, // bar | pie | line | stat
  title: { type: String, default: '' },
  data: { type: Array, default: () => [] }, // [{ name, value }]
})

const chartEl = ref()
let chart = null

function buildOption() {
  if (props.type === 'pie') {
    return {
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      series: [{ type: 'pie', radius: '65%', data: props.data, emphasis: { itemStyle: { shadowBlur: 10 } } }]
    }
  }
  if (props.type === 'line') {
    return {
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: props.data.map(d => d.name), axisLabel: { rotate: 30 } },
      yAxis: { type: 'value', minInterval: 1 },
      series: [{ type: 'line', data: props.data.map(d => d.value), smooth: true, areaStyle: {} }]
    }
  }
  // default bar
  return {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: props.data.map(d => d.name), axisLabel: { rotate: 30, overflow: 'truncate', width: 80 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ type: 'bar', data: props.data.map(d => d.value), barMaxWidth: 60 }]
  }
}

onMounted(() => {
  if (props.type === 'stat') return
  chart = echarts.init(chartEl.value)
  chart.setOption(buildOption())
  window.addEventListener('resize', () => chart?.resize())
})

onUnmounted(() => {
  chart?.dispose()
})

watch(() => [props.data, props.type], () => {
  if (chart) chart.setOption(buildOption(), true)
}, { deep: true })
</script>
