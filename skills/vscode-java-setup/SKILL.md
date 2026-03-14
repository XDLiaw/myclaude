---
name: vscode-java-setup
description: 協助將 Eclipse / STS 的 Java 專案啟動設定遷移到 VS Code，包含 launch.json 轉換、環境變數設定、中文 log 亂碼修復。當需要在 VS Code 執行 Spring Boot 或 Argo Job、從 STS 匯出設定轉換格式、或解決 terminal 中文亂碼時使用。
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
---

# VS Code Java Setup Skill

協助將 Eclipse / STS 的啟動設定遷移到 VS Code，讓 Spring Boot app 和 Argo Job 可以在 VS Code 正常執行。

## 核心功能

1. **STS launch config 轉換** - 將 `.launch` 檔案轉為 VS Code `launch.json`
2. **中文 log 亂碼修復** - 修復 Windows PowerShell 的 UTF-8 encoding 問題
3. **必要 Extension 清單** - 確認 Java 開發必要套件已安裝

## 使用時機

- "幫我把 STS 的啟動設定轉到 VS Code"
- "VS Code 跑 Spring Boot log 中文亂碼"
- "VS Code 要裝哪些 Java extension"
- "launch.json 怎麼設定"

---

## Extension 清單

必要 extensions（缺少則安裝）：

```bash
code --list-extensions | grep -i -E "java|spring|boot|maven"
```

| Extension ID | 功能 |
|---|---|
| `redhat.java` | Java 核心語言支援（LSP） |
| `vscjava.vscode-java-pack` | Java Extension Pack |
| `vscjava.vscode-java-debug` | Debugger |
| `vscjava.vscode-java-test` | Test Runner (JUnit) |
| `vscjava.vscode-maven` | Maven 整合 |
| `vscjava.vscode-spring-boot-dashboard` | Spring Boot Dashboard |

安裝指令：
```bash
code --install-extension vscjava.vscode-spring-boot-dashboard
```

---

## STS launch config 轉換

### Step 1: 找到 STS 匯出的 .launch 檔案

STS 可從 Run Configurations → Export 匯出 `.launch` 檔案（XML 格式）。

`.launch` 檔案中的關鍵欄位對應：

| STS `.launch` 欄位 | VS Code `launch.json` 欄位 |
|---|---|
| `org.eclipse.jdt.launching.MAIN_TYPE` | `mainClass` |
| `org.eclipse.jdt.launching.PROJECT_ATTR` | `projectName` |
| `org.eclipse.debug.core.environmentVariables` mapEntry | `env` 物件 |
| `org.eclipse.jdt.launching.PROGRAM_ARGUMENTS` | `args` |
| `spring.boot.profile` | `vmArgs` 中的 `-Dspring.profiles.active=` |

### Step 2: 建立或更新 .vscode/launch.json

`launch.json` 放在 VS Code 開啟的資料夾下的 `.vscode/` 目錄。

### Step 3: launch.json 基本結構

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "type": "java",
            "name": "設定名稱",
            "request": "launch",
            "mainClass": "com.example.MainApplication",
            "projectName": "module-name",
            "console": "integratedTerminal",
            "vmArgs": "-Dspring.profiles.active=local -Dfile.encoding=UTF-8 -Dstdout.encoding=UTF-8 -Dstderr.encoding=UTF-8",
            "env": {
                "ENV_VAR_NAME": "value"
            }
        }
    ]
}
```

**重要欄位說明：**
- `console: "integratedTerminal"` — 讓輸出走 integrated terminal（而非 Debug Console），才能正確顯示中文
- `vmArgs` 中的 encoding 參數 — 讓 Java process 輸出 UTF-8
- `projectName` — 對應 Maven module 名稱（pom.xml 的 artifactId）

### Step 4: Spring Boot app 範例

```json
{
    "type": "java",
    "name": "api (dev)",
    "request": "launch",
    "mainClass": "com.example.ApiApplication",
    "projectName": "api",
    "console": "integratedTerminal",
    "vmArgs": "-Dspring.profiles.active=dev -Dfile.encoding=UTF-8 -Dstdout.encoding=UTF-8 -Dstderr.encoding=UTF-8",
    "env": {
        "spring_datasource_password": "xxx",
        "spring_datasource_username": "xxx"
    }
}
```

### Step 5: Argo Job 範例（含 program arguments）

```json
{
    "type": "java",
    "name": "argojob - SomeJob (local)",
    "request": "launch",
    "mainClass": "com.example.ArgoJobApplication",
    "projectName": "argojob",
    "console": "integratedTerminal",
    "vmArgs": "-Dspring.profiles.active=local -Dfile.encoding=UTF-8 -Dstdout.encoding=UTF-8 -Dstderr.encoding=UTF-8",
    "args": "<executionId> <scheduleName> <env> <base64EncodedJobData> 1 1",
    "env": {
        "spring_mail_password": "xxx",
        "spring_mail_username": "xxx"
    }
}
```

---

## 中文 log 亂碼修復

### 問題根因

Windows PowerShell 預設 `[Console]::OutputEncoding` 是 **Big5 (CP950)**。即使 Java 已設定輸出 UTF-8，PowerShell 仍用 CP950 解讀，造成亂碼。

**錯誤嘗試（無效）：**
- `terminal.integrated.env.windows` 設 `JAVA_TOOL_OPTIONS` → Java debugger 不走此路
- VS Code terminal profile 加 `chcp 65001` → PowerShell 自己的 encoding 蓋掉 chcp

**正確修法：**

### Fix 1: launch.json 加 encoding vmArgs（讓 Java 輸出 UTF-8）

```json
"vmArgs": "-Dfile.encoding=UTF-8 -Dstdout.encoding=UTF-8 -Dstderr.encoding=UTF-8"
```

> `-Dstdout.encoding` 和 `-Dstderr.encoding` 為 Java 17+ 才支援的參數。

### Fix 2: launch.json 加 console 設定（讓輸出走 terminal）

```json
"console": "integratedTerminal"
```

### Fix 3: PowerShell profile 設定 UTF-8（讓 terminal 正確顯示）

確認 profile 路徑：
```bash
powershell.exe -NoProfile -Command "echo \$PROFILE"
# 通常是 C:\Users\{user}\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1
```

在 profile 檔案最前面加入：
```powershell
# UTF-8 encoding for correct Chinese display
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null
```

三個 Fix 都需要，缺一不可：
- Fix 1: Java 輸出 UTF-8
- Fix 2: 輸出送到 terminal（而非 Debug Console）
- Fix 3: terminal 能正確顯示 UTF-8

### 確認修復後 PowerShell encoding 狀態

```bash
powershell.exe -NoProfile -Command "[Console]::OutputEncoding"
# CodePage 應為 65001（UTF-8），不是 950（Big5）
```

---

## 如何執行設定

設定完 `launch.json` 後，有兩種方式執行：

1. **Command Center**（推薦）：點 VS Code 頂部輸入框 → 輸入 `debug` → 選 `Debug: Start Debugging` → 選擇 configuration
2. **Spring Boot Dashboard**：左側 Activity Bar 的葉子圖示 → 選 app → ▶ 執行（會自動套用 launch.json 中對應的設定）

---

## 注意事項

- `launch.json` 放在 VS Code **實際開啟的資料夾**下的 `.vscode/`，路徑不對則設定不會被讀取
- Multi-module Maven 專案的 `projectName` 對應各自 module 的名稱，不是 root project
- Run & Debug 側欄的 dropdown 有時需要 Java Language Server 完整載入才會出現，可改用 Command Center 執行
