<template>
  <div ref="chartEl" style="width:100%;height:100%"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  type: { type: String, default: 'bar' },
  data: { type: Array, default: () => [] },
})

const chartEl = ref()
let chart = null
let ro = null

const COLORS = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc']

function buildOption() {
  if (props.type === 'pie') {
    return {
      color: COLORS,
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { orient: 'vertical', right: 10, top: 'center', type: 'scroll', textStyle: { fontSize: 12 } },
      series: [{
        type: 'pie',
        radius: ['38%', '65%'],
        center: ['42%', '50%'],
        data: props.data,
        emphasis: { itemStyle: { shadowBlur: 12, shadowColor: 'rgba(0,0,0,0.25)' } },
        label: { formatter: '{b}\n{d}%', fontSize: 11 }
      }]
    }
  }
  if (props.type === 'line') {
    return {
      color: COLORS,
      tooltip: { trigger: 'axis' },
      grid: { left: 44, right: 16, top: 16, bottom: 64 },
      xAxis: {
        type: 'category',
        data: props.data.map(d => d.name),
        axisLabel: { rotate: 30, overflow: 'truncate', width: 80, fontSize: 11 },
        axisLine: { lineStyle: { color: '#e0e0e0' } }
      },
      yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { type: 'dashed', color: '#f0f0f0' } } },
      series: [{
        type: 'line',
        data: props.data.map(d => d.value),
        smooth: true,
        symbol: 'circle',
        symbolSize: 7,
        lineStyle: { width: 3, color: '#5470c6' },
        itemStyle: { color: '#5470c6', borderWidth: 2, borderColor: '#fff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(84,112,198,0.35)' },
            { offset: 1, color: 'rgba(84,112,198,0.02)' }
          ])
        }
      }]
    }
  }
  // bar
  return {
    color: COLORS,
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 44, right: 16, top: 16, bottom: 64 },
    xAxis: {
      type: 'category',
      data: props.data.map(d => d.name),
      axisLabel: { rotate: 30, overflow: 'truncate', width: 80, fontSize: 11 },
      axisLine: { lineStyle: { color: '#e0e0e0' } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      splitLine: { lineStyle: { type: 'dashed', color: '#f0f0f0' } }
    },
    series: [{
      type: 'bar',
      data: props.data.map((d, i) => ({
        value: d.value,
        itemStyle: { color: COLORS[i % COLORS.length], borderRadius: [4, 4, 0, 0] }
      })),
      barMaxWidth: 52,
      emphasis: { itemStyle: { shadowBlur: 8, shadowColor: 'rgba(0,0,0,0.15)' } }
    }]
  }
}

onMounted(() => {
  chart = echarts.init(chartEl.value)
  chart.setOption(buildOption())
  ro = new ResizeObserver(() => chart?.resize())
  ro.observe(chartEl.value)
})

onUnmounted(() => {
  ro?.disconnect()
  chart?.dispose()
})

watch(() => [props.data, props.type], () => {
  chart?.setOption(buildOption(), true)
}, { deep: true })
</script>
