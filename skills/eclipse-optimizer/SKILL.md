---
name: eclipse-optimizer
description: 診斷並修復 Eclipse / Spring Tools Suite 啟動過慢的問題。當 Eclipse 啟動很慢、反應遲鈍、或需要定期清理優化時使用。自動清理 JDT stale index、檢查 JVM 記憶體設定、分析系統資源狀況。
allowed-tools:
  - Bash
  - Read
  - Edit
---

# Eclipse Optimizer Skill

診斷並修復 Eclipse / Spring Tools Suite (STS) 啟動過慢或效能低落的問題。

## 核心功能

1. **JDT Index 清理** - 清除累積的 stale Java 搜尋索引（最常見原因）
2. **JVM 記憶體檢查** - 確認 eclipse.ini 有設定 `-Xms` / `-Xmx`
3. **系統資源診斷** - 查看 RAM 使用、找出記憶體壓力來源
4. **Workspace 健診** - 找出異常大的 metadata

## 使用時機

當使用者說：
- "Eclipse 啟動很慢"
- "STS 開很久"
- "Eclipse 越來越慢"
- "幫我優化 Eclipse"
- "清理 Eclipse"
- "定期維護 Eclipse"

---

## 執行流程

### Step 1: 找到 Eclipse 安裝位置

```bash
# 在常見位置尋找 eclipse.ini 或 SpringToolsForEclipse.ini
find /c/Users -maxdepth 6 -name "eclipse.ini" -o -name "SpringToolsForEclipse.ini" 2>/dev/null | grep -v ".metadata"
```

常見位置：
- `C:\Users\{user}\Downloads\spring-tools-for-eclipse-*\sts-*\SpringToolsForEclipse.ini`
- `C:\eclipse\eclipse.ini`
- `C:\Program Files\Eclipse\eclipse.ini`

### Step 2: 找到所有 Workspace

```bash
find /c/Users -maxdepth 6 -name ".metadata" -type d 2>/dev/null | grep -v "\.plugins" | head -20
```

通常位於：
- `C:\Users\{user}\Downloads\Workspace\`
- `C:\Workspace\`
- `C:\Users\{user}\eclipse-workspace\`

### Step 3: 診斷 JDT Index 數量（關鍵指標）

```bash
# 統計每個 workspace 的 stale index 數量
for ws in "/c/Users/eric.liao/Downloads/Workspace/"*/; do
  count=$(ls "${ws}.metadata/.plugins/org.eclipse.jdt.core/" 2>/dev/null | grep "\.index$" | wc -l)
  echo "$count  ${ws}"
done
```

**判斷標準：**
| index 數量 | 狀態 |
|-----------|------|
| 0 - 30    | 正常 |
| 31 - 80   | 偏多，建議清理 |
| 80+       | 嚴重積累，必須清理 |

### Step 4: 檢查 eclipse.ini JVM 設定

```bash
cat "/path/to/SpringToolsForEclipse.ini"
```

**必要設定（缺少則補上）：**
```
-vmargs
-Xms1g       ← 初始 heap，避免啟動時頻繁 GC 擴張
-Xmx4g       ← 最大 heap，根據系統 RAM 調整
```

**建議值（依 RAM 調整）：**
| 系統 RAM | -Xms | -Xmx |
|---------|------|------|
| 8GB     | 512m | 2g   |
| 16GB    | 1g   | 3g   |
| 32GB+   | 1g   | 4g   |

加入位置（必須在 `-vmargs` 後的第一行）：
```
-vmargs
-Xms1g
-Xmx4g
-XX:CompileCommand=quiet
...
```

### Step 5: 檢查系統資源

```bash
# 查看 RAM 使用狀況
powershell.exe -NoProfile -Command "Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory"

# 查看哪些程式吃最多記憶體
tasklist /FO CSV /NH 2>/dev/null | sort -t',' -k5 -rn | head -15
```

**常見記憶體殺手：**
- `vmmemWSL` → WSL2 佔用大量 RAM（可設定上限）
- `MsMpEng` → Windows Defender 掃描（需設排除路徑）
- `chrome` → 多個分頁
- `Docker` → 容器佔用

### Step 6: 檢查 Workspace metadata 大小

```bash
# 各 plugin 佔用空間
du -sh "/c/Users/eric.liao/Downloads/Workspace/新保險/.metadata/.plugins/"* 2>/dev/null | sort -rh | head -10
```

**警戒值：**
- `org.eclipse.jdt.core` > 100MB → 需要清理 index
- 整個 `.metadata` > 500MB → 異常，需要調查

---

## 清理動作

### 清理 JDT Index（最重要）

**前置：確認 Eclipse 已關閉**

```bash
# 確認沒有 Eclipse/STS 程序在執行
tasklist 2>/dev/null | grep -i "java\|eclipse\|spring"
```

```bash
# 清理所有 workspace 的 stale index
find "/c/Users/eric.liao/Downloads/Workspace" -path "*/.metadata/.plugins/org.eclipse.jdt.core/*.index" -delete && echo "清理完成"
```

```bash
# 驗證清理結果
for ws in "/c/Users/eric.liao/Downloads/Workspace/"*/; do
  count=$(ls "${ws}.metadata/.plugins/org.eclipse.jdt.core/" 2>/dev/null | grep "\.index$" | wc -l)
  echo "$count  ${ws}"
done
```

> **注意：** 清理後第一次啟動 Eclipse 會重建索引，速度稍慢屬正常現象。之後每次啟動就會恢復正常速度。

### 修復 JVM 記憶體設定

```bash
# 讀取並編輯 eclipse.ini
```

在 `-vmargs` 後加入（如果缺少）：
```
-Xms1g
-Xmx4g
```

### WSL2 記憶體限制（選用）

如果 `vmmemWSL` 佔用過多 RAM，可建立 `C:\Users\{user}\.wslconfig`：

```ini
[wsl2]
memory=4GB
swap=2GB
```

之後執行 `wsl --shutdown` 重啟 WSL2 套用設定。

---

## 診斷輸出格式

執行診斷後，輸出以下格式的報告：

```
## Eclipse 效能診斷報告

### JDT Index 狀況
| Workspace | Index 數量 | 狀態 |
|-----------|-----------|------|
| 新保險     | 244       | 嚴重 |
| 叫車       | 218       | 嚴重 |

### JVM 設定
- -Xms: 未設定 ❌ → 建議 1g
- -Xmx: 未設定 ❌ → 建議 4g

### 系統資源
- 總 RAM: 32GB
- 可用 RAM: 6GB（偏低）
- 記憶體壓力來源: vmmemWSL (8GB)

### 建議動作
1. [必要] 清理 JDT stale index（934 個）
2. [必要] 新增 JVM 記憶體設定
3. [建議] 限制 WSL2 記憶體用量
```

---

## 定期維護建議

建議每 1-2 個月執行一次 JDT index 清理，特別是：
- Maven 依賴大量更新後
- 專案有大量程式碼變動後
- 感覺 Eclipse 又開始變慢時

清理指令（Eclipse 關閉後執行）：
```bash
find "/c/Users/eric.liao/Downloads/Workspace" -path "*/.metadata/.plugins/org.eclipse.jdt.core/*.index" -delete && echo "清理完成"
```
