<script setup>
import { computed, onMounted, ref } from 'vue'
import { getJson, postJson } from '../api'

const domains = ref([])
const domainId = ref(1)
const state = ref('draft') // draft=草稿 published=已发布
const draftRows = ref([])
const publishedRows = ref([])
const records = ref([])
const reports = ref([])
const err = ref('')
const notice = ref('')
const busy = ref(false)

const latestReport = computed(() => reports.value[0] || null)
const latestRecord = computed(() => records.value[0] || null)
const currentPublish = computed(() =>
  records.value.find((r) => r.status === '成功') || null
)

async function refresh() {
  const q = `domain_id=${domainId.value}`
  const [draft, published, pubs, reps] = await Promise.all([
    getJson(`/api/layers/汇总?${q}&state=draft`),
    getJson(`/api/layers/汇总?${q}&state=published`),
    getJson(`/api/publish?${q}`),
    getJson(`/api/reconcile?${q}`),
  ])
  draftRows.value = draft
  publishedRows.value = published
  records.value = pubs
  reports.value = reps
}

onMounted(async () => {
  try {
    domains.value = await getJson('/api/domains')
    if (domains.value.length) domainId.value = domains.value[0].id
    await refresh()
  } catch (e) {
    err.value = String(e.message || e)
  }
})

async function publish() {
  busy.value = true
  err.value = ''
  notice.value = ''
  try {
    const rec = await postJson('/api/publish', { domain_id: domainId.value })
    if (rec.status === '成功') {
      notice.value = `发布成功：发布编号 ${rec.id}，引用对账报告 ${rec.reconcile_report_id}，共 ${rec.row_count} 行。`
      state.value = 'published'
    } else {
      err.value = `发布被拒绝：${rec.reason}`
    }
    await refresh()
  } catch (e) {
    err.value = String(e.message || e)
  } finally {
    busy.value = false
  }
}
</script>
<template>
  <div>
    <h2>汇总层</h2>
    <p class="lead">
      汇总分双态：明细到汇总只写<strong>草稿</strong>；最近一次层间对账为「一致」时才可发布，
      发布把草稿快照整体写入<strong>已发布</strong>区，已发布区只能被下一次成功发布整体替换。
    </p>
    <div class="toolbar">
      <label>
        主题域
        <select v-model.number="domainId" @change="refresh">
          <option v-for="d in domains" :key="d.id" :value="d.id">{{ d.name }}</option>
        </select>
      </label>
      <span class="tabs">
        <button
          class="tab"
          :class="{ active: state === 'draft' }"
          @click="state = 'draft'"
        >草稿（{{ draftRows.length }} 行）</button>
        <button
          class="tab"
          :class="{ active: state === 'published' }"
          @click="state = 'published'"
        >已发布（{{ publishedRows.length }} 行）</button>
      </span>
      <button :disabled="busy" @click="publish">发布当前草稿</button>
      <span v-if="latestReport" class="muted">
        最近对账：
        <span :class="latestReport.status === '一致' ? 'ok' : 'warn'">
          报告 {{ latestReport.id }} · {{ latestReport.status }}
        </span>
      </span>
      <span v-else class="warn">尚未对账，不能发布</span>
    </div>
    <p v-if="notice" class="okline">{{ notice }}</p>
    <p v-if="err" class="err">{{ err }}</p>
    <p v-if="latestRecord && latestRecord.status === '拒绝'" class="warnline">
      最近一次发布被拒绝（发布编号 {{ latestRecord.id }}）：{{ latestRecord.reason }}
    </p>

    <div v-if="state === 'draft'" class="panel">
      <h3>草稿态汇总 <span class="badge badge-draft">草稿</span></h3>
      <table v-if="draftRows.length">
        <thead>
          <tr>
            <th>编号</th><th>主题域</th><th>业务日</th><th>门店编码</th>
            <th>金额合计</th><th>件数合计</th><th>明细行数</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in draftRows" :key="r.id">
            <td>{{ r.id }}</td>
            <td>{{ r.domain_id }}</td>
            <td>{{ r.biz_day }}</td>
            <td>{{ r.store_code }}</td>
            <td>{{ r.amount_sum }}</td>
            <td>{{ r.qty_sum }}</td>
            <td>{{ r.line_count }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="muted">草稿为空，请先在「分层任务」跑明细到汇总。</p>
    </div>

    <div v-else class="panel">
      <h3>已发布汇总 <span class="badge badge-pub">已发布</span></h3>
      <p v-if="currentPublish" class="muted">
        当前发布：发布编号 {{ currentPublish.id }} · 引用对账报告 {{ currentPublish.reconcile_report_id }}
        · {{ currentPublish.row_count }} 行 · {{ currentPublish.created_at }}
      </p>
      <table v-if="publishedRows.length">
        <thead>
          <tr>
            <th>编号</th><th>发布编号</th><th>业务日</th><th>门店编码</th>
            <th>金额合计</th><th>件数合计</th><th>明细行数</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in publishedRows" :key="r.id">
            <td>{{ r.id }}</td>
            <td>{{ r.publish_id }}</td>
            <td>{{ r.biz_day }}</td>
            <td>{{ r.store_code }}</td>
            <td>{{ r.amount_sum }}</td>
            <td>{{ r.qty_sum }}</td>
            <td>{{ r.line_count }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="muted">已发布区为空：对账一致后点击「发布当前草稿」。</p>
    </div>

    <div class="panel">
      <h3>发布记录</h3>
      <table v-if="records.length">
        <thead>
          <tr>
            <th>编号</th><th>状态</th><th>对账报告</th><th>行数</th><th>原因</th><th>时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in records" :key="p.id">
            <td>{{ p.id }}</td>
            <td :class="p.status === '成功' ? 'ok' : 'warn'">{{ p.status }}</td>
            <td>{{ p.reconcile_report_id ?? '—' }}</td>
            <td>{{ p.row_count }}</td>
            <td>{{ p.reason || '—' }}</td>
            <td>{{ p.created_at }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="muted">暂无发布记录。</p>
    </div>
  </div>
</template>
