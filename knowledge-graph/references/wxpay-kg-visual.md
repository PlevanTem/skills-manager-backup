# 微信支付系统知识图谱 — 网状关系全景

> 基于工作区`业务知识/核心信息/`全部文件 + 业务知识/补充信息/微信支付名词列表0317.md
> + 业架业务知识库-test 知识库

---

## 一、知识图谱顶层架构

```plantuml
@startuml WxPay_Full_KG
!theme plain
skinparam backgroundColor #FAFAFA
skinparam package {
  BackgroundColor #E8F4FD
  BorderColor #1976D2
}
skinparam class {
  BackgroundColor #FFFFFF
  BorderColor #42A5F5
  ArrowColor #1565C0
  FontSize 11
}
skinparam note {
  BackgroundColor #FFF9C4
  BorderColor #F9A825
}
hide empty methods

title 微信支付系统知识图谱 — 全景本体

' =====================
' 参与方体系
' =====================
package "参与方体系" #EDE7F6 {
  class "自然人\nNaturalPerson" as NP #D1C4E9 {
    + 证件号+证件类型
    + 客户号（唯一）
  }
  class "证件真身\nCredentialsIdentity" as CI #D1C4E9 {
    + 财付通证件唯一标识
    + 证件类型
    + 证件号
  }
  class "微信账号\nWeChat" as WX #B39DDB {
    + openid
    + unionid
    + 微信号
  }
  class "微信支付账号\nWeChatPay" as WXPAY #9575CD {
    + uin（微信支付账号）
    + 实名等级：I/II/III类
    + 支付密码
  }
  class "普通商户\nMerchant" as MCH #B39DDB {
    + mchid（商户号）
    + 财付通商户号
    + 商户类别码(MCC)
    + 结算银行账户
  }
  class "服务商\nServiceProvider" as SP #9575CD {
    + sp_mchid（服务商商户号）
    + sp_appid
    + 受理产品权限
  }
  class "从业机构\nAcquiringBank" as BANK #7E57C2 {
    + 机构编码
  }
  class "清算机构\nClearing" as CLEAR #7E57C2 {
    + 清算机构商户号
    note: 银联/网联
  }
  class "品牌\nBrand" as BRAND #CE93D8 {
    + BrandId
    + BrandName
    + BrandLogo
    + BrandState
  }
  class "门店\nStore" as STORE #CE93D8 {
    + 门店外部ID
    + 门店地址
  }
  class "主体\nSubject" as SUBJ #D1C4E9 {
    + SubjectId
    + 主体类型
    + 营业执照
  }
}

' =====================
' 账户体系
' =====================
package "账户体系" #E8F5E9 {
  class "零钱账户\nWallet" as WALLET #A5D6A7 {
    + 可用余额
    + 冻结余额
    + 实名等级限额
  }
  class "零钱通\nQianbao" as LINGQT #81C784 {
    + 申购份额
    + 货币基金类型
    note: 1.0/1.5/2.0版本
  }
  class "银行卡(借记)\nDebitCard" as DC #A5D6A7 {
    + 卡号(PAN)
    + 银行预留手机号
    + 绑卡序列号
  }
  class "信用卡\nCreditCard" as CC #C8E6C9 {
    + 卡号(PAN)
    + 部分场景受限
  }
  class "商户资金账户\nMerchantFund" as MFA #66BB6A {
    + 基本账户(BASIC)
    + 手续费账户(FEES)
    + 经营账户(OPERATION)
    + 分账冻结户
    + 风控冻结户
    + 退款异常专户
  }
  class "支付分账户\nPayScoreAccount" as PSA #A5D6A7 {
    + 展示分
    + 真实分
    + 信用额度
  }
  class "零花钱账户\nPocketMoney" as PM #C8E6C9 {
    + 家长管控限额
    + 安全锁机制
  }
}

' =====================
' 交易体系
' =====================
package "交易体系" #FFF3E0 {
  class "支付订单\nPayOrder" as PO #FFE082 {
    + transaction_id
    + out_trade_no
    + trade_type(JSAPI/APP/NATIVE等)
    + 订单金额(分)
    + 支付成功时间
    + 订单状态
    + 资金流类型
    + 是否指定分账
  }
  class "退款单\nRefundOrder" as RO #FFCC80 {
    + refund_id
    + out_refund_no
    + 退款金额
    + 退款状态
    + 退款资金来源
    + 退款入账账户
  }
  class "结算单\nSettlementBill" as SB #FFE0B2 {
    + 计费费率
    + 结算金额
    + 应收/实收手续费
    + 结算入账账户类型
  }
  class "分账单\nProfitShare" as PS #FFAB91 {
    + 分账单号
    + 分账接收方列表
    + 分账比例/金额
    + 分账状态
  }
  class "委托扣款单\nDeductOrder" as DO #FFCC80 {
    + 合同号(contract_id)
    + 扣款金额
    + 扣款状态
  }
}

' =====================
' 协议体系
' =====================
package "协议体系" #FCE4EC {
  class "代扣协议\nDelegationContract" as DCON #F48FB1 {
    + contract_id
    + plan_id（模板ID）
    + 协议状态: SIGNED/TERMINATED
    + 签约时间
    + 有效期
  }
  class "支付分服务协议\nPayScoreAgreement" as PSC #F48FB1 {
    + 服务ID
    + 用户openid
    + 授权状态
  }
}

' =====================
' 产品/服务体系
' =====================
package "产品/服务体系" #E0F7FA {
  class "交易服务类型\nTxServiceType" as TST #80DEEA {
    + 服务ID（20xxx）
    + 产品类型
    + 地域（中国大陆/境外）
    + 连接模式（商户直连等）
  }
  class "产品权限\nProductPermission" as PP #80DEEA {
    + 商户号
    + 产品ID
    + 权限状态(已开通/申请中/未开通)
  }
  class "支付分服务\nPayScoreService" as PSV #4DD0E1 {
    + service_id
    + 服务名称
    + 服务门槛分
    + 扣费额度上限
  }
  class "支付分服务订单\nPayScoreOrder" as PSORD #4DD0E1 {
    + service_id
    + out_order_no（32位纯数字）
    + 服务状态
    + 后付费项目列表
  }
}

' =====================
' 营销体系
' =====================
package "营销体系" #F3E5F5 {
  class "代金券\nCoupon" as CPN #CE93D8 {
    + coupon_id
    + 券类型: CASH充值/NO_CASH非充值
    + 面额
    + 使用条件金额
    + 优惠标记(goodstag)
    + 券状态
  }
  class "商家券\nMerchantCoupon" as MCPN #CE93D8 {
    + card_id（批次号）
    + 券类型: NORMAL/DISCOUNT/EXCHANGE
  }
  class "企业红包\nEnterpriseRedPacket" as ERP #CE93D8 {
    + 红包金额
    + 发放类型
  }
  class "优惠活动\nPromotion" as PROMO #E1BEE7 {
    + 优惠ID
    + 活动类型
    + 投放计划
  }
}

' =====================
' 连接模式体系（关键）
' =====================
package "连接模式体系" #F1F8E9 {
  class "商户直连\nDirectConnect" as DCONN #AED581 {
    note: 商户直接对接微信支付\nmchid即收款账户
  }
  class "服务商直连\nSPConnect" as SPCONN #AED581 {
    note: sp_mchid + sub_mchid\n资金入子商户账户
  }
  class "机构直连\nInstDirect" as IDCONN #8BC34A {
    note: 从业机构直连清算
  }
  class "机构间连\nInstInter" as IICONN #8BC34A {
    note: 经银联/网联中转
  }
}

' =====================
' 核心关系网络
' =====================

' 用户体系
NP "1" --> "1..*" CI : 持有证件
NP --> WX : 注册
WX --> WXPAY : 开通支付
WXPAY --> WALLET : 拥有零钱账户
WXPAY --> DC : 绑定银行卡
WXPAY --> CC : 绑定信用卡
WXPAY --> PSA : 拥有支付分账户
WXPAY --> PM : 开通零花钱
WALLET --> LINGQT : 转入

' 商户体系
MCH --> SUBJ : 归属主体
MCH --> MFA : 拥有资金账户
MCH --> BRAND : 拥有品牌
BRAND --> STORE : 下设门店
SP "1" --> "0..*" MCH : 代理子商户

' 支付流程
WXPAY "0..*" --> "0..*" PO : 发起支付
MCH "1" --> "0..*" PO : 收款
PO --> TST : 使用交易服务类型
PO "1" --> "0..*" RO : 触发退款
PO "1" --> "0..1" SB : 触发结算
PO "1" --> "0..1" PS : 发起分账
PO "0..*" --> "0..*" CPN : 使用代金券

' 账户流水
SB --> MFA : 结算入账
RO --> WALLET : 退款入用户账户
RO --> MFA : 或退款入商户账户

' 代扣协议链路
WXPAY "0..*" --> "0..*" DCON : 签署代扣协议
DO "0..*" --> "1" DCON : 基于协议扣款
DO --> PO : 产生支付订单

' 支付分链路
WXPAY --> PSC : 授权支付分服务
MCH --> PSV : 注册支付分服务
PSORD "0..*" --> "1" PSC : 基于服务协议
PSORD "0..*" --> "1" PSV : 属于服务
PSORD --> PO : 后付款触发支付

' 产品权限
MCH --> PP : 开通产品权限
PP --> TST : 对应交易服务类型
TST --> DCONN : 商户直连模式
TST --> SPCONN : 服务商直连模式
TST --> IDCONN : 机构直连模式
TST --> IICONN : 机构间连模式

' 营销
MCH --> CPN : 发放代金券
MCH --> MCPN : 发放商家券
MCH --> ERP : 发放红包
MCH --> PROMO : 创建优惠活动
PROMO --> CPN : 包含代金券

@enduml
```

---

## 二、参与方体系详细关系图

```plantuml
@startuml WxPay_Participant_Detail
!theme plain
skinparam backgroundColor #FAFAFA
skinparam class {
  BackgroundColor #FFFFFF
  BorderColor #7E57C2
  ArrowColor #512DA8
  FontSize 10
}
hide empty methods

title 微信支付参与方体系 — 完整58种参与方的分类与关系

package "用户类" #F3E5F5 {
  class "自然人\n(56)" as NP
  class "证件真身\n(57)" as CI
  class "微信账号\n(48)" as WX
  class "微信支付账号\n(49)" as WXPAY
  class "钱包机构用户\n(55)" as WIU
  class "企微员工\n(52)" as WCE
}
package "商户主体类" #EDE7F6 {
  class "主体-企业\n(9)" as SubCo
  class "主体-个体工商户\n(8)" as SubInd
  class "主体-小微商户\n(12)" as SubMicro
  class "主体-其他组织\n(11)" as SubOrg
  class "主体-党政机关\n(10)" as SubGov
}
package "商户经营类" #D1C4E9 {
  class "普通商户\n(1)" as MCH {
    note: 直连商户
  }
  class "服务商\n(2)" as SP
  class "渠道商\n(5)" as CH
  class "财付通商户\n(46)" as TPM
  class "微信支付香港商户\n(47)" as HKMCH
}
package "机构类" #B39DDB {
  class "从业机构\n(4)\nAcquiringBank" as BANK {
    note: 银行/支付机构
  }
  class "清算机构\n(3)\nClearing" as CLEAR {
    note: 银联/网联
  }
  class "钱包机构\n(53)" as WI
  class "钱包网络\n(54)" as WN
}
package "平台/应用类" #9575CD {
  class "微信开放平台\n(6)" as WXOpen
  class "微信公众平台\n(7)" as WXMp
  class "微信小程序\n(24)" as WXMini
  class "微信App\n(26)" as WXApp
  class "网页\n(28)" as WEB
  class "QQ小程序\n(25)" as QQMini
  class "QQ App\n(27)" as QQApp
}
package "营销/场所类" #CE93D8 {
  class "品牌\n(13)" as BRAND
  class "门店\n(14)" as STORE
  class "固定场所\n(21)" as SV
  class "流动经营\n(22)" as IV
  class "交通工具\n(23)" as VH
  class "品牌连接规则\n(58)" as BCR
}
package "企业微信类" #7E57C2 {
  class "企微企业\n(51)" as WCCorp
  class "企微员工\n(52)" as WCEmp
}
package "特殊类" #5E35B1 {
  class "零花钱可穿戴设备\n(50)" as AWD
}

' 关键关系
NP --> CI : 持有证件
NP --> WX : 注册账号
WX --> WXPAY : 开通支付
WX --> WXMini : 使用小程序
MCH --> SubCo : 归属法人主体
MCH --> BRAND : 拥有品牌
BRAND --> STORE : 拥有门店
BRAND --> BCR : 关联规则
SP --> MCH : 代理子商户接入
CH --> BANK : 配合从业机构
BANK --> CLEAR : 接入清算
WI --> WN : 接入钱包网络
WIU --> WI : 归属机构
WCCorp --> WCEmp : 包含员工

@enduml
```

---

## 三、连接模式×产品×地域 三维关系图

```plantuml
@startuml WxPay_TxService_Matrix
!theme plain
skinparam backgroundColor #F8F9FA

title 交易服务类型 = 产品 × 地域 × 连接模式（来自交易服务类型.xlsx）

package "中国大陆 × 商户直连" #E3F2FD {
  class "APP支付\nID:20010" as A01
  class "扫码支付\nID:20013" as A02
  class "小程序支付\nID:20016" as A03
  class "JSAPI支付\nID:20026" as A04
  class "H5支付\nID:20028" as A05
  class "Native支付\nID:20031" as A06
  class "PC网页支付\nID:20034" as A07
  class "网页支付\nID:20060" as A08
}
package "中国大陆 × 服务商直连" #E8F5E9 {
  class "APP支付\nID:20011" as B01
  class "扫码支付\nID:20014" as B02
  class "小程序支付\nID:20017" as B03
  class "JSAPI支付\nID:20021" as B04
  class "H5支付\nID:20029" as B05
  class "Native支付\nID:20032" as B06
  class "PC网页支付\nID:20035" as B07
  class "国库支付\nID:20019" as B08
  class "还款支付\nID:20057" as B09
  class "网页支付\nID:20059" as B10
  class "APP-C2C电商\nID:20058" as B11
  class "小程序-C2C电商\nID:20020" as B12
}
package "中国大陆 × 机构间连" #FFF3E0 {
  class "APP支付\nID:20012" as C01
  class "扫码支付\nID:20015" as C02
  class "小程序支付\nID:20018" as C03
  class "JSAPI支付\nID:20027" as C04
  class "H5支付\nID:20030" as C05
  class "Native支付\nID:20033" as C06
  class "PC网页支付\nID:20036" as C07
  class "网页支付\nID:20061" as C08
}

note bottom
  交易服务类型 = 产品 × 地域 × 连接模式
  根节点 ID=10000：个人到单位交易服务-根
  二级技术产品：ID=1001x
  三级业务产品：ID=2xxxx
end note
@enduml
```

---

## 四、C2B支付流程 — 完整资金链路

```plantuml
@startuml WxPay_C2B_FundFlow
!theme plain
skinparam backgroundColor #FEFEFE
skinparam sequence {
  ArrowColor #1976D2
  LifeLineBackgroundColor #E3F2FD
  ParticipantBackgroundColor #BBDEFB
}

title C2B支付全链路（含资金账户变动）

actor "微信用户\n(WeChatPay)" as U
participant "商户系统" as M
participant "微信支付\n收款域" as WXP
participant "财付通\n清算" as CFT
participant "用户资金账户\n(零钱/银行卡)" as UA
participant "商户资金账户\n(待结算)" as MA
database "交易订单\nDB" as DB

U -> M: 触发支付（扫码/唤起支付面板）
M -> WXP: 下单请求\n(mchid/sp_mchid+sub_mchid/金额/触点信息)
WXP -> DB: 创建PayOrder [NOTPAY]
WXP --> M: 返回prepay_id/code_url
M --> U: 唤起收银台 / 展示二维码

U -> WXP: 确认支付（密码/指纹/刷脸）
WXP -> CFT: 扣款请求
CFT -> UA: 扣减用户账户\n(零钱/银行卡)
UA --> CFT: 扣款成功
CFT -> MA: 商户待结算+金额\n(PENDING)
CFT --> WXP: 扣款成功
WXP -> DB: 更新PayOrder [SUCCESS]

WXP -> M: 支付成功异步通知\n(transaction_id/payer_total/优惠信息)
M --> WXP: 200 OK 确认

note right of CFT
  优惠券处理：
  CASH券：占商户资金
  NO_CASH券：微信垫付
  payer_total = 订单金额 - 优惠金额
end note

note right of MA
  资金状态：
  PENDING → 待结算
  T+1后 → AVAILABLE可用
  分账场景 → FROZEN冻结
end note

@enduml
```

---

## 五、退款领域完整关系图

```plantuml
@startuml WxPay_Refund_Detail
!theme plain
skinparam backgroundColor #FEFEFE
skinparam class {
  BackgroundColor #FFFFFF
  BorderColor #E53935
  ArrowColor #B71C1C
}
hide empty methods

title 微信支付退款领域 — 完整实体关系（来源：退款业务领域建模.png + 知识库用例规约）

package "申请方" #FFEBEE {
  class "商户/服务商" as MREFUND {
    + 商户号
    + 服务商商户号（可选）
    + 子商户号（可选）
  }
}

package "退款单聚合根" #FCE4EC {
  class "退款单\nRefundOrder" as RO {
    + refund_id（31位）
    + out_refund_no（商户唯一）
    + 退款金额
    + 退款状态
    + 退款资金来源
    + 退款入账账户
    + 反向结算成功时间
    + 商户手续费退还时间
  }
  class "退款收款人规则" as RRULE {
    + 决定退款接收方
  }
}

package "关联订单" #FFF3E0 {
  class "支付订单\nPayOrder" as PO {
    + transaction_id
    + 订单金额
    + 有优惠信息
  }
}

package "资金账户" #E8F5E9 {
  class "商户资金账户" as MA {
    + 基本账户
    + 可用余额（AVAILABLE）
    + 未结算资金（UNSETTLED）
    + 退款异常专户
  }
  class "用户账户" as UA {
    + 零钱账户
    + 零钱通
    + 银行卡账户
  }
}

package "结算系统" #E3F2FD {
  class "反向结算" as RS {
    + 从商户账户扣减
    + 退还手续费
  }
}

' 关系
MREFUND --> RO : 申请退款
RO --> PO : 关联原始订单
RO --> RRULE : 依据规则选择收款方
RRULE --> UA : 退款到用户账户（原路退回）
RRULE --> MA : 退款到商户账户（异常场景）
MA --> RO : 提供退款资金来源\n(优先UNSETTLED)
RO --> RS : 触发反向结算
RS --> MA : 扣减手续费

note right of RO
  退款状态机：
  PROCESSING → 处理中
  SUCCESS → 成功
  FAIL → 失败
  CHANGE → 异常（银行卡作废/冻结）
end note

note right of MA
  资金来源优先级：
  1. 未结算资金(UNSETTLED)
  2. 可用余额(AVAILABLE)
  3. 服务商垫资(申请开通)
end note

@enduml
```

---

## 六、支付分系统完整关系图

```plantuml
@startuml WxPay_PayScore
!theme plain
skinparam backgroundColor #FEFEFE
skinparam class {
  BackgroundColor #FFFFFF
  BorderColor #6A1B9A
  ArrowColor #4A148C
}
hide empty methods

title 微信支付分系统 — 完整领域模型

class "微信用户\nWeChatUser" as U
class "支付分账户\nPayScoreAccount" as PSA {
  + 展示分（对外可见）
  + 真实分（内部计算）
  + 信用额度
  + 冻结额度
  + 逾期待还金额
}
class "支付分服务\nPayScoreService" as PSV {
  + service_id（唯一）
  + 服务名称
  + 一级/二级分类
  + 服务门槛分
  + 扣费额度上限
  + 按计划扣费次数上限
}
class "支付分服务模板\nServiceTemplate" as PSTPL {
  + plan_id
  + 模板一级分类名称
  + 免确认页配置
  + 创结单模式配置
}
class "支付分服务协议\nPayScoreAgreement" as PSAGR {
  + 商户号 + AppID（唯一确定）
  + 服务ID
  + 用户OpenID
  + 授权状态
}
class "支付分服务订单\nPayScoreOrder" as PSORD {
  + service_id
  + out_order_no（32位纯数字）
  + 服务状态
  + 后付费项目列表（最多10条）
  + 商户优惠列表（最多10条）
  + 总收款金额
}
class "支付分收款单\nPayScoreCollection" as PSCO {
  + 间连模式收款单号
  + 收款金额
  + 关联收款渠道
}
class "支付分运营账号\nPayScoreAdmin" as PSADM {
  + 商户号 + AppID确定
  + 绑定服务ID
  + 绑定状态
}
class "押金单\nDeposit" as DEP {
  + 押金单号
  + 押金金额
  + 押金状态
  + 行业类型
}

' 关系
U --> PSA : 拥有支付分账户
U --> PSAGR : 授权服务协议
PSV --> PSTPL : 基于模板配置
PSV --> PSAGR : 对应服务协议
PSORD --> PSAGR : 基于服务协议
PSORD --> PSV : 属于服务
PSORD --> PSCO : 对应收款单
PSORD --> DEP : 可关联押金单（免押/缴押）
PSV --> PSADM : 绑定运营账号

note right of PSA
  展示分规则：
  首次开通：真实分<阈值→直接设下限
  展示分有上下限约束
  逾期状态影响可用服务
end note

note right of PSORD
  创结单模式（免确认）：
  商户直接对用户扣款
  无需用户二次确认
end note

@enduml
```

---

## 七、商户入驻与主体体系

```plantuml
@startuml WxPay_Merchant_Onboard
!theme plain
skinparam backgroundColor #FEFEFE

title 微信支付商户入驻体系（含主体类型 × 连接模式）

package "商户主体类型" #EDE7F6 {
  class "企业\nCompany(9)" as CO
  class "个体工商户\nIndividualBusiness(8)" as IB
  class "小微商户\nMicroMerchant(12)" as MM
  class "党政机关\nInstitution(10)" as GOV
  class "其他组织\nOtherOrg(11)" as OO
}

package "商户接入类型" #E3F2FD {
  class "普通商户\n(直连，类型1)" as MCH {
    + 独立商户号
    + 费率由微信支付设置
    + 直接对接API
  }
  class "特约商户/子商户\n(服务商代理)" as SUBM {
    + sub_mchid
    + 资金直接入账
    + 不能直接调API
  }
  class "二级商户\n(平台收付通)" as L2M {
    + 资金冻结
    + 平台解冻
    + 合单支付
  }
}

package "入驻流程" #FFF3E0 {
  class "入驻申请单" as APP {
    + 营业执照
    + 法人信息
    + 商户类别码MCC
    + 银行账户信息
  }
  class "开户意愿验证" as OW {
    + 法人扫码
    + 视频验证
    + 承诺函
  }
  class "法人身份核验" as LV {
    + 实名认证一致性
    + 上行打款验证
    + 刷脸认证
  }
  class "产品权限开通" as PP {
    + 基础收款权限
    + 特殊产品申请
    + 分账权限
  }
}

' 关系
CO --> MCH : 申请直连商户
IB --> MCH : 申请直连商户
MM --> SUBM : 特约商户
MCH --> APP : 提交入驻申请
APP --> OW : 需验证开户意愿
APP --> LV : 需验证法人身份
APP --> PP : 审核通过后开通权限
SUBM --> MCH : 归属服务商代理

note bottom
  超管（Admin）：商户平台最高权限管理员
  超管变更需通过：上行打款 / 刷脸认证
end note

@enduml
```

---

## 八、账户体系与资金流向全景

```plantuml
@startuml WxPay_Account_FundFlow
!theme plain
skinparam backgroundColor #F8F9FA

title 微信支付账户体系 × 资金流向全链路

package "用户侧账户" #FFF8E1 {
  rectangle "零钱账户\nWallet" as WA #FFE082
  rectangle "零钱通\nQianbao\n（货币基金）" as QT #FFD54F
  rectangle "银行借记卡" as DC #FFCA28
  rectangle "信用卡" as CC #FFB300
  rectangle "零花钱账户" as PM #FFA000
}

rectangle "微信支付\n清算层\n（财付通）" as CFT #E3F2FD

package "商户侧账户" #E8F5E9 {
  rectangle "基本账户\nBASIC\n（待结算/可用）" as BASIC #A5D6A7
  rectangle "手续费账户\nFEES" as FEES #66BB6A
  rectangle "分账冻结户\nFROZEN_SHARE" as FRZ_S #81C784
  rectangle "风控冻结户\nFROZEN_RISK" as FRZ_R #C8E6C9
  rectangle "退款异常专户\nABNORMAL" as ABN #DCEDC8
}

rectangle "分账接收方账户\n（其他商户）" as SHAREE #F3E5F5
rectangle "用户银行账户\n（提现/退款目标）" as BANKA #FFF3E0

' 支付流程
WA --> CFT : C2B支付（零钱）
DC --> CFT : C2B支付（银行卡）
CC --> CFT : C2B支付（信用卡，部分受限）
QT --> CFT : C2B支付（零钱通）
CFT --> BASIC : 收款成功→待结算入账
BASIC --> BASIC : T+1结算：PENDING→AVAILABLE

' 手续费
BASIC --> FEES : 扣除手续费
FEES --> CFT : 手续费转微信支付

' 退款流程
BASIC --> CFT : 退款资金来源（未结算/可用余额）
CFT --> WA : 退款到用户零钱
CFT --> BANKA : 退款到用户银行卡
CFT --> ABN : 退款异常（银行卡冻结/作废）

' 分账流程
BASIC --> FRZ_S : 支付成功+分账标记→冻结
FRZ_S --> SHAREE : 分账完成→解冻转入
FRZ_S --> BASIC : 分账完成→剩余解冻回基本账户

' 风控流程
BASIC --> FRZ_R : 风控介入冻结

' 用户提现
WA --> BANKA : 用户提现到银行卡
QT --> WA : 赎回零钱通

note left of CFT
  清算层处理：
  - 收单验证
  - 反洗钱检查
  - 跨行清算
  - 跨境换汇
end note

@enduml
```

---

## 九、微信支付系统全子域图（来自知识库文档路径结构）

以下是从业架业务知识库提取的**确定性正确的子域结构**：

```plantuml
@startuml WxPay_SubDomain
!theme plain
skinparam backgroundColor #F8F9FA
skinparam package {
  BackgroundColor #E8F4FD
  BorderColor #1976D2
}

title 微信支付系统子域全景图（来源：业架业务知识库-test）

package "微信支付系统" as WXPAY_SYS #EDE7F6 {
  package "C2B交易" {
    [付款码支付]
    [扫码支付]
    [JSAPI支付]
    [小程序支付]
    [APP支付]
    [H5支付]
    [PC网页支付]
    [刷脸支付]
  }
  package "商业退款" {
    [境内退款]
    [境外退款]
  }
  package "结算" {
    [收款结算]
    [商业收款结算]
  }
  package "分账" {
    [分账]
  }
  package "商户入驻" {
    [境内商户]
    [跨境商户]
  }
  package "商户基础" {
    [产品权限]
    [商户基础信息]
  }
  package "商户运营管理" {
    [产品权限运营]
    [商户风险管理]
  }
  package "用户信息" {
    [用户信息]
  }
  package "实名" {
    [实名认证]
  }
  package "用户支付方式" {
    [支付方式管理]
    [支付方式运营]
  }
  package "参与方运营" {
    [参与方定义]
    [参与方运营]
    [商户运营]
  }
  package "参与方关系运营" {
    [参与方关系定义]
    [参与方关系运营]
  }
  package "地域连接模式运营" {
    [地域连接模式定义]
  }
  package "境外" {
    [跨境支付]
    [资源活动立项管理]
  }
  package "客服服务" {
    [帮助中心]
    [商户服务]
  }
  package "业管运营工具" {
    [产品权限审批]
  }
}

package "微信支付分系统" as WXPAYSCORE #F3E5F5 {
  [支付分账户管理]
  [支付分服务授权]
  [支付分订单]
}

package "微信群收款系统" as WXGROUP #FFF3E0 {
  [群收款]
}

package "微信用户订单系统" as WXORDER #E8F5E9 {
  [购物订单]
}

package "在线业务研发支撑系统" as DEVOPS #E3F2FD {
  [契约管理]
  [系统需求]
  [系统数据权限管理]
}

@enduml
```
