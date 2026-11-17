# XWatt 类图结构化提取协议

> 仅当知识源文档中包含 `xwatt.woa.com` URL 时，按本协议执行。

## 获取方式

通过可用的类图结构化接口调用 `getWattDiagramData` 或等价能力，传入 XWatt 资源 URL。

## 返回数据结构

```
data.resContent:
  statementList: [节点列表]
  transitionList: [边列表]
```

## 节点解析

| 字段 | 用途 |
|------|------|
| `id` | 节点唯一ID（用于边的 `fromStateId`/`toStateId` 引用） |
| `name` | 类名（中文） |
| `enName` | 英文名 |
| `backgroundColor` | 子域归属标识（按颜色分域） |
| `propertyList` | 类的属性列表 |

## 边解析

| 字段 | 用途 |
|------|------|
| `fromStateId` | 源节点 ID |
| `toStateId` | 目标节点 ID |
| `relation` | 关系类型（见下方映射） |
| `sourceMultiplicity` | 源端基数 |
| `targetMultiplicity` | 目标端基数 |
| `remark` | 关系标注 |

## 关系类型映射

| XWatt `relation` | 图谱关系类型 | 说明 |
|-------------------|------------|------|
| `Association` | 关联 | 一般关联 |
| `Generalization` | 继承 | is-a 关系 |
| `Composition` | 组合 | 强生命周期依赖 |
| `Aggregation` | 聚合 | 弱生命周期依赖 |
| `Directed Association` | 定向关联 | 有方向的关联 |
| `NoteLink` | **过滤掉** | 注释连线，非业务关系 |

## 为什么必须用结构化数据

人工整理的 MD 文档是对类图的文字描述，容易遗漏跨域连线。
XWatt JSON 是类图工具直接导出的结构化数据，包含图中每一条边，保障不遗漏。
实操经验：v5 版本因仅用 MD 文本导致 ~40% 的跨域边缺失，v6 用 XWatt JSON 后达到 100% 连通。
