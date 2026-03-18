# Argo Workflow YAML 範本

此文件包含所有必要的 YAML 範本，供 argo-workflow-integrator Skill 使用。

**重要：生成檔案時必須保留所有 TODO 和註解，這些是供維護人員參考的重要標記。**

---

## 1. kustomconfig.yaml

**位置**: `{team}/{app}/kustomize/overlays/{env}/kustomconfig.yaml`

```yaml
images:
  - path: spec/templates[]/container/image
    kind: WorkflowTemplate
```

---

## 2. Base WorkflowTemplate

**位置**: `{team}/{app}/kustomize/base/jobs/{team}-{app}-argojob-wt.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: {team}-{app}-argojob-wt #TODO: 通常會跟檔名一樣，請遵照格式命名 {team name}-{app-name}-wt
  namespace: {team} #TODO: 請修改team name
  annotations:
    #TODO: 為了管理後台查詢的方便，這邊請填上專案名稱(建議用git repo上名稱)，例如：jkopay-batchsystem, jkopay-insurance
    batchsystem/project: {app}
spec:
  serviceAccountName: {team}-batchsystem-sa #TODO: 請遵照格式命名 {team name}-batchsystem-sa
  imagePullSecrets:
    - name: jkopay-operator-garcfg
  arguments:
    parameters:
      - name: jobData
        value: default
      - name: instanceCount
        value: "1" #需要sharding時由sj填寫，這裡只是預設值，勿改
      - name: instanceId
        value: "1"
  templates:
    - name: main
      metadata:
        annotations:
          vault.hashicorp.com/agent-inject: "true"
          #TODO: 請遵照格式命名 {team name}-batchsystem，須找SRE申請新vault role
          vault.hashicorp.com/role: "{team}-batchsystem"
          vault.hashicorp.com/agent-pre-populate-only: "true"
          vault.hashicorp.com/agent-inject-secret-env-config: "secret/data/sit/{team}/app/{app}" #TODO: 下面的vault.hashicorp.com/agent-inject-template-env-config也要一起改
          vault.hashicorp.com/agent-inject-template-env-config: |
            {{{{- with secret "secret/data/sit/{team}/app/{app}" -}}}}
            {{{{- range $k, $v := .Data.data }}}}
            export {{{{ $k }}}}='{{{{ $v }}}}'
            {{{{- end }}}}
            exec "$@"
            {{{{- end }}}}
      metrics:
        prometheus:
          - name: job_execute_result_counter
            labels:
              - key: team
                value: '{{{{workflow.namespace}}}}'
              - key: name
                value: '{{{{workflow.parameters.templateName}}}}'
              - key: status
                value: '{{{{status}}}}'
            help: Count of execution by result status
            counter:
              value: '1'
          - name: job_execute_duration
            help: Duration of workflow execution
            labels:
              - key: team
                value: '{{{{workflow.namespace}}}}'
              - key: name
                value: '{{{{workflow.parameters.templateName}}}}'
              - key: status
                value: '{{{{status}}}}'
            gauge:
              realtime: false
              value: '{{{{duration}}}}'
      inputs:
        parameters:
          - name: jobData
          - name: instanceCount
          - name: instanceId
      container:
        #TODO: 請修改為實際的 image，若不清楚可詢問SRE，或參考kustomization.yaml的images，冒號後面的tagId僅為placeholder，不須與kustomization.yaml中相同，但請務必確認image存在
        image: {container-image}
        #TODO: 請修改為實際的 command
        command:
          - "bash"
          - "-c"
          - |
            source /vault/secrets/env-config && \
            {java-command}
```

---

## 3. Overlay WorkflowTemplate

**位置**: `{team}/{app}/kustomize/overlays/{env}/jobs/{team}-{app}-argojob-wt.patch.yaml`

### SIT 環境（使用 secretRef）

```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: {team}-{app}-argojob-wt #TODO: 通常會跟檔名一樣，請遵照格式命名 {team name}-{app-name}-wt
  namespace: {team} #TODO: 請修改team name
  labels:
    environment: sit #TODO: 請修改為實際的環境
spec:
  serviceAccountName: {team}-batchsystem-sa #TODO: 請遵照格式命名 {team name}-batchsystem-sa
  imagePullSecrets:
    - name: jkopay-operator-garcfg
  arguments:
    parameters:
      - name: jobData
        value: default
      - name: instanceCount
        value: "1" #需要sharding時由sj填寫，這裡只是預設值，勿改
      - name: instanceId
        value: "1"
  templates:
    - name: main
      metrics:
        prometheus:
          - name: job_execute_result_counter
            labels:
              - key: team
                value: '{{{{workflow.namespace}}}}'
              - key: name
                value: '{{{{workflow.parameters.templateName}}}}'
              - key: status
                value: '{{{{status}}}}'
            help: Count of execution by result status
            counter:
              value: '1'
          - name: job_execute_duration
            help: Duration of workflow execution
            labels:
              - key: team
                value: '{{{{workflow.namespace}}}}'
              - key: name
                value: '{{{{workflow.parameters.templateName}}}}'
              - key: status
                value: '{{{{status}}}}'
            gauge:
              realtime: false
              value: '{{{{duration}}}}'
      inputs:
        parameters:
          - name: jobData
          - name: instanceCount
          - name: instanceId
      container:
        #TODO: 請修改為實際的 image，若不清楚可詢問SRE，或參考kustomization.yaml的images，冒號後面的tagId僅為placeholder，不須與kustomization.yaml中相同，但請務必確認image存在
        image: {container-image}
        envFrom:
            - secretRef:
                name: sit-{app}-secret #TODO: 請修改為實際的 secret name，格式通常是 {env}-{app-name}-secret
        #TODO: 請修改為實際的 command (注意: SIT不需要source vault secrets)
        command:
          - "bash"
          - "-c"
          - |
            {java-command}
```

### UAT/PROD 環境（請參考該專案現有的 wt.patch.yaml 確認是使用 Vault 還是 secretRef）

```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: {team}-{app}-argojob-wt #TODO: 通常會跟檔名一樣，請遵照格式命名 {team name}-{app-name}-wt
  namespace: {team} #TODO: 請修改team name
  labels:
    environment: {env} #TODO: 請修改為實際的環境
spec:
  serviceAccountName: {team}-batchsystem-sa #TODO: 請遵照格式命名 {team name}-batchsystem-sa
  imagePullSecrets:
    - name: jkopay-operator-garcfg
  arguments:
    parameters:
      - name: jobData
        value: default
      - name: instanceCount
        value: "1" #需要sharding時由sj填寫，這裡只是預設值，勿改
      - name: instanceId
        value: "1"
  templates:
    - name: main
      metrics:
        prometheus:
          - name: job_execute_result_counter
            labels:
              - key: team
                value: '{{{{workflow.namespace}}}}'
              - key: name
                value: '{{{{workflow.parameters.templateName}}}}'
              - key: status
                value: '{{{{status}}}}'
            help: Count of execution by result status
            counter:
              value: '1'
          - name: job_execute_duration
            help: Duration of workflow execution
            labels:
              - key: team
                value: '{{{{workflow.namespace}}}}'
              - key: name
                value: '{{{{workflow.parameters.templateName}}}}'
              - key: status
                value: '{{{{status}}}}'
            gauge:
              realtime: false
              value: '{{{{duration}}}}'
      inputs:
        parameters:
          - name: jobData
          - name: instanceCount
          - name: instanceId
      container:
        #TODO: 請修改為實際的 image，若不清楚可詢問SRE，或參考kustomization.yaml的images，冒號後面的tagId僅為placeholder，不須與kustomization.yaml中相同，但請務必確認image存在
        image: {container-image}
        envFrom:
            - secretRef:
                name: {env}-{app}-secret #TODO: 請修改為實際的 secret name，格式通常是 {env}-{app-name}-secret
        #TODO: 請修改為實際的 command
        command:
          - "bash"
          - "-c"
          - |
            {java-command}
```

---

## 4. Base Schedule Job

**位置**: `{team}/{app}/kustomize/base/jobs/{team}-{job-name}-sj.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
metadata:
  #TODO: 請符合格式規範 => {team}-{job-name}-sj
  name: {team}-{job-name}-sj
  namespace: {team} #TODO: 請修改team name
  annotations:
    workflows.argoproj.io/description: |
      Shared CronWorkflow Process
    workflows.argoproj.io/version: ">= 3.2.0"
    #TODO: 為了管理後台查詢的方便，這邊請填上專案名稱(建議用git repo上名稱)，例如：jkopay-batchsystem, jkopay-insurance
    batchsystem/project: {app}
spec:
  schedule: "{cron-schedule}" #TODO: 請修改為實際的 schedule (!!!注意!!!只有5位數，最小單位是分鐘)
  timezone: "Asia/Taipei"
  concurrencyPolicy: "{concurrency-policy}" #TODO: 可用選項 {Allow, Forbid, Replace}
  workflowSpec:
    metrics:
      prometheus:
        - name: cronwf_execute_result_counter
          help: Count of execution by result status
          labels:
            - key: name
              value: '{{{{workflow.labels.workflows.argoproj.io/cron-workflow}}}}'
            - key: status
              value: '{{{{status}}}}'
            - key: workflowId
              value: '{{{{workflow.uid}}}}'
            - key: scheduledTime
              value: '{{{{workflow.scheduledTime}}}}'
          counter:
            value: '1'
        - name: cronwf_execute_duration
          help: Duration of cron workflow execution
          labels:
            - key: name
              value: '{{{{workflow.labels.workflows.argoproj.io/cron-workflow}}}}'
            - key: status
              value: '{{{{status}}}}'
          gauge:
            realtime: false
            value: '{{{{workflow.duration}}}}'
    workflowTemplateRef:
      # 重要: 不要手動添加環境前綴 (dev-, sit-)
      # 系統會自動處理環境前綴
      name: batchsystem-main-cron-workflow-template
    arguments:
      parameters:
        - name: templateName
          #TODO: 與*-wt.yaml 的 metadata.name 一致並加上環境前綴。請遵照格式命名 {env}-{team name}-{app-name}-wt
          value: sit-{team}-{app}-argojob-wt
        - name: jobData
          #為避免還沒有要上prod，就使用base的設定誤執行，所以先使用placeholder使得就算執行，也會因為參數錯誤而跳過
          value: placeholder
```

---

## 5. Overlay Schedule Job

**位置**: `{team}/{app}/kustomize/overlays/{env}/jobs/{team}-{job-name}-sj.patch.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
metadata:
  #TODO: 請符合格式規範 => {team}-{job-name}-sj
  name: {team}-{job-name}-sj
  namespace: {team} #TODO: 請修改team name
  annotations:
    workflows.argoproj.io/description: |
      Shared CronWorkflow Process
    workflows.argoproj.io/version: ">= 3.2.0"
    #TODO: 為了管理後台查詢的方便，這邊請填上專案名稱(建議用git repo上名稱)，例如：jkopay-batchsystem, jkopay-insurance
    batchsystem/project: {app}
  labels:
    environment: {env} #TODO: 請修改為實際的環境
spec:
  schedule: "{cron-schedule}" #TODO: 請修改為實際的 schedule (!!!注意!!!只有5位數，最小單位是分鐘)
  timezone: "Asia/Taipei"
  workflowSpec:
    metrics:
      prometheus:
        - name: cronwf_execute_result_counter
          help: Count of execution by result status
          labels:
            - key: name
              value: '{{{{workflow.labels.workflows.argoproj.io/cron-workflow}}}}'
            - key: status
              value: '{{{{status}}}}'
            - key: workflowId
              value: '{{{{workflow.uid}}}}'
            - key: scheduledTime
              value: '{{{{workflow.scheduledTime}}}}'
          counter:
            value: '1'
        - name: cronwf_execute_duration
          help: Duration of cron workflow execution
          labels:
            - key: name
              value: '{{{{workflow.labels.workflows.argoproj.io/cron-workflow}}}}'
            - key: status
              value: '{{{{status}}}}'
          gauge:
            realtime: false
            value: '{{{{workflow.duration}}}}'
    workflowTemplateRef:
      #TODO: 手動添加環境前綴 (uat-, sit-)，prod不用加。如果要有Sharding功能，請在最後添加(-sharding)。例如:sit-batchsystem-main-cron-workflow-template-sharding
      name: {workflowTemplateRef}
    arguments:
      parameters:
        - name: templateName
          #TODO: 與*-wt.yaml 的 metadata.name 一致並加上環境前綴。請遵照格式命名 {env !!!PROD則省略這部分!!!}-{team name}-{app-name}-wt
          value: {templateName}
        - name: jobData
          # JOB 所需要的參數 請使用 base64 字串
          # {decoded-json-comment}
          value: {base64-jobData}
```

---

## 變數替換說明

### 基本變數
- `{team}`: 團隊名稱（如 rd3, rd1）
- `{app}`: 應用程式名稱（如 jkopay-insurance）
- `{job-name}`: Job 名稱（如 legacy-retry-write-off）
- `{env}`: 環境（sit, uat, prod）

### WorkflowTemplate 變數
- `{container-image}`: Docker image 完整路徑
  - 格式: `asia-east1-docker.pkg.dev/jkopay-operator/app-docker-repository/{team}/{app}/{env}/argojob:{tag}`
- `{java-command}`: Java 啟動指令
  - 範例: `java -Xmx512m -Xms512m -Dspring.profiles.active=${PROFILE} -jar /app.jar {{{{workflow.uid}}}} {{{{workflow.name}}}} {{{{workflow.namespace}}}} {{{{inputs.parameters.jobData}}}} {{{{inputs.parameters.instanceCount}}}} {{{{inputs.parameters.instanceId}}}}`

### Schedule Job 變數
- `{cron-schedule}`: 5 位數 cron 表達式（如 "0 2 * * *"）
- `{concurrency-policy}`: Forbid, Allow, 或 Replace
- `{workflowTemplateRef}`: WorkflowTemplate 引用名稱
  - SIT: `sit-batchsystem-main-cron-workflow-template`
  - UAT: `uat-batchsystem-main-cron-workflow-template`
  - PROD: `batchsystem-main-cron-workflow-template`
  - Sharding: 加上 `-sharding` 後綴
- `{templateName}`: WorkflowTemplate 名稱
  - SIT: `sit-{team}-{app}-argojob-wt`
  - UAT: `uat-{team}-{app}-argojob-wt`
  - PROD: `{team}-{app}-argojob-wt`
- `{base64-jobData}`: Base64 編碼的 JSON
  - 原始格式: `{"jobName":"{job-class-name}","parameter":{job-parameters}}`
  - 使用 `echo -n` 進行 base64 編碼
- `{decoded-json-comment}`: jobData 的原始 JSON 內容，作為註解方便閱讀
  - 範例: `{"jobName":"DailyTransactionReportJob","parameter":{}}`

---

## 環境差異摘要

### Vault 路徑格式
- `secret/data/{env}/{team}/app/{app}`
- SIT: `secret/data/sit/rd3/app/jkopay-insurance`
- UAT: `secret/data/uat/rd3/app/jkopay-insurance`
- PROD: `secret/data/prod/rd3/app/jkopay-insurance`

### workflowTemplateRef（Schedule Job 使用）
- SIT: `sit-batchsystem-main-cron-workflow-template`
- UAT: `uat-batchsystem-main-cron-workflow-template`
- PROD: `batchsystem-main-cron-workflow-template`
- Sharding: 加上 `-sharding` 後綴

### templateName（Schedule Job 使用）
- SIT: `sit-{team}-{app}-argojob-wt`
- UAT: `uat-{team}-{app}-argojob-wt`
- PROD: `{team}-{app}-argojob-wt`

---

## Container Registry 資訊

- **Registry**: `asia-east1-docker.pkg.dev/jkopay-operator/app-docker-repository`
- **Image path**: `{team}/{app}/{env}/{role}:tag`
- **Common roles**: `api`, `batch`, `argojob`
- **Pull secret**: `jkopay-operator-garcfg`

---

## 重要規則

### 命名規則
1. 所有 `metadata.name` 必須**全小寫**
2. 只允許：小寫字母、數字、連字號 `-`
3. 不允許：大寫字母、底線 `_`、特殊符號

### TODO 註解保留規則
- **生成檔案時必須保留所有範本中的 TODO 和註解**
- 這些 TODO 是供後續維護人員參考的重要標記
- 即使變數已被替換為實際值，TODO 仍須保留

### Cron Schedule 格式
- **必須是 5 位數**: `分 時 日 月 週`
- **最小單位是分鐘**（不含秒位）
- 範例:
  - `0 2 * * *` - 每天凌晨 2:00
  - `*/30 * * * *` - 每 30 分鐘
  - `0 9-17 * * 1-5` - 週一到週五 9:00-17:00

### jobData 格式
- 必須 Base64 編碼
- 原始 JSON 結構:
  ```json
  {
    "jobName": "Java類別名稱",
    "parameter": {
      "key1": "value1",
      "key2": "value2"
    }
  }
  ```
- `jobName` 必須與 Java code 中 `getJobName()` 回傳值**完全一致**

### Vault Role 申請
- 格式: `{team}-batchsystem`
- 需向 SRE 團隊申請
- 每個 team 只需申請一次

---

## Kustomize 文件結構

### Base kustomization.yaml

```yaml
resources:
- jobs/{team}-{app}-argojob-wt.yaml
- jobs/{team}-{job-name}-sj.yaml
```

### Overlay kustomization.yaml

```yaml
configurations:
- kustomconfig.yaml

patches:
- path: jobs/{team}-{app}-argojob-wt.patch.yaml
  target:
    kind: WorkflowTemplate
    name: {team}-{app}-argojob-wt
- path: jobs/{team}-{job-name}-sj.patch.yaml
  target:
    kind: CronWorkflow
    name: {team}-{job-name}-sj
```
