<template>
  <!-- 待办任务卡片 -->
  <div class="card">
    <div class="card-head">
      <h3 class="card-title">
        <ListChecks :size="18" :stroke-width="1.75" />
        待办任务
      </h3>
      <span class="tag-ai">AI 生成</span>
    </div>

    <!-- 空状态：LLM 提不出待办 -->
    <div v-if="!tasks.length" class="empty">这场会议没有提取到待办任务</div>

    <div v-for="(task, i) in tasks" :key="i" class="task">
      <el-checkbox v-model="doneList[i]" size="large">
        <div class="task-body">
          <div class="task-owner">
            {{ task.owner || '未指派' }}
            <span v-if="task.deadline" class="task-deadline">截止：{{ task.deadline }}</span>
          </div>
          <div class="task-name" :class="{ 'task-done': doneList[i] }">
            {{ task.task }}
          </div>
        </div>
      </el-checkbox>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ListChecks } from 'lucide-vue-next'

const props = defineProps({
  // LLM 输出的任务数组：[{ task, owner, deadline }]
  tasks: {
    type: Array,
    required: true,
  },
})

// 勾选状态只存本地（页面交互用，不入库）
const doneList = ref(props.tasks.map(() => false))
watch(
  () => props.tasks,
  (val) => {
    doneList.value = val.map(() => false)
  }
)
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

/* 标题：图标与文字垂直居中 */
.card-title {
  display: flex;
  align-items: center;
  gap: 9px;
}

.card-title svg {
  color: var(--color-accent);
  flex-shrink: 0;
}

.empty {
  color: var(--color-muted);
  font-size: 14px;
  padding: 12px 0 4px;
}

.task {
  background: var(--color-canvas);
  border-radius: var(--radius-sm);
  padding: 14px 16px;
  margin-top: 12px;
}

.task-owner {
  font-size: 12px;
  color: var(--color-accent);
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 截止时间：灰色小字，和负责人同行 */
.task-deadline {
  color: var(--color-muted);
  font-weight: 400;
}

.task-name {
  font-size: 15px;
  margin-top: 2px;
}

/* 已完成：划线置灰 */
.task-done {
  text-decoration: line-through;
  color: var(--color-muted);
}
</style>
