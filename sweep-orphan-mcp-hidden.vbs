Set objShell = CreateObject("WScript.Shell")
objShell.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -File ""C:\Users\eric.liao\.claude\sweep-orphan-mcp.ps1""", 0, False
