# 05-tiercraft（筑层）

筑层 — 数仓分层建设台：贴源入仓 → 明细清洗标准化 → 汇总落表 → 层间行数/键对账。

**不是** 多源 Feed 归并，**不是** 作业依赖编排，**不是** CDC 变更流按序落库，**不是** 质检隔离签发。
**也不是** 报表看板 / CRUD 后台 / 电商订单前台 / OA 工单。

## 启动

```bash
docker compose up --build
```

本地开发：

```bash
# 后端
cd backend
pip install -r requirements.txt
set DATA_DIR=..\data
uvicorn app.main:app --reload --port 10500

# 前端
cd frontend
npm install
npm run dev
```

| 入口 | 地址 |
| --- | --- |
| 前端 | http://localhost:5500 |
| 接口 | http://localhost:10500 |

## 主链

登记主题域 → 贴源层装载夹具 → 明细层清洗标准化 → 汇总层聚合（只写草稿） → 层间对账 → 对账一致后发布草稿快照到已发布区 → 总览与各层列表数字同源

## 发布闸口

- 汇总分**草稿 / 已发布**双态，物理分表（`layer_summary` 草稿、`layer_summary_published` 已发布副本），隔离查询，不靠状态位冒充。
- 明细到汇总只重写草稿；已发布区只能被一次成功发布整体替换。
- 仅当该主题域最近一次层间对账为「一致」才允许发布；发布记录引用对账报告编号、发布时间、行数，与发布区内容同源派生。
- 未对账或对账存在差异：整单拒绝，发布区不动，拒绝原因写入发布记录并在界面展示；发布写库为单事务，不留半截发布区。
- 接口：`POST /api/publish`（返回本次发布记录，含拒绝原因）、`GET /api/publish`、`GET /api/layers/汇总?state=draft|published`。

## 界面约定

页面文案全部中文；分层称「贴源层 / 明细层 / 汇总层」，界面不出现英文缩写站名。
