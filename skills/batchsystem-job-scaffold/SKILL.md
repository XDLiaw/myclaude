---
name: batchsystem-job-scaffold
description: Use when generating BatchSystem Job application code (.NET or Java), including Job classes, parameter models, DI registration, Dockerfile, and optionally GitLab CI. Typically invoked as Step 2 after batchsystem-schedule-job.
---

# BatchSystem Job Scaffold — Step 2 of 3

## 角色

依據 `.batchsystem-job-config.json` 自動產生 App 端程式碼（.NET 或 Java）、Dockerfile，並可選設定 GitLab CI。

## Step 1：讀取設定檔

讀取工作目錄的 `.batchsystem-job-config.json`。

若檔案不存在，顯示：
```
❌ 找不到 .batchsystem-job-config.json
請先執行 /batchsystem-schedule-job 完成需求收集後再執行本 skill。
```

從設定檔取得以下關鍵值：
- `mode`：`create`（全新專案）或 `add`（既有專案新增 Job）
- `techStack`：`dotnet` 或 `java`
- `team`、`project`、`jobName`
- `jobData.{env}.parameter`：用來產生 Parameter Model 的欄位（取任一環境的 parameter 即可）
- `paths.appRepo`：App 專案路徑

---

## Step 2：確認 ProjectName（.NET 專用）

若 `techStack == "dotnet"` 且 `mode == "create"`，詢問使用者：

```
根據 project={project}，建議專案名稱為：{推導名稱}

例如：project=jkopay-insurance → JKOPay.Insurance.Job
     project=payment-gateway   → JKOPay.PaymentGateway.Job

請確認或輸入您想要的 ProjectName（直接 Enter 採用建議值）：
```

推導規則：將 `project` 以 `-` 分割，每段首字大寫，組合為 `JKOPay.{PascalCase}.Job`。

使用者確認 ProjectName 後，**立即將 `dotnetProjectName` 寫回 `{appRepo}/.batchsystem-job-config.json`**，供 Step 3（batchsystem-gitops-scaffold）使用：

```json
{
  "dotnetProjectName": "{ProjectName}"
}
```

---

## Step 2.5：掃描 App 路徑（決定補充清單）

在產生任何檔案之前，先掃描 `{appRepo}` 確認現有狀態，決定哪些檔案需要建立、哪些已存在。

> **techStack 分流**：以下掃描清單適用於 **.NET**。Java 的掃描項目見 Step 3 Java 章節。

### 掃描項目（.NET）

**根目錄（{appRepo}/）：**

| 檔案 | 掃描方式 |
|------|---------|
| `Directory.Packages.props` | Glob 檢查是否存在 |
| `nuget.config` | Glob 檢查是否存在 |
| `*.sln` | Glob 搜尋 |
| `.gitlab-ci.yml` | Glob 檢查是否存在 |
| `deployments/Dockerfile/argojob/Dockerfile` | Glob 檢查是否存在 |

**專案目錄（{appRepo}/src/{ProjectName}/）：**

| 檔案 | 掃描方式 |
|------|---------|
| `{ProjectName}.csproj` | Glob 檢查 |
| `Program.cs` | Glob 檢查 |
| `appsettings.json` | Glob 檢查 |
| `appsettings.local.json` | Glob 檢查 |
| `appsettings.development.json` | Glob 檢查 |
| `appsettings.sit.json` | Glob 檢查 |
| `Models/{JobName}Parameter.cs` | Glob 檢查 |
| `Models/Job/{JobName}.cs` | Glob 檢查 |

### 掃描結果展示

掃描完成後，展示以下摘要並請使用者確認：

```
📂 掃描結果：{appRepo}

根目錄：
  ✅ Directory.Packages.props（已存在，略過）
  ❌ nuget.config（不存在，將建立）
  ❌ JKOPay.PlatformSkill.Job.sln（不存在，將建立）
  ✅ .gitlab-ci.yml（已存在，略過）

專案目錄 src/{ProjectName}/：
  ✅ {ProjectName}.csproj（已存在，略過）
  ❌ Program.cs（不存在，將建立）
  ✅ appsettings.json（已存在，略過）
  ❌ Models/{JobName}Parameter.cs（不存在，將建立）
  ❌ Models/Job/{JobName}.cs（不存在，將建立）

共需建立 {n} 個檔案，略過 {m} 個已存在的檔案。

  (a) 確認，只建立缺少的檔案（預設）
  (b) 覆蓋所有檔案（包含已存在的）
  (c) 逐一確認

請選擇：
```

- 選 `(a)`：只建立掃描結果中標記 ❌ 的檔案
- 選 `(b)`：所有檔案都建立（已存在的會覆蓋）
- 選 `(c)`：每個檔案建立前個別詢問

### 特殊判斷：`Directory.Packages.props` 已存在時

若 `Directory.Packages.props` 已存在，讀取其內容，檢查是否已包含：
- `JKOPay.Platform.BatchSystem`

若缺少套件版本，提示：
```
⚠️ Directory.Packages.props 已存在，但缺少以下套件版本宣告：
  - JKOPay.Platform.BatchSystem（需要 0.2.0-beta1）

是否自動補充？[y/N]
```

### 特殊判斷：`.gitlab-ci.yml` 已存在時（同 Add 模式邏輯）

若 `.gitlab-ci.yml` 已存在，讀取其內容，檢查 `APP_ROLE.options` 是否包含 `argojob`，若無則提示補充。

---

## Step 3：依技術棧產生程式碼

### .NET

#### Create 模式（mode == "create"）

**優先使用 `dotnet new` 指令建立 scaffold**，再手動建立或覆寫各設定檔。

```bash
# Step 1：建立 solution 與 console project
cd {appRepo}
dotnet new sln -n {ProjectName}
dotnet new console -n {ProjectName} -o src/{ProjectName} --framework net10.0
dotnet sln add src/{ProjectName}/{ProjectName}.csproj

# Step 2：加入 BatchSystem SDK 套件（透過 Directory.Packages.props 管理版本）
# 手動建立 Directory.Packages.props（見下方模板）
# 然後修改 csproj 加入 PackageReference（見下方模板）
dotnet restore src/{ProjectName}/{ProjectName}.csproj
```

> ⚠️ **注意**：`dotnet new console` 會建立 `Program.cs`（含 Hello World）和基本 csproj。
> 建立後必須**覆寫**以下檔案以符合 BatchSystem 規格：
> - `{ProjectName}.csproj`（調整 TargetFramework、加入 PackageReference 和 appsettings ItemGroup）
> - `Program.cs`（替換為 BatchSystem 整合模板）
> - 新增所有 `appsettings.json` 檔案

產生以下 12 個檔案：

**src/{ProjectName}/ 目錄下（9 個）** + **{appRepo}/ 根目錄（3 個）**

---

### 根目錄檔案（放在 {appRepo}/）

---

**根目錄檔案 1：`Directory.Packages.props`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<Project>
  <PropertyGroup>
    <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>
  </PropertyGroup>
  <ItemGroup>
    <PackageVersion Include="JKOPay.Platform.BatchSystem" Version="0.2.0-beta1" />
  </ItemGroup>
</Project>
```

---

**根目錄檔案 2：`nuget.config`**

```xml
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <packageSources>
    <clear />
    <add key="nuget.org" value="https://api.nuget.org/v3/index.json" />
    <add key="JKOPay" value="https://gitlab.jkopay.app/api/v4/projects/593/packages/nuget/index.json" />
  </packageSources>
  <packageSourceMapping>
    <packageSource key="JKOPay">
      <package pattern="JKOPay.*" />
    </packageSource>
    <packageSource key="nuget.org">
      <package pattern="*" />
    </packageSource>
  </packageSourceMapping>
</configuration>
```

---

**根目錄檔案 3：`{ProjectName}.sln`**

```
Microsoft Visual Studio Solution File, Format Version 12.00
# Visual Studio Version 17
VisualStudioVersion = 17.0.0.0
MinimumVisualStudioVersion = 10.0.40219.1
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "{ProjectName}", "src\{ProjectName}\{ProjectName}.csproj", "{GUID}"
EndProject
Global
	GlobalSection(SolutionConfigurationPlatforms) = preSolution
		Debug|Any CPU = Debug|Any CPU
		Release|Any CPU = Release|Any CPU
	EndGlobalSection
	GlobalSection(ProjectConfigurationPlatforms) = postSolution
		{GUID}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{GUID}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{GUID}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{GUID}.Release|Any CPU.Build.0 = Release|Any CPU
	EndGlobalSection
EndGlobal
```

`{GUID}` 以 `Guid.NewGuid().ToString("B").ToUpper()` 產生（格式：`{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}`）。

---

### src/{ProjectName}/ 目錄下的檔案

---

**檔案 1：`{ProjectName}.csproj`**

```xml
<Project Sdk="Microsoft.NET.Sdk">
    <PropertyGroup>
        <OutputType>Exe</OutputType>
        <TargetFramework>net10.0</TargetFramework>
        <ImplicitUsings>enable</ImplicitUsings>
        <Nullable>enable</Nullable>
        <ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally>
    </PropertyGroup>

    <ItemGroup>
        <PackageReference Include="JKOPay.Platform.BatchSystem" />
    </ItemGroup>

    <ItemGroup>
        <None Update="appsettings.json">
            <CopyToOutputDirectory>Always</CopyToOutputDirectory>
        </None>
        <None Update="appsettings.local.json">
            <CopyToOutputDirectory>Always</CopyToOutputDirectory>
        </None>
        <None Update="appsettings.development.json">
            <CopyToOutputDirectory>Always</CopyToOutputDirectory>
        </None>
        <None Update="appsettings.sit.json">
            <CopyToOutputDirectory>Always</CopyToOutputDirectory>
        </None>
    </ItemGroup>
</Project>
```

---

**檔案 2：`Program.cs`**

`{Namespace}` 與 `{ProjectName}` 相同（即 `JKOPay.{PascalCase}.Job`）。
`{jobname_lowercase}` 為 `{jobName}` 全部轉小寫（移除連字號）。

```csharp
using JKOPay.Platform.BatchSystem;
using JKOPay.Platform.BatchSystem.Models;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using {Namespace}.Models.Job;

var env = Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT") ?? "local";

var host = Host.CreateDefaultBuilder(args)
    .SetBatchPlatform(args)
    .ConfigureHostConfiguration(config =>
    {
        config.Sources.Clear();
        config.AddEnvironmentVariables();
        config.AddJsonFile("appsettings.json", optional: false, reloadOnChange: false);
        config.AddJsonFile($"appsettings.{env}.json", optional: true, reloadOnChange: false);
    })
    .ConfigureServices((context, services) =>
    {
        // Register Jobs (key must be lowercase class name, no hyphens)
        services.AddKeyedScoped<IJob, {JobName}>("{jobname_lowercase}");
    })
    .Build();

var job = host.GetJob();
await job.ExecuteAsync();
```

---

**檔案 3：`appsettings.json`**

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information"
    }
  },
  "Serilog": {
    "MinimumLevel": "Information",
    "WriteTo": [
      {
        "Name": "Async",
        "Args": {
          "configure": [
            {
              "Name": "Console",
              "Args": {
                "formatter": "Serilog.Formatting.Json.JsonFormatter, Serilog"
              }
            }
          ]
        }
      }
    ],
    "Enrich": ["FromLogContext"]
  }
}
```

---

**檔案 4-6：`appsettings.{env}.json`**（結構相同，只有 Domain 不同）

```json
{
  "BatchSystemAPI": {
    "Domain": "{Domain}"
  }
}
```

| 檔案 | Domain |
|------|--------|
| `appsettings.local.json` | `https://batchsystem.foundation.dev:8443/` |
| `appsettings.development.json` | `http://dev-foundation-jkopay-batchsystem-api-svc:9090/` |
| `appsettings.sit.json` | `http://sit-foundation-jkopay-batchsystem-api-svc:9090/` |

---

**檔案 7：`Models/{JobName}Parameter.cs`**

從 `config.jobData.{任一env}.parameter` 的 key 自動推導 C# 屬性：

| JSON 值型別 | C# 型別 |
|-------------|---------|
| string      | `string` |
| integer     | `int` |
| float       | `double` |
| boolean     | `bool` |
| array       | `List<對應型別>` |

key 名稱轉為 PascalCase 作為屬性名。string 型別屬性預設值設為 `string.Empty`。

範例（parameter = `{ "batchSize": 100, "startDate": "2026-01-01" }`）：

```csharp
namespace {Namespace}.Models;

public class {JobName}Parameter
{
    public int BatchSize { get; set; }
    public string StartDate { get; set; } = string.Empty;
}
```

---

**檔案 8：`Models/Job/{JobName}.cs`**

```csharp
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using JKOPay.Platform.BatchSystem.Models;
using {Namespace}.Models;

namespace {Namespace}.Models.Job;

public class {JobName} : BaseJob, IJob
{
    private readonly ILogger<{JobName}> _logger;

    public {JobName}(ILogger<{JobName}> logger) : base(logger)
    {
        _logger = logger;
    }

    public override async Task ExecuteAsync(CancellationToken token = default)
    {
        var param = JsonConvert.DeserializeObject<{JobName}Parameter>(Arg!);
        _logger.LogInformation("Executing {JobName} with param: {@Param}", param);

        // TODO: Implement business logic here

        await Task.CompletedTask;
    }
}
```

---

**檔案 9：`Dockerfile`**

放置於 `{appRepo}/deployments/Dockerfile/argojob/Dockerfile`（GitLab CI 用）。

```dockerfile
FROM mcr.microsoft.com/dotnet/aspnet:10.0-alpine-composite AS base
WORKDIR /app

FROM mcr.microsoft.com/dotnet/sdk:10.0-alpine AS build
ARG BUILD_CONFIGURATION=Release
WORKDIR /src
COPY ["Directory.Packages.props", "./"]
COPY ["nuget.config", "./"]
COPY ["src/{ProjectName}/{ProjectName}.csproj", "src/{ProjectName}/"]
RUN dotnet restore "src/{ProjectName}/{ProjectName}.csproj"
COPY . .
WORKDIR "/src/src/{ProjectName}"
RUN dotnet build "{ProjectName}.csproj" -c $BUILD_CONFIGURATION -o /app/build

FROM build AS publish
ARG BUILD_CONFIGURATION=Release
RUN dotnet publish "{ProjectName}.csproj" -c $BUILD_CONFIGURATION -o /app/publish /p:UseAppHost=false

FROM base AS final
WORKDIR /app
COPY --from=publish /app/publish .
USER $APP_UID
ENTRYPOINT ["dotnet", "{ProjectName}.dll"]
```

---

#### Add 模式（mode == "add"）

只產生或修改 3 個項目：

1. **新增 `Models/{JobName}Parameter.cs`**（同 Create 模式的檔案 7）
2. **新增 `Models/Job/{JobName}.cs`**（同 Create 模式的檔案 8）
3. **修改 `Program.cs`**：找到最後一行 `services.AddKeyedScoped<IJob,` 後插入新的 DI 註冊：
   ```csharp
   services.AddKeyedScoped<IJob, {JobName}>("{jobname_lowercase}");
   ```

根目錄的 `Directory.Packages.props`、`nuget.config`、`.sln` 已存在，不重複建立。

---

### Java

#### 變數說明

| 變數 | 推導規則 | 範例 |
|------|---------|------|
| `{basePackage}` | `com.jkopay.` + project 去掉 `jkopay-` 前綴，移除連字號，全小寫 | `jkopay-insurance` → `com.jkopay.insurance` |
| `{JobClassName}` | `jobData.{env}.jobName` 首字大寫（camelCase → PascalCase） | `retryWriteoffJob` → `RetryWriteoffJob` |
| `{jobDataJobName}` | `jobData.{env}.jobName` 原值（必須與 jobData JSON 中的 jobName 一致） | `retryWriteoffJob` |

#### 掃描項目（Java）

掃描完成後展示結果並詢問使用者確認（同 .NET 的 Step 2.5 流程）。

| 檔案 | 掃描方式 |
|------|---------|
| `argojob/src/main/java/**/ArgoJobApplication.java` | Glob 搜尋 |
| `argojob/src/main/resources/application.yml` | Glob 檢查 |
| `argojob/src/main/java/**/{JobClassName}Job.java` | Glob 搜尋 |
| `argojob/src/main/java/**/{JobClassName}Parameter.java` | Glob 搜尋 |
| `deployments/Dockerfile/argojob/Dockerfile` | Glob 檢查 |
| `.gitlab-ci.yml` | Glob 檢查 |

> ⚠️ **Java 不需要修改 Application.java**：Spring 透過 `@Component` 自動掃描所有 Job 類別。
> 這與 .NET 不同，.NET 的 Add 模式需修改 `Program.cs` 手動註冊 DI key。

#### Create 模式（全新 argojob 模組）

產生 5 個檔案：

---

**檔案 1：`argojob/src/main/java/{basePackage}/ArgoJobApplication.java`**

```java
package {basePackage};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;

@EnableCaching
@SpringBootApplication(scanBasePackages = { "{basePackage}", "com.jkos.batchsystem" })
public class ArgoJobApplication {
    public static void main(String[] args) {
        SpringApplication.run(ArgoJobApplication.class, args);
    }
}
```

---

**檔案 2：`argojob/src/main/resources/application.yml`**

```yaml
spring:
  profiles:
    include:
      - core
```

---

**檔案 3：`argojob/src/main/java/{basePackage}/argojob/job/{JobClassName}Job.java`**

（同 Add 模式，見下方）

---

**檔案 4：`argojob/src/main/java/{basePackage}/argojob/model/{JobClassName}Parameter.java`**

（同 Add 模式，見下方）

---

**檔案 5：`deployments/Dockerfile/argojob/Dockerfile`**

```dockerfile
FROM maven:3.9-eclipse-temurin-17-alpine AS build
WORKDIR /workspace
COPY pom.xml .
COPY core/pom.xml core/
COPY argojob/pom.xml argojob/
RUN mvn dependency:go-offline -pl argojob -am -q
COPY core/src core/src
COPY argojob/src argojob/src
RUN mvn package -pl argojob -am -DskipTests -q

FROM eclipse-temurin:17-jre-alpine
COPY --from=build /workspace/argojob/target/argojob.jar /app.jar
ENTRYPOINT ["java", "-jar", "/app.jar"]
```

---

#### Add 模式（既有 argojob 模組新增 Job）

只產生 2 個檔案，**不需要修改任何現有檔案**（Spring 自動掃描 `@Component`）。

---

**Job 類別：`argojob/src/main/java/{basePackage}/argojob/job/{JobClassName}Job.java`**

```java
package {basePackage}.argojob.job;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import {basePackage}.argojob.model.{JobClassName}Parameter;
import com.jkos.batchsystem.constant.BatchSystemEnv;
import com.jkos.batchsystem.job.BaseArgoJob;
import com.jkos.batchsystem.model.ArgoJobInfo;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Component
@RequiredArgsConstructor
public class {JobClassName}Job extends BaseArgoJob<{JobClassName}Parameter> {

    @Value("${batchsystem.env}")
    private BatchSystemEnv batchSystemEnv;

    @Override
    public BatchSystemEnv getBatchSystemEnv() {
        return this.batchSystemEnv;
    }

    @Override
    public String getJobName() {
        return "{jobDataJobName}";
    }

    @Override
    public Class<{JobClassName}Parameter> getJobParameterClass() {
        return {JobClassName}Parameter.class;
    }

    @Override
    protected void run(ArgoJobInfo argoJobInfo, {JobClassName}Parameter jobParameter) {
        log.info("[{JobClassName}Job] 啟動排程, instanceId: {}/{}",
                argoJobInfo.getInstanceId(), argoJobInfo.getInstanceCount());
        // TODO: Implement business logic here
    }
}
```

若 Job 有需要注入 Service，以 `private final` 宣告（`@RequiredArgsConstructor` 自動產生建構子）：

```java
// 範例：注入 Service
private final WriteOffService writeOffService;
```

若需要 Prometheus metrics，加入 `@Timed`：

```java
import io.micrometer.core.annotation.Timed;
// 加在 class 上
@Timed(value = "job_execute_duration", percentiles = { 0.5, 0.95, 0.99 })
```

---

**Parameter 類別：`argojob/src/main/java/{basePackage}/argojob/model/{JobClassName}Parameter.java`**

從 `config.jobData.{任一env}.parameter` 的 key 自動推導 Java 欄位：

| JSON 值型別 | Java 型別 |
|-------------|----------|
| string      | `String` |
| integer     | `int` |
| float       | `double` |
| boolean     | `boolean` |
| array       | `List<對應型別>` |

key 名稱保持 camelCase 作為欄位名。

範例（parameter = `{ "batchSize": 100, "startDate": "20260101" }`）：

```java
package {basePackage}.argojob.model;

import com.jkos.batchsystem.model.ArgoJobParameter;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class {JobClassName}Parameter implements ArgoJobParameter {
    private int batchSize;
    private String startDate;
}
```

若 parameter 為空（無 parameter 欄位），產生空殼：

```java
package {basePackage}.argojob.model;

import com.jkos.batchsystem.model.ArgoJobParameter;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class {JobClassName}Parameter implements ArgoJobParameter {
    // TODO: 定義 Job 執行所需的參數
}
```

---

## Step 4：GitLab CI 設定（Optional）

詢問使用者：
```
需要幫忙設定 GitLab CI/CD 來自動建置和推送 argojob image 嗎？

  (a) 已經有了，不需要
  (b) 需要，幫我設定
  (c) 先跳過
```

選 `(a)` 或 `(c)` 則跳過此步驟。

選 `(b)` 則執行以下邏輯：

**Create 模式（無 .gitlab-ci.yml）**：在 `{appRepo}/` 建立 `.gitlab-ci.yml`：

```yaml
include:
  - project: "runner-configs/gitlab-shared-steps"
    ref: master
    file: "gitops/cicd.yaml"

stages:
  - info
  - build_and_delivery
  - deploy
  - autotest
  - notification

variables:
  ACTION:
    description: "CHOOSE ACTION"
    value: "build-and-delivery"
    options:
      - "none"
      - "build-and-delivery"
  REVISION:
    description: GIT REVISION
    value: HEAD
  BUILD_ENVIRONMENT:
    description: "Build Environment"
    value: "sit"
    options:
      - "sit"
      - "uat"
      - "prod"
  BUILD_BASE_IMAGE:
    value: "false"
    options:
      - "true"
      - "false"
  APP_ROLE:
    description: "app role"
    value: "all"
    options:
      - none
      - all
      - argojob
  TEAM_NAME: "{team}"
  PROJECT_NAME: "{project}"
  PLATFORM: "idc"
```

同時確保 `{appRepo}/deployments/Dockerfile/argojob/Dockerfile` 存在（內容同上述 Dockerfile 模板）。

**Add 模式（已有 .gitlab-ci.yml）**：

1. 讀取現有 `.gitlab-ci.yml`
2. 檢查 `APP_ROLE.options` 是否包含 `argojob`，沒有則插入
3. 檢查 `{appRepo}/deployments/Dockerfile/argojob/Dockerfile` 是否存在，不存在則建立

---

## Step 5：完成並交棒

顯示完成摘要：
```
✅ Step 2 完成！已產生以下檔案：
  [列出所有已產生或修改的完整路徑]

接下來進入 Step 3：GitOps 設定建立
請執行 /batchsystem-gitops-scaffold
```

然後自動呼叫 `/batchsystem-gitops-scaffold`。

---

## 錯誤處理

| 情境 | 處理方式 |
|------|----------|
| `.batchsystem-job-config.json` 不存在 | 提示執行 Step 1，停止 |
| `paths.appRepo` 路徑不存在 | 詢問使用者確認路徑，確認後自動建立目錄 |
| Add 模式但 `Program.cs` 找不到 | 顯示警告，請使用者手動確認路徑 |
| Java 模板不存在 | 顯示模板設定說明，停止 |
| 檔案已存在 | Step 2.5 掃描時標記 ✅，依使用者選擇（略過 / 覆蓋 / 逐一確認）處理 |
| `Directory.Packages.props` 缺少套件版本 | Step 2.5 偵測並提示補充，不整個覆蓋 |
