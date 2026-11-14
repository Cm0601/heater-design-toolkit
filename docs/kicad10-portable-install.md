# 免管理员安装 KiCad 10 并部署插件

适用于**没有管理员权限**、或希望把程序全部装在非系统盘（如 D 盘）的场景。已在 Windows 11 + KiCad 10.0.8 实测。

## 为什么不用安装器

KiCad 官方 Windows 安装器是 NSIS 包，静默安装需要提权：

```powershell
Start-Process -FilePath kicad-10.0.8-x86_64.exe -ArgumentList '/S','/D=D:\KiCad\10.0' -Verb RunAs -Wait
```

若 UAC 未通过，会返回异常退出码且**不落地任何文件**。此时改用解包方案。

## 步骤

### 1. 校验安装包

```powershell
$sig = Get-AuthenticodeSignature .\kicad-10.0.8-x86_64.exe
$sig.Status           # 应为 Valid
$sig.SignerCertificate.Subject   # CN=KICAD SERVICES CORPORATION
```

### 2. 解包到目标目录

```powershell
& "C:\Program Files\7-Zip\7z.exe" x .\kicad-10.0.8-x86_64.exe -o"D:\KiCad\10.0" -y
```

解包后约 4.6 GB。

### 3. 验证

```powershell
& "D:\KiCad\10.0\bin\kicad-cli.exe" version   # 10.0.8
& "D:\KiCad\10.0\bin\python.exe" --version    # 3.11.5（KiCad 自带）
```

### 4. 部署插件依赖

```powershell
& "D:\KiCad\10.0\bin\python.exe" -m pip install scipy
```

务必装到 **KiCad 自带的 Python**，装到系统 Python 无效。

### 5. 部署插件

```powershell
$dest = Join-Path $env:APPDATA "kicad\10.0\scripting\plugins"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item .\kicad-plugin\Heater_Generator_Plugin -Destination $dest -Recurse -Force
```

### 6. 启用

打开 `D:\KiCad\10.0\bin\pcbnew.exe` → `工具 → 外部插件 → 刷新插件` → 工具栏出现红色加热器图标。

## 已知限制

- **没有注册表项**：文件关联（.kicad_pcb 双击打开）、开始菜单、`kicad-cli` 的 PATH 都不会自动创建，需手动配
- **卸载 = 删除目录**，但 `%APPDATA%\kicad` 下的用户配置会保留
- 升级 KiCad 时不能覆盖安装，需重新解包到新版本目录

## 排错

| 现象 | 原因 | 处理 |
|---|---|---|
| 插件不可见 | 依赖缺失或语法错误 | 用 KiCad 自带 Python 执行 `import scipy` 检查 |
| 点插件报 `VECTOR2I` TypeError | 插件是 v7 版代码 | 见 README 的兼容性补丁 |
| 生成走线后无反应 | 未在 PCB Editor 中打开板子 | `pcbnew.GetBoard()` 返回空 |
