<template>
  <!-- AI 会议摘要卡片 -->
  <div class="card">
    <div class="card-head">
      <h3>📌 会议摘要</h3>
      <span class="tag-ai">AI 生成</span>
    </div>

    <div class="theme">会议主题：{{ summary.theme }}</div>

    <div class="section-label">核心内容</div>
    <ul class="points">
      <li v-for="(point, i) in summary.points" :key="i">{{ point }}</li>
    </ul>
  </div>
</template>

<script setup>
defineProps({
  summary: {
    type: Object,
    required: true,
  },
})
</script>

<style scoped>
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.card-head h3 {
  margin: 0;
  font-size: 18px;
}

.theme {
  font-size: 15px;
  font-weight: 600;
  padding: 12px 16px;
  background: var(--color-canvas);
  border-radius: var(--radius-sm);
  margin-bottom: 18px;
}

.section-label {
  font-size: 13px;
  color: var(--color-muted);
  margin-bottom: 8px;
}

.points {
  margin: 0;
  padding-left: 20px;
  font-size: 15px;
  line-height: 1.9;
  color: var(--color-ink);
}
</style>
