# 知识图谱生成示例

## 示例 1：YAML 主输出格式

v6.0 起主输出为五层 YAML 格式，以下为完整示例。

### kg-entities.yaml

```yaml
meta:
  title: "微信支付商户领域知识图谱"
  domain: "微信支付-商户管理"
  version: "v1.0"

entities:
  - id: "E_MERCHANT_商户"
    name: "商户"
    name_en: "Merchant"
    type: "聚合根"
    domain: "参与方域"
    description: "在微信支付平台注册并开展经营活动的法人或个人主体。商户是整个支付体系的核心参与者，所有交易、结算、退款都围绕商户展开。"
    aliases: ["商家", "收款方", "mch", "merchant"]
    source: "名词库"
    properties:
      - {key: "商户号", type: "string", required: true}
      - {key: "商户名称", type: "string", required: true}
      - {key: "商户类型", type: "enum"}
    confidence: 0.99

  - id: "E_MERCHANT_门店"
    name: "门店"
    name_en: "Store"
    type: "实体"
    domain: "参与方域"
    description: "商户的线下经营场所。一个商户可拥有多个门店，门店是线下收款的最小经营单元。"
    aliases: ["store", "shop"]
    source: "名词库"
    properties:
      - {key: "门店ID", type: "string", required: true}
      - {key: "门店名称", type: "string", required: true}
    confidence: 0.95

  - id: "E_TRADE_交易订单"
    name: "交易订单"
    name_en: "TradeOrder"
    type: "聚合根"
    domain: "交易域"
    description: "一次交易行为的完整记录。订单是支付体系的核心凭证，其状态变化驱动退款和结算流程。"
    aliases: ["交易单", "支付订单", "order"]
    source: "34-交易领域模型.md"
    properties:
      - {key: "微信支付交易订单号", type: "string", required: true}
      - {key: "商户订单号", type: "string", required: true}
      - {key: "订单金额", type: "decimal", required: true}
    confidence: 0.99

  - id: "E_REFUND_退款单"
    name: "退款单"
    name_en: "RefundOrder"
    type: "实体"
    domain: "退款域"
    description: "对已支付订单发起的资金退还操作记录。退款金额从商户账户扣除并原路返回给用户。"
    aliases: ["退款订单", "refund"]
    source: "00-退款业务领域建模.md"
    confidence: 0.99

  - id: "E_SETTLE_结算账户"
    name: "结算账户"
    name_en: "SettlementAccount"
    type: "实体"
    domain: "结算域"
    description: "商户用于接收交易资金的银行账户。交易资金 T+1 自动结算到此账户。"
    aliases: ["收款账户", "settle_acct"]
    source: "名词库"
    confidence: 0.95
```

### kg-relations.yaml

```yaml
relations:
  - id: "R_001"
    head: "E_MERCHANT_商户"
    relation_type: "组合"
    tail: "E_MERCHANT_门店"
    description: "商户拥有多个门店，门店生命周期依赖商户"
    cardinality: "1:N"
    source: "名词库"
    domain: "参与方域"

  - id: "R_002"
    head: "E_MERCHANT_商户"
    relation_type: "关联"
    tail: "E_SETTLE_结算账户"
    description: "商户绑定结算账户用于资金结算"
    cardinality: "1:N"
    source: "名词库"
    domain: "参与方域"

  - id: "R_003"
    head: "E_TRADE_交易订单"
    relation_type: "关联"
    tail: "E_REFUND_退款单"
    description: "已支付订单可发起退款，一个订单可多笔退款但累计不超过订单金额"
    cardinality: "1:N"
    source: "00-退款业务领域建模.md"
    domain: "交易域"

  - id: "R_004"
    head: "E_TRADE_交易订单"
    relation_type: "关联"
    tail: "E_SETTLE_结算账户"
    description: "交易资金结算到商户的结算账户"
    cardinality: "N:1"
    source: "34-交易领域模型.md"
    domain: "结算域"

  - id: "R_005"
    head: "E_MERCHANT_商户"
    relation_type: "关联"
    tail: "E_TRADE_交易订单"
    description: "商户收款产生交易订单"
    cardinality: "1:N"
    source: "34-交易领域模型.md"
    domain: "交易域"
```

### kg-rules.yaml

```yaml
meta:
  title: "微信支付商户领域业务规则"
  version: "v1.0"

rules:
  - id: "BR001"
    name: "退款金额上限校验"
    type: "validation"
    description: "单笔退款金额不能超过原交易订单的剩余可退金额。违反时拒绝退款请求，返回 REFUND_AMT_EXCEEDED。"
    involvedEntities: ["E_REFUND_退款单", "E_TRADE_交易订单"]
    condition: "refund_amount ≤ order_amount - already_refunded_amount"
    action: "允许退款，创建退款单"
    exception: "拒绝退款，返回错误码 REFUND_AMT_EXCEEDED"
    codeLocation: "refund_validator.cpp:ValidateRefundAmount()"
    priority: "critical"
    source: "平台商户系统-受理单笔退款(v2).md"

  - id: "BR002"
    name: "退款权限校验"
    type: "permission"
    description: "只有商户管理员角色才能发起退款操作。违反时拒绝请求，返回 NO_PERMISSION。"
    involvedEntities: ["E_MERCHANT_商户", "E_REFUND_退款单"]
    condition: "operator.role == '商户管理员'"
    action: "允许发起退款"
    exception: "拒绝退款，返回 NO_PERMISSION"
    priority: "critical"
    source: "平台商户系统-受理单笔退款(v2).md"

  - id: "BR003"
    name: "结算金额计算"
    type: "calculation"
    description: "商户结算金额 = 交易金额 - 平台服务费 - 已退款金额。用于每日结算对账。"
    involvedEntities: ["E_TRADE_交易订单", "E_SETTLE_结算账户"]
    condition: "settlement_amount = order_amount - service_fee - refunded_amount"
    action: "按计算结果生成结算记录"
    source: "结算领域模型.md"
```

### kg-flows.yaml

```yaml
meta:
  title: "微信支付商户领域业务流程"
  version: "v1.0"

flows:
  - id: "BF001"
    name: "受理单笔退款流程"
    description: "商户发起退款请求，系统校验参数和业务规则后执行扣款、记账和通知"
    triggerCondition: "商户调用退款 API（POST /v3/refund/domestic/refunds）"
    involvedEntities: ["E_REFUND_退款单", "E_TRADE_交易订单", "E_SETTLE_结算账户"]
    happyPath: "参数校验→权限校验→金额校验→创建退款单→扣款→记账→通知商户"
    steps:
      - order: 1
        actor: "退款服务"
        action: "校验请求参数完整性和格式"
        entityRef: "E_REFUND_退款单"
        codeEntry: "refund_service.cpp:ValidateParams()"
      - order: 2
        actor: "退款服务"
        action: "校验操作者退款权限"
        entityRef: "E_MERCHANT_商户"
        ruleRef: "BR002"
        codeEntry: "refund_service.cpp:CheckPermission()"
      - order: 3
        actor: "退款服务"
        action: "校验退款金额是否超限"
        entityRef: "E_TRADE_交易订单"
        ruleRef: "BR001"
        codeEntry: "refund_validator.cpp:ValidateRefundAmount()"
      - order: 4
        actor: "退款服务"
        action: "创建退款单并锁定资金"
        entityRef: "E_REFUND_退款单"
        codeEntry: "refund_service.cpp:CreateRefundOrder()"
        output: "退款单号"
      - order: 5
        actor: "资金服务"
        action: "从结算账户扣款"
        entityRef: "E_SETTLE_结算账户"
        codeEntry: "fund_service.cpp:Deduct()"
      - order: 6
        actor: "记账服务"
        action: "生成退款记账凭证"
        codeEntry: "accounting_service.cpp:CreateVoucher()"
      - order: 7
        actor: "通知服务"
        action: "推送退款结果通知给商户"
        entityRef: "E_MERCHANT_商户"
        codeEntry: "notify_service.cpp:SendRefundResult()"
    errorScenarios:
      - "金额超限（step 3）→ 返回 REFUND_AMT_EXCEEDED，不创建退款单"
      - "账户余额不足（step 5）→ 返回 NOTENOUGH，退款单标记失败"
      - "通知发送失败（step 7）→ 退款成功但异步重试通知"
    source: "平台商户系统-受理单笔退款(v2).md"
```

### kg-glossary.yaml

```yaml
meta:
  title: "微信支付商户领域术语表"
  version: "v1.0"

glossary:
  - term: "mchid"
    definition: "商户号，唯一标识一个商户主体的 10 位数字编码"
    entityRef: "E_MERCHANT_商户"
    fieldRef: "商户号"
    source: "名词库"

  - term: "FrefundAmt"
    definition: "退款金额，用户申请退回的资金数额，单位为分"
    entityRef: "E_REFUND_退款单"
    fieldRef: "退款金额"
    source: "代码分析"

  - term: "out_trade_no"
    definition: "商户订单号，商户系统内部的唯一订单标识"
    entityRef: "E_TRADE_交易订单"
    fieldRef: "商户订单号"
    source: "API 文档"

  - term: "RefundOrder"
    definition: "退款单实体类，对应业务概念中的退款单"
    entityRef: "E_REFUND_退款单"
    source: "代码分析"

  - term: "t_refund"
    definition: "退款单数据库表"
    entityRef: "E_REFUND_退款单"
    source: "DDL"
```

---

## 示例 2：完整 JSON 输出（AI 消费格式）

**输入**：名词（商户、门店、订单、退款、结算账户）+ 文档 + 代码路径

```json
{
  "meta": {
    "title": "微信支付商户领域知识图谱",
    "domain": "微信支付-商户管理",
    "version": "1.0",
    "createdAt": "2026-03-19",
    "description": "覆盖商户入驻、交易、退款、结算的核心概念和业务规则。AI 可基于此理解 merchant-service 代码的业务逻辑。",
    "sources": ["商户系统PRD", "结算设计文档"],
    "codeRepos": ["merchant-service/"],
    "aiUsageHint": "1. 读代码前先查 glossary（如 mchid=商户号）；2. 用 codeMapping 定位代码；3. 用 businessRules 理解校验逻辑；4. 用 businessFlows 理解调用链"
  },
  "glossary": {
    "mchid": { "definition": "商户号，唯一标识，10位数字", "entityRef": "E001" },
    "mch_id": { "definition": "同 mchid，数据库列名风格", "entityRef": "E001" },
    "store_id": { "definition": "门店ID", "entityRef": "E002" },
    "txn": { "definition": "transaction 缩写，指一笔交易/订单", "entityRef": "E003" },
    "order_no": { "definition": "订单号", "entityRef": "E003" },
    "refund_id": { "definition": "退款单号", "entityRef": "E004" },
    "refund_amt": { "definition": "退款金额，单位分", "entityRef": "E004" },
    "settle": { "definition": "结算，将交易资金划转到商户银行账户", "entityRef": "E005" },
    "acct_no": { "definition": "结算账户号", "entityRef": "E005" }
  },
  "entities": [
    {
      "id": "E001", "name": "商户", "enName": "Merchant", "type": "core",
      "description": "在微信支付平台注册并开展经营活动的法人或个人主体。商户是整个支付体系的核心参与者，所有交易、结算、退款都围绕商户展开。",
      "source": "名词库",
      "synonyms": ["mch", "merchant", "商家", "收款方"],
      "lifecycle": "入驻申请 → 审核中 → 已激活 → 已冻结(可选) → 已注销(可选)",
      "properties": [
        { "name": "商户号", "type": "string", "required": true, "codeField": "mchid", "dbColumn": "Fmch_id", "dbTable": "t_merchant_info" },
        { "name": "商户名称", "type": "string", "required": true, "codeField": "merchant_name" },
        { "name": "商户类型", "type": "enum", "enumValues": ["个体工商户", "企业", "政府及事业单位"] },
        { "name": "注册状态", "type": "enum", "enumValues": ["待审核", "已激活", "已冻结", "已注销"], "codeField": "mch_status" }
      ],
      "codeMapping": {
        "modules": ["merchant-service"],
        "classes": ["MerchantManager", "MerchantDAO"],
        "dbTables": ["t_merchant_info", "t_merchant_ext"],
        "apis": ["/v3/merchant/create", "/v3/merchant/query"]
      },
      "stateTransitions": [
        { "from": "待审核", "to": "已激活", "trigger": "审核通过" },
        { "from": "已激活", "to": "已冻结", "trigger": "风控冻结" },
        { "from": "已冻结", "to": "已激活", "trigger": "解冻" },
        { "from": "已激活", "to": "已注销", "trigger": "主动注销" }
      ],
      "tags": ["核心", "商户体系"]
    },
    {
      "id": "E002", "name": "门店", "enName": "Store", "type": "core",
      "description": "商户的线下经营场所。一个商户可拥有多个门店，门店是线下收款的最小经营单元。",
      "source": "名词库", "synonyms": ["store", "shop"],
      "properties": [
        { "name": "门店ID", "type": "string", "required": true, "codeField": "store_id", "dbColumn": "Fstore_id", "dbTable": "t_store_info" },
        { "name": "门店名称", "type": "string", "required": true },
        { "name": "所属商户号", "type": "string", "required": true, "codeField": "mchid" }
      ],
      "codeMapping": { "dbTables": ["t_store_info"], "classes": ["StoreManager"] }
    },
    {
      "id": "E003", "name": "订单", "enName": "Order", "type": "core",
      "description": "一次交易行为的完整记录。订单是支付体系的核心凭证，其状态变化驱动退款和结算流程。",
      "source": "名词库", "synonyms": ["order", "txn", "transaction"],
      "lifecycle": "创建 → 待支付 → 已支付 → 已关闭/已退款",
      "properties": [
        { "name": "订单号", "type": "string", "required": true, "codeField": "order_no", "dbTable": "t_order" },
        { "name": "订单金额", "type": "decimal", "required": true, "description": "单位：分", "codeField": "total_amount" },
        { "name": "已退款金额", "type": "decimal", "codeField": "refunded_amount" },
        { "name": "订单状态", "type": "enum", "enumValues": ["待支付", "已支付", "已关闭", "已退款"], "codeField": "order_status" }
      ],
      "codeMapping": { "modules": ["order-service"], "dbTables": ["t_order"], "classes": ["OrderManager"] },
      "stateTransitions": [
        { "from": "待支付", "to": "已支付", "trigger": "支付成功" },
        { "from": "待支付", "to": "已关闭", "trigger": "超时" },
        { "from": "已支付", "to": "已退款", "trigger": "全额退款" }
      ]
    },
    {
      "id": "E004", "name": "退款", "enName": "Refund", "type": "event",
      "description": "对已支付订单发起的资金退还操作。退款金额从商户账户扣除并原路返回给用户。一个订单可多笔退款但累计不超过订单金额。",
      "source": "名词库", "synonyms": ["refund", "退款单"],
      "properties": [
        { "name": "退款单号", "type": "string", "required": true, "codeField": "refund_id", "dbTable": "t_refund" },
        { "name": "退款金额", "type": "decimal", "required": true, "codeField": "refund_amt" },
        { "name": "退款状态", "type": "enum", "enumValues": ["处理中", "已退款", "退款失败"], "codeField": "refund_status" },
        { "name": "原订单号", "type": "string", "required": true, "codeField": "order_no" }
      ],
      "codeMapping": { "modules": ["refund-service"], "dbTables": ["t_refund"], "classes": ["RefundManager", "RefundValidator"], "apis": ["/v3/refund/domestic/refunds"] }
    },
    {
      "id": "E005", "name": "结算账户", "enName": "SettlementAccount", "type": "core",
      "description": "商户用于接收交易资金的银行账户。交易资金 T+1 自动结算到此账户。变更结算账户需严格审核。",
      "source": "名词库", "synonyms": ["settle_acct", "收款账户"],
      "properties": [
        { "name": "账户号", "type": "string", "required": true, "codeField": "acct_no", "dbTable": "t_settle_acct" },
        { "name": "开户行", "type": "string", "required": true },
        { "name": "户名", "type": "string", "required": true },
        { "name": "账户类型", "type": "enum", "enumValues": ["对公", "对私"] }
      ],
      "codeMapping": { "modules": ["settle-service"], "dbTables": ["t_settle_acct"] }
    }
  ],
  "relations": [
    { "id": "R001", "source": "E001", "target": "E002", "type": "contains", "label": "拥有", "cardinality": "1:N", "description": "商户拥有多个门店", "dataPath": "t_store_info.Fmch_id → t_merchant_info.Fmch_id" },
    { "id": "R002", "source": "E001", "target": "E005", "type": "associates", "label": "绑定", "cardinality": "1:N", "description": "商户绑定结算账户用于资金结算", "dataPath": "t_settle_acct.Fmch_id → t_merchant_info.Fmch_id" },
    { "id": "R003", "source": "E002", "target": "E003", "type": "produces", "label": "产生", "cardinality": "1:N", "description": "门店产生交易订单" },
    { "id": "R004", "source": "E003", "target": "E004", "type": "triggers", "label": "发起退款", "cardinality": "1:N", "description": "已支付订单可发起退款", "dataPath": "t_refund.Forder_no → t_order.Forder_no" },
    { "id": "R005", "source": "E003", "target": "E005", "type": "references", "label": "结算到", "cardinality": "N:1", "description": "交易资金结算到商户的结算账户" }
  ],
  "businessRules": [
    {
      "id": "BR001", "name": "退款金额校验", "type": "validation", "priority": "critical",
      "description": "退款金额不能超过可退金额（订单金额-已退款总金额）。防止资金损失的核心校验。",
      "involvedEntities": ["E004", "E003"],
      "condition": "refund_amount <= total_amount - refunded_amount",
      "action": "允许退款", "exception": "拒绝，返回 REFUND_AMOUNT_EXCEED",
      "codeLocation": "refund-service::RefundValidator::CheckRefundAmount()"
    },
    {
      "id": "BR002", "name": "退款订单状态校验", "type": "constraint", "priority": "critical",
      "description": "只有已支付的订单才能退款。确保退款只针对真实完成的交易。",
      "involvedEntities": ["E003", "E004"],
      "condition": "order_status == '已支付'",
      "action": "允许退款", "exception": "拒绝，返回 ORDER_STATUS_ERROR",
      "codeLocation": "refund-service::RefundValidator::CheckOrderStatus()"
    },
    {
      "id": "BR003", "name": "结算周期", "type": "flow_control", "priority": "major",
      "description": "交易资金 T+1 自动结算。监管合规要求。",
      "involvedEntities": ["E003", "E005"],
      "condition": "当前日期 > 交易日期 + 1", "action": "发起结算划转"
    }
  ],
  "businessFlows": [
    {
      "id": "BF001", "name": "商户退款流程",
      "description": "商户对已支付订单发起退款，资金原路返回给用户",
      "triggerCondition": "商户调用退款API或在商户平台操作",
      "involvedEntities": ["E001", "E003", "E004"],
      "steps": [
        { "order": 1, "actor": "商户", "action": "提交退款申请", "entityRef": "E004", "codeEntry": "POST /v3/refund/domestic/refunds" },
        { "order": 2, "actor": "系统", "action": "校验退款金额", "ruleRef": "BR001", "codeEntry": "RefundValidator::CheckRefundAmount()" },
        { "order": 3, "actor": "系统", "action": "校验订单状态", "ruleRef": "BR002", "codeEntry": "RefundValidator::CheckOrderStatus()" },
        { "order": 4, "actor": "系统", "action": "创建退款单", "entityRef": "E004", "codeEntry": "RefundManager::CreateRefund()" },
        { "order": 5, "actor": "系统", "action": "执行资金退回", "codeEntry": "FundService::ExecuteRefund()" },
        { "order": 6, "actor": "系统", "action": "更新订单和退款状态", "entityRef": "E003" },
        { "order": 7, "actor": "系统", "action": "通知商户", "codeEntry": "NotifyService::SendRefundNotify()" }
      ],
      "happyPath": "提交 → 金额校验 → 状态校验 → 创建退款单 → 资金退回 → 更新状态 → 通知",
      "errorScenarios": [
        "金额超限 → REFUND_AMOUNT_EXCEED",
        "状态不对 → ORDER_STATUS_ERROR",
        "资金退回失败 → 标记 REFUND_FAIL，触发重试"
      ]
    }
  ]
}
```

---

## 示例 2：基于图谱生成需求文档

**需求**："支持商户部分退款，允许一个订单分多次退款"

**AI 分析过程**：
1. 涉及实体：订单(E003)、退款(E004)
2. BR001 已支持累计校验 → 无需修改
3. BF001 步骤 6 需区分部分退款 vs 全额退款

**输出草稿**：

```markdown
## 需求：支持部分退款

### 实体变更
- **订单(E003)**：新增状态 `部分退款`，新增迁移 已支付→部分退款、部分退款→已退款
- **退款(E004)**：无变更

### 规则变更
- BR001：无需修改（已支持累计校验）
- 新增 BR004：单笔退款下限 ≥ 1 分

### 流程变更
- BF001 步骤 6：判断累计退款金额，=订单金额→已退款，<订单金额→部分退款

### 影响范围
- `OrderManager::UpdateOrderStatus()` 需增加部分退款判断
- R005（订单→结算账户）：部分退款后剩余金额正常结算，需确认逻辑
```
