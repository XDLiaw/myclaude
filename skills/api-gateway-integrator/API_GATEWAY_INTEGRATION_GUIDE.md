# API Gateway 服務整合教學

本文件說明如何將服務整合到 API Gateway，包含：
1. **新服務直接串接** - 透過 API Gateway 對外提供服務
2. **舊服務灰度轉移** - 從舊 VM 漸進式遷移到新 K8s 服務

以 **Insurance 保險服務** 為實際案例說明。

## 環境與 Domain 命名規則

| 環境 | Domain 格式 | 範例 |
|------|-------------|------|
| SIT | `sit-{service}.jkopay.app` | `sit-insurance.jkopay.app` |
| UAT | `uat-{service}.jkopay.app` | `uat-insurance.jkopay.app` |
| PROD | `{service}.jkopay.com` | `insurance.jkopay.com` |

> **注意**: PROD 環境不帶 env 前綴，且 domain 結尾是 `.com` 而非 `.app`

## 架構概覽

```
                         外部用戶
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
      {service-1}      {service-2}      (其他服務)
      .jkopay.xxx      .jkopay.xxx
            │               │
            └───────┬───────┘
                    ▼
             ┌────────────┐
             │  Ingress   │
             └─────┬──────┘
                   ▼
          ┌────────────────┐
          │  API Gateway   │
          └────────┬───────┘
                   │
       ┌───────────┴───────────┐
       │                       │
       ▼                       ▼
┌─────────────┐        ┌─────────────────┐
│ service-1   │        │ service-2       │
│ cluster     │        │ cluster         │
│ (直接路由)   │        │ (FeatureFlag LB)│
└──────┬──────┘        └────────┬────────┘
       │                        │
       ▼               ┌────────┴────────┐
┌─────────────┐        │                 │
│  新服務      │        ▼                 ▼
│  (K8s)      │   ┌─────────┐      ┌─────────┐
│             │   │ legacy  │      │  new    │
└─────────────┘   │ (舊 VM) │      │ (K8s)   │
                  └─────────┘      └─────────┘
```

## 兩種整合模式

| 模式 | 用途 | 路由方式 | 範例 |
|------|------|----------|------|
| 直接路由 | 新服務直接對外 | 單一 destination | `insurance-api` |
| 灰度轉移 | 舊服務遷移到新服務 | FeatureFlag 控制流量 | `insurance-pay` |

### Insurance 案例

| Domain | 用途 | 路由方式 |
|--------|------|----------|
| `{env}-insurance.jkopay.app` | 新保險服務 API | 直接路由到 K8s 服務 |
| `{env}-insurance-pay.jkopay.app` | 保險支付服務（灰度轉移中） | FeatureFlag 控制流量分配 |

## DNS 變更

灰度轉移的前提是將原始對外 domain 的 DNS 從舊 VM 改為指向 API Gateway。

### 變更前
```
用戶 → DNS → 舊 VM Nginx
             (Host: {env}-insurance-pay.jkopay.app)
```

### 變更後
```
用戶 → DNS → API Gateway → 舊 VM Nginx
                            (Host: {env}-insurance-pay.jkopay.app)
                               ↑
                         保留原始 Host
```

### DNS 記錄變更

| Domain | 變更前指向 | 變更後指向 |
|--------|-----------|-----------|
| `sit-insurance-pay.jkopay.app` | rd3-python-02.jkopay.sit | API Gateway Ingress |
| `uat-insurance-pay.jkopay.app` | rd3-python-04.jkopay.sit | API Gateway Ingress |
| `insurance-pay.jkopay.com` | (舊 VM) | API Gateway Ingress |

> **重點**: 舊服務的 Nginx 完全不需要修改！
>
> 因為 API Gateway 設定了 `RequestHeaderOriginalHost: true`，轉發時會保留原始的 Host header，所以舊服務 Nginx 收到的請求跟以前一樣，完全無感知這個轉變。
>
> 這也是灰度轉移的優點 — 可以隨時切回去，不需要改舊服務的任何設定。

## 需要修改的檔案

### 1. API Gateway ConfigMap
**檔案位置**: `jkopay-api-gateway/kustomize/overlays/{env}/idc/configMap.patch.yaml`

#### 1.1 新增 FeatbitSettings（Feature Flag 連線設定）
```json
"FeatbitSettings": {
  "EnvSecret": "{環境對應的 EnvSecret}",
  "StreamingUri": "wss://flags.jkopay.com",
  "EventUri": "https://flags.jkopay.com",
  "StartWaitTime": 3000
}
```

#### 1.2 新增 FeatureFlagLoadBalancingSettings（流量分配規則）
```json
"FeatureFlagLoadBalancingSettings": {
  "ControlledDestination": "insurance-pay-cluster/new",
  "DefaultDestination": "insurance-pay-cluster/legacy",
  "UserKeyId": "Guid",
  "Rules": [
    {
      "Path": "/insurance/entry",
      "FeatureFlagKey": "migration-insurance-api",
      "DefaultValue": false
    },
    {
      "Path": "/insurance/refund",
      "FeatureFlagKey": "migration-insurance-api",
      "DefaultValue": false
    },
    {
      "Path": "/insurance/inquiry",
      "FeatureFlagKey": "migration-insurance-api",
      "DefaultValue": false
    },
    {
      "Path": "/jkopay/server/onlinepay/result_callback",
      "FeatureFlagKey": "migration-insurance-api",
      "DefaultValue": false
    }
  ]
}
```

#### 1.3 新增 Routes

**insurance-api（新保險服務 API）**
```json
"insurance-api": {
  "ClusterId": "insurance-api-cluster",
  "Match": {
    "Hosts": ["{env}-insurance.jkopay.app"]
  },
  "CorsPolicy": "AllowDefaultCors"
}
```
> 此 route 直接將流量導向新的 K8s 保險服務，無需灰度控制。

**insurance-pay（保險支付 - 灰度轉移）**
```json
"insurance-pay": {
  "ClusterId": "insurance-pay-cluster",
  "Match": {
    "Hosts": ["{env}-insurance-pay.jkopay.app"]
  },
  "Transforms": [
    { "RequestHeaderOriginalHost": "true" }
  ],
  "CorsPolicy": "AllowDefaultCors"
}
```
> **重要**: 需要加上 `RequestHeaderOriginalHost` transform，確保轉發到舊服務時保留原始的 Host header，否則舊服務的 nginx 會因為 `server_name` 不匹配而拒絕請求。

#### 1.4 新增 Clusters

**insurance-api-cluster（新保險服務）**
```json
"insurance-api-cluster": {
  "Destinations": {
    "insurance-api-destination": {
      "Address": "http://{env}-jkopay-insurance-api-svc:8080/"
    }
  }
}
```
> 單純路由到新的 K8s 服務，無需特殊設定。

**insurance-pay-cluster（灰度轉移用）**
```json
"insurance-pay-cluster": {
  "LoadBalancingPolicy": "FeatureFlag",
  "HttpClient": {
    "DangerousAcceptAnyServerCertificate": true
  },
  "Destinations": {
    "insurance-pay-cluster/legacy": {
      "Address": "https://{legacy-vm-hostname}/"
    },
    "insurance-pay-cluster/new": {
      "Address": "http://{env}-jkopay-insurance-api-svc:8080/"
    }
  }
}
```

> **注意**:
> - `LoadBalancingPolicy: "FeatureFlag"` 啟用 feature flag 控制的流量分配
> - `DangerousAcceptAnyServerCertificate: true` 跳過 SSL 憑證驗證（因為舊 VM 的憑證 CN 可能不匹配）
> - 舊服務使用 `https://`（舊 VM nginx 監聽 443 port）

### 2. API Gateway Ingress
**檔案位置**: `jkopay-api-gateway/kustomize/overlays/{env}/idc/ingress.patch.yaml`

#### 2.1 新增 TLS Hosts
```yaml
spec:
  tls:
    - hosts:
        # ... 現有 hosts ...
        - {env}-insurance.jkopay.app
        - {env}-insurance-pay.jkopay.app
      secretName: wildcard-jkopay-app-tls-secret
```

#### 2.2 新增 Ingress Rules
```yaml
rules:
  # ... 現有 rules ...
  - host: {env}-insurance.jkopay.app
    http:
      paths:
        - pathType: Prefix
          path: "/"
          backend:
            service:
              name: jkopay-api-gateway-svc
              port:
                number: 8888
  - host: {env}-insurance-pay.jkopay.app
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

### 3. 停用 jkopay-insurance 原本的 Ingress
**檔案位置**: `jkopay-insurance/kustomize/overlays/{env}/ingress.api.patch.yaml`

> **為什麼用 placeholder 而不是直接刪除？**
>
> 理想做法是直接刪除 ingress，但因為：
> 1. 通常不會一次轉移全部環境（SIT → UAT → PROD 逐步進行）
> 2. Ingress 定義在 `base/` 中，被所有環境共用
> 3. 無法在 base 刪除 ingress，否則會影響尚未轉移的環境
>
> 因此使用 placeholder host 作為過渡方案，讓該環境的 ingress 實際上不生效。
>
> **當所有環境都完成轉移後**，應該：
> 1. 從 `base/` 刪除 ingress 定義
> 2. 移除各環境的 `ingress.api.patch.yaml`

將原本的 ingress 改成 placeholder，避免衝突：
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: jkopay-insurance-api-ing
  annotations:
    # This ingress is disabled - routing is handled by api-gateway
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: rd3-nginx
  rules:
    - host: unused.insurance.placeholder.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: jkopay-insurance-api-svc
                port:
                  number: 8080
```

### 4. 更新 jkopay-insurance kustomization.yaml
**檔案位置**: `jkopay-insurance/kustomize/overlays/{env}/kustomization.yaml`

加上註解說明 ingress 已移到 api-gateway：
```yaml
# ingress moved to api-gateway (rd3/jkopay-api-gateway)
patches:
- path: ./deployment.api.patch.yaml
# ...
```

## 環境對應表（Insurance 案例）

| 環境 | Domain | Legacy VM | 新服務 |
|------|--------|-----------|--------|
| SIT | `sit-insurance-pay.jkopay.app` | rd3-python-02.jkopay.sit | sit-jkopay-insurance-api-svc:8080 |
| UAT | `uat-insurance-pay.jkopay.app` | rd3-python-04.jkopay.sit | uat-jkopay-insurance-api-svc:8080 |
| PROD | `insurance-pay.jkopay.com` | (待確認) | jkopay-insurance-api-svc:8080 |

> **PROD 注意事項**:
> - Domain 不帶 env 前綴，使用 `.com` 結尾
> - K8s 服務名稱通常也不帶 env 前綴

## 設定摘要

### 通用對照表

| 設定項目 | 直接路由模式 | 灰度轉移模式 |
|----------|--------------|--------------|
| LoadBalancingPolicy | (無) | FeatureFlag |
| RequestHeaderOriginalHost | 不需要 | 需要（舊 VM 檢查 Host） |
| DangerousAcceptAnyServerCertificate | 不需要 | 需要（舊 VM 憑證問題） |
| 目標服務 | 僅 K8s | K8s + 舊 VM |

### Insurance 案例

| 設定項目 | insurance-api | insurance-pay |
|----------|---------------|---------------|
| 用途 | 新保險服務 API | 保險支付（灰度轉移） |
| 模式 | 直接路由 | 灰度轉移 |
| Cluster | insurance-api-cluster | insurance-pay-cluster |

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

### 舊服務 Nginx 設定參考

舊服務的 nginx 會檢查以下項目：
```nginx
server {
    listen    443    ssl;
    server_name  {env}-insurance-pay.jkopay.app;  # 檢查 Host header

    ssl_certificate      /etc/nginx/ssl/...;      # SSL 憑證
    ssl_certificate_key  /etc/nginx/ssl/...;

    location /insurance/ {
        proxy_set_header Host $host;              # 傳遞 Host 給後端
        # ...
    }
}
```

## 灰度控制

透過 Featbit 的 `migration-insurance-api` feature flag 控制流量比例：
- `false` (預設): 流量導向 legacy（舊 VM）
- `true`: 流量導向 new（新 K8s 服務）

可以在 Featbit 後台設定漸進式 rollout 比例。

## 完成遷移後

當灰度轉移完成，所有流量都切換到新服務後：
1. 移除 `insurance-pay-cluster` 中的 `legacy` destination
2. 移除 `LoadBalancingPolicy: "FeatureFlag"` 設定
3. 移除 `DangerousAcceptAnyServerCertificate` 設定
4. 移除 `FeatureFlagLoadBalancingSettings` 中的相關 rules
5. 下線舊 VM 服務
