---
name: api-gateway-integrator
description: 協助將服務整合到 API Gateway，支援新服務直接串接和舊服務灰度轉移兩種模式。當需要將服務透過 API Gateway 對外、設定流量分配、或從舊 VM 遷移到 K8s 時使用。
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# API Gateway Integrator Skill

自動化將服務整合到 API Gateway，包含新服務直接串接和舊服務灰度轉移。

## 核心功能

1. **新服務直接串接** - 將新的 K8s 服務透過 API Gateway 對外提供
2. **舊服務灰度轉移** - 從舊 VM 漸進式遷移到新 K8s 服務，使用 FeatureFlag 控制流量
3. **環境配置生成** - 自動產生 SIT/UAT/PROD 的設定
4. **Ingress 管理** - 設定 TLS 和路由規則

## 使用時機

當使用者提出以下需求時，啟用此 Skill：

- "幫我把 xxx 服務串接到 API Gateway"
- "我要做灰度轉移"
- "將服務從 VM 遷移到 K8s"
- "設定 API Gateway 流量分配"
- "新增 API Gateway route"

## 環境與 Domain 命名規則

| 環境 | Domain 格式 | 範例 |
|------|-------------|------|
| SIT | `sit-{service}.jkopay.app` | `sit-insurance.jkopay.app` |
| UAT | `uat-{service}.jkopay.app` | `uat-insurance.jkopay.app` |
| PROD | `{service}.jkopay.com` | `insurance.jkopay.com` |

> **注意**: PROD 環境不帶 env 前綴，且 domain 結尾是 `.com` 而非 `.app`

## 操作流程

### 前置收集資訊

在開始建立設定前，**必須**收集以下資訊：

#### 基本資訊
- **服務名稱**: 如 `insurance`、`payment`
- **整合模式**: 直接路由 / 灰度轉移
- **環境**: SIT / UAT / PROD

#### 如果是「灰度轉移」模式，還需要
- **舊服務 VM hostname**: 如 `rd3-python-04.jkopay.sit`
- **舊服務 nginx 設定**: 確認 port (通常 443) 和 server_name
- **Feature Flag Key**: 如 `migration-insurance-api`
- **需要控制的 API paths**: 如 `/insurance/entry`、`/insurance/refund`
- **Featbit EnvSecret**: 每個環境的 EnvSecret

### 資訊確認範例對話

```
Claude: 我將協助您將服務整合到 API Gateway。請提供以下資訊：

1. 整合模式
   - 直接路由：新服務直接透過 API Gateway 對外
   - 灰度轉移：舊 VM 服務漸進式遷移到新 K8s 服務

2. 基本資訊：
   - 服務名稱: (如 insurance)
   - 目標環境: (SIT / UAT / PROD)

[如果是灰度轉移]
3. 舊服務資訊：
   - 舊 VM hostname: (如 rd3-python-04.jkopay.sit)
   - 舊服務 port: (通常 443)
   - 舊服務是否為 HTTPS: (是/否)

4. Feature Flag 設定：
   - Feature Flag Key: (如 migration-xxx-api)
   - 需要控制的 API paths: (如 /api/entry, /api/callback)
```

---

## 兩種整合模式

| 模式 | 用途 | 路由方式 |
|------|------|----------|
| 直接路由 | 新服務直接對外 | 單一 destination |
| 灰度轉移 | 舊服務遷移到新服務 | FeatureFlag 控制流量 |

### 設定差異對照表

| 設定項目 | 直接路由模式 | 灰度轉移模式 |
|----------|--------------|--------------|
| LoadBalancingPolicy | (無) | FeatureFlag |
| RequestHeaderOriginalHost | 不需要 | 需要（舊 VM 檢查 Host） |
| DangerousAcceptAnyServerCertificate | 不需要 | 需要（舊 VM 憑證問題） |
| 目標服務 | 僅 K8s | K8s + 舊 VM |

---

## DNS 變更說明

灰度轉移的前提是將原始對外 domain 的 DNS 從舊 VM 改為指向 API Gateway。

### 變更前
```
用戶 → DNS → 舊 VM Nginx
             (Host: {domain})
```

### 變更後
```
用戶 → DNS → API Gateway → 舊 VM Nginx
                            (Host: {domain})
                               ↑
                         保留原始 Host
```

> **重點**: 舊服務的 Nginx 完全不需要修改！
>
> 因為 API Gateway 設定了 `RequestHeaderOriginalHost: true`，轉發時會保留原始的 Host header，所以舊服務 Nginx 收到的請求跟以前一樣，完全無感知這個轉變。
>
> 這也是灰度轉移的優點 — 可以隨時切回去，不需要改舊服務的任何設定。

---

## 需要修改的檔案

### 1. API Gateway ConfigMap
**檔案位置**: `jkopay-api-gateway/kustomize/overlays/{env}/idc/configMap.patch.yaml`

#### 1.1 新增 FeatbitSettings（僅灰度轉移需要）
```json
"FeatbitSettings": {
  "EnvSecret": "{環境對應的 EnvSecret}",
  "StreamingUri": "wss://flags.jkopay.com",
  "EventUri": "https://flags.jkopay.com",
  "StartWaitTime": 3000
}
```

#### 1.2 新增 FeatureFlagLoadBalancingSettings（僅灰度轉移需要）
```json
"FeatureFlagLoadBalancingSettings": {
  "ControlledDestination": "{service}-cluster/new",
  "DefaultDestination": "{service}-cluster/legacy",
  "UserKeyId": "Guid",
  "Rules": [
    {
      "Path": "/api/path1",
      "FeatureFlagKey": "migration-{service}-api",
      "DefaultValue": false
    }
  ]
}
```

#### 1.3 新增 Routes

**直接路由模式**
```json
"{service}-api": {
  "ClusterId": "{service}-api-cluster",
  "Match": {
    "Hosts": ["{domain}"]
  },
  "CorsPolicy": "AllowDefaultCors"
}
```

**灰度轉移模式**
```json
"{service}": {
  "ClusterId": "{service}-cluster",
  "Match": {
    "Hosts": ["{domain}"]
  },
  "Transforms": [
    { "RequestHeaderOriginalHost": "true" }
  ],
  "CorsPolicy": "AllowDefaultCors"
}
```

#### 1.4 新增 Clusters

**直接路由模式**
```json
"{service}-api-cluster": {
  "Destinations": {
    "{service}-api-destination": {
      "Address": "http://{env}-jkopay-{service}-api-svc:8080/"
    }
  }
}
```

**灰度轉移模式**
```json
"{service}-cluster": {
  "LoadBalancingPolicy": "FeatureFlag",
  "HttpClient": {
    "DangerousAcceptAnyServerCertificate": true
  },
  "Destinations": {
    "{service}-cluster/legacy": {
      "Address": "https://{legacy-vm-hostname}/"
    },
    "{service}-cluster/new": {
      "Address": "http://{env}-jkopay-{service}-api-svc:8080/"
    }
  }
}
```

### 2. API Gateway Ingress
**檔案位置**: `jkopay-api-gateway/kustomize/overlays/{env}/idc/ingress.patch.yaml`

#### 2.1 新增 TLS Hosts
```yaml
spec:
  tls:
    - hosts:
        # ... 現有 hosts ...
        - {domain}
      secretName: wildcard-jkopay-app-tls-secret  # SIT/UAT
      # secretName: wildcard-jkopay-com-tls-secret  # PROD
```

#### 2.2 新增 Ingress Rules
```yaml
rules:
  - host: {domain}
    http:
      paths:
        - pathType: Prefix
          path: "/"
          backend:
            service:
              name: jkopay-api-gateway-svc
              port:
                number: 8888
```

### 3. 停用原服務的 Ingress（僅灰度轉移需要）
**檔案位置**: `jkopay-{service}/kustomize/overlays/{env}/ingress.api.patch.yaml`

> **為什麼用 placeholder 而不是直接刪除？**
>
> 理想做法是直接刪除 ingress，但因為：
> 1. 通常不會一次轉移全部環境（SIT → UAT → PROD 逐步進行）
> 2. Ingress 定義在 `base/` 中，被所有環境共用
> 3. 無法在 base 刪除 ingress，否則會影響尚未轉移的環境
>
> 因此使用 placeholder host 作為過渡方案。
>
> **當所有環境都完成轉移後**，應該：
> 1. 從 `base/` 刪除 ingress 定義
> 2. 移除各環境的 `ingress.api.patch.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: jkopay-{service}-api-ing
  annotations:
    # This ingress is disabled - routing is handled by api-gateway
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: rd3-nginx
  rules:
    - host: unused.{service}.placeholder.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: jkopay-{service}-api-svc
                port:
                  number: 8080
```

---

## 驗證配置

建立完所有設定後，執行 kustomize build 驗證：

```bash
kustomize build {team}/{app}/kustomize/overlays/{env}
```

---

## 常見問題排查

### 502 Bad Gateway

可能原因：
1. **協定錯誤** - 舊 VM 是 HTTPS (443)，但 Address 用了 HTTP
2. **Host header 不對** - 舊服務 nginx 的 `server_name` 檢查失敗
3. **SSL 憑證驗證失敗** - 憑證 CN 不匹配連線的 hostname

解法：
- 確保 Address 使用 `https://`
- 加上 `RequestHeaderOriginalHost` transform
- 加上 `DangerousAcceptAnyServerCertificate: true`

---

## 完成遷移後的清理

當灰度轉移完成，所有流量都切換到新服務後：
1. 移除 cluster 中的 `legacy` destination
2. 移除 `LoadBalancingPolicy: "FeatureFlag"` 設定
3. 移除 `DangerousAcceptAnyServerCertificate` 設定
4. 移除 `FeatureFlagLoadBalancingSettings` 中的相關 rules
5. 下線舊 VM 服務
6. 從 `base/` 刪除原服務的 ingress 定義

---

## 參考資源

### 完整整合指南

- [API_GATEWAY_INTEGRATION_GUIDE.md](./API_GATEWAY_INTEGRATION_GUIDE.md) - 詳細步驟和案例說明

### Insurance 案例參考

- 實際設定檔: `rd3/jkopay-api-gateway/kustomize/overlays/uat/idc/configMap.patch.yaml`
- 包含完整的 routes、clusters、feature flag 設定

---

## 互動式範例

```
User: "幫我把 payment 服務整合到 API Gateway（灰度轉移模式）"

Claude:
我將協助您將 payment 服務整合到 API Gateway。

請提供以下資訊：

1. 目標環境: (SIT / UAT / PROD)
2. 舊 VM hostname: (如 rd3-python-05.jkopay.sit)
3. Feature Flag Key: (如 migration-payment-api)
4. 需要控制的 API paths: (如 /payment/create, /payment/callback)
5. Featbit EnvSecret: (該環境的 EnvSecret)

User: "UAT, rd3-python-05.jkopay.sit, migration-payment-api, /payment/create 和 /payment/callback"

Claude:
收到！讓我確認配置：

📋 配置摘要
- 服務: payment
- 環境: UAT
- 模式: 灰度轉移
- Domain: uat-payment.jkopay.app
- 舊 VM: rd3-python-05.jkopay.sit
- Feature Flag: migration-payment-api
- API Paths: /payment/create, /payment/callback

確認後我將開始修改設定檔。確認嗎？(yes/no)
```

---

## 總結

此 Skill 提供：
- 自動化 API Gateway 整合流程
- 支援直接路由和灰度轉移兩種模式
- 完整的設定檔修改
- 環境差異自動處理（SIT/UAT vs PROD）
- 清晰的驗證和問題排查指引
