<template>
  <div ref="chartEl" style="width:100%;height:100%"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  type: { type: String, default: 'bar' },
  data: { type: Array, default: () => [] },       // [{name, value}] or [{x,y,name}] for scatter
  series: { type: Array, default: () => [] },     // [{name, data:[{name,value}]}] for multi-series
  gaugeMax: { type: Number, default: 100 },
})

const emit = defineEmits(['click'])
const chartEl = ref()
let chart = null
let ro = null

const COLORS = ['#5470c6','#91cc75','#fac858','#ee6666','#73c0de','#3ba272','#fc8452','#9a60b4','#ea7ccc']
const isMulti = () => props.series.length > 0

function buildOption() {
  switch (props.type) {
    case 'pie':    return buildPie()
    case 'funnel': return buildFunnel()
    case 'gauge':  return buildGauge()
    case 'scatter':return buildScatter()
    case 'line':   return buildLine()
    default:       return buildBar()
  }
}

function buildPie() {
  return {
    color: COLORS,
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', right: 10, top: 'center', type: 'scroll', textStyle: { fontSize: 12 } },
    series: [{
      type: 'pie', radius: ['38%', '65%'], center: ['42%', '50%'],
      data: props.data,
      emphasis: { itemStyle: { shadowBlur: 12, shadowColor: 'rgba(0,0,0,0.25)' } },
      label: { formatter: '{b}\n{d}%', fontSize: 11 }
    }]
  }
}

function buildFunnel() {
  return {
    color: COLORS,
    tooltip: { trigger: 'item', formatter: '{b}: {c}' },
    series: [{
      type: 'funnel', left: '10%', width: '80%', top: 20, bottom: 20,
      data: props.data.map((d, i) => ({ ...d, itemStyle: { color: COLORS[i % COLORS.length] } })),
      label: { position: 'inside', formatter: '{b}: {c}', color: '#fff', fontSize: 12 },
      emphasis: { label: { fontSize: 14 } }
    }]
  }
}

function buildGauge() {
  const val = props.data[0]?.value ?? 0
  const pct = props.gaugeMax > 0 ? Math.min(100, Math.round((val / props.gaugeMax) * 100)) : 0
  return {
    series: [{
      type: 'gauge', startAngle: 200, endAngle: -20,
      min: 0, max: props.gaugeMax, splitNumber: 5,
      axisLine: {
        lineStyle: {
          width: 20,
          color: [[pct / 100, new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#5470c6' }, { offset: 1, color: '#91cc75' }
          ])], [1, '#f0f0f0']]
        }
      },
      pointer: { show: false },
      axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false },
      detail: {
        valueAnimation: true,
        formatter: `{value}\n${pct}%`,
        color: '#5470c6', fontSize: 22, fontWeight: 700, offsetCenter: [0, '10%']
      },
      title: { show: false },
      data: [{ value: val }]
    }]
  }
}

function buildScatter() {
  return {
    color: COLORS,
    tooltip: { trigger: 'item', formatter: p => `${p.data[2] || ''}<br/>X: ${p.data[0]}<br/>Y: ${p.data[1]}` },
    grid: { left: 44, right: 16, top: 16, bottom: 40 },
    xAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed', color: '#f0f0f0' } } },
    yAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed', color: '#f0f0f0' } } },
    series: [{
      type: 'scatter',
      data: props.data.map(d => [d.x, d.y, d.name]),
      symbolSize: 10,
      itemStyle: { color: '#5470c6', opacity: 0.75 },
      emphasis: { itemStyle: { shadowBlur: 8 } }
    }]
  }
}

function buildLine() {
  const multi = isMulti()
  const xData = multi
    ? [...new Set(props.series.flatMap(s => s.data.map(d => d.name)))]
    : props.data.map(d => d.name)
  return {
    color: COLORS,
    tooltip: { trigger: 'axis' },
    legend: multi ? { top: 0, type: 'scroll', textStyle: { fontSize: 12 } } : { show: false },
    grid: { left: 44, right: 16, top: multi ? 36 : 16, bottom: 64 },
    xAxis: {
      type: 'category', data: xData,
      axisLabel: { rotate: 30, overflow: 'truncate', width: 80, fontSize: 11 },
      axisLine: { lineStyle: { color: '#e0e0e0' } }
    },
    yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { type: 'dashed', color: '#f0f0f0' } } },
    series: multi
      ? props.series.map((s, i) => ({
          name: s.name, type: 'line', smooth: true,
          data: xData.map(x => s.data.find(d => d.name === x)?.value ?? 0),
          lineStyle: { width: 2.5 }, symbol: 'circle', symbolSize: 6,
          areaStyle: i === 0 ? {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: COLORS[i] + '55' }, { offset: 1, color: COLORS[i] + '05' }
            ])
          } : undefined
        }))
      : [{
          type: 'line', smooth: true, data: props.data.map(d => d.value),
          lineStyle: { width: 3, color: '#5470c6' }, symbol: 'circle', symbolSize: 7,
          itemStyle: { color: '#5470c6', borderWidth: 2, borderColor: '#fff' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(84,112,198,0.35)' }, { offset: 1, color: 'rgba(84,112,198,0.02)' }
            ])
          }
        }]
  }
}

function buildBar() {
  const multi = isMulti()
  const xData = multi
    ? [...new Set(props.series.flatMap(s => s.data.map(d => d.name)))]
    : props.data.map(d => d.name)
  return {
    color: COLORS,
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: multi ? { top: 0, type: 'scroll', textStyle: { fontSize: 12 } } : { show: false },
    grid: { left: 44, right: 16, top: multi ? 36 : 16, bottom: 64 },
    xAxis: {
      type: 'category', data: xData,
      axisLabel: { rotate: 30, overflow: 'truncate', width: 80, fontSize: 11 },
      axisLine: { lineStyle: { color: '#e0e0e0' } }, axisTick: { show: false }
    },
    yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { type: 'dashed', color: '#f0f0f0' } } },
    series: multi
      ? props.series.map((s, i) => ({
          name: s.name, type: 'bar', barMaxWidth: 36,
          data: xData.map(x => s.data.find(d => d.name === x)?.value ?? 0),
          itemStyle: { color: COLORS[i % COLORS.length], borderRadius: [3, 3, 0, 0] }
        }))
      : [{
          type: 'bar', barMaxWidth: 52,
          data: props.data.map((d, i) => ({
            value: d.value,
            itemStyle: { color: COLORS[i % COLORS.length], borderRadius: [4, 4, 0, 0] }
          })),
          emphasis: { itemStyle: { shadowBlur: 8, shadowColor: 'rgba(0,0,0,0.15)' } }
        }]
  }
}

onMounted(() => {
  chart = echarts.init(chartEl.value)
  chart.setOption(buildOption())
  chart.on('click', p => emit('click', p))
  ro = new ResizeObserver(() => chart?.resize())
  ro.observe(chartEl.value)
})

onUnmounted(() => {
  ro?.disconnect()
  chart?.dispose()
})

watch(() => [props.data, props.series, props.type, props.gaugeMax], () => {
  chart?.setOption(buildOption(), true)
}, { deep: true })
</script>
