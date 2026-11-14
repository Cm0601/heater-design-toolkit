# Heater Design Toolkit

面向 **PCB / 陶瓷加热器** 的开源设计工具合集与实机验证记录。把两块互补的能力拼在一起：

1. **PCB Heater Generator**（Web）—— 先算功率、线宽、蛇形走线长度，导出 KiCad footprint
2. **Heater Generator Plugin**（KiCad 插件）—— 在 PCB Editor 里按空间填充曲线（Gilbert 曲线）直接画出加热走线与板框

本仓库同时包含：KiCad 10 的兼容性补丁、无界面验证脚本、以及一份可复现的实测样例。

---

## 目录结构

```
kicad-plugin/Heater_Generator_Plugin/   KiCad 插件（已打 KiCad 10 补丁，MIT）
scripts/gen_heater_footprint.py         无界面生成蛇形加热 footprint
scripts/test_heater_plugin.py           无 GUI 环境下验证插件算法与 pcbnew API
docs/kicad10-portable-install.md        免管理员安装 KiCad 10 + 部署插件
```

> `examples/` 下的 `.kicad_mod` / `.svg` 是**生成产物**，不入库，跑一次脚本即得（见下文）。

---

## 一、KiCad 插件（Heater PCB Generator）

### 功能

- 支持曲线：Generalized Hilbert（"gilbert"）曲线，算法来自 [jakubcerveny/gilbert](https://github.com/jakubcerveny/gilbert)
- 输出：加热走线 + Edge Cuts 板框
- 可调参数：线宽、铜到铜间距、铜到板边间距、网络名

### 安装

```bash
# 1) 依赖装进 KiCad 自带的 Python，而不是系统 Python
#    Windows 默认路径示例
"C:\Program Files\KiCad\10.0\bin\python.exe" -m pip install scipy

# 2) 插件复制到 KiCad 用户插件目录
#    Windows: %APPDATA%\kicad\10.0\scripting\plugins\
#    Linux:   ~/.local/share/kicad/10.0/scripting/plugins/
#    macOS:   ~/Library/Preferences/kicad/10.0/scripting/plugins/
```

3) 打开 PCB Editor → `工具 / Tools` → `外部插件 / External Plugins` → `刷新插件 / Refresh Plugins`
4) 工具栏右侧出现**红色加热器图标**，点击即可

> 本仓库未包含 `icon.png`（二进制文件，不影响插件功能，缺图标时 KiCad 显示默认图标）。
> 需要原图标可从上游取回：
> `curl -o kicad-plugin/Heater_Generator_Plugin/icon.png https://raw.githubusercontent.com/steltze/KiCad-Heater-Generator-Plugin/main/icon.png`

### KiCad 10 兼容性补丁（本仓库已包含）

上游代码面向 KiCad v7，在 v10 下会直接抛 `TypeError`。原因与修复：

```python
# v7 写法（v10 报错）
track.SetStart(pcbnew.VECTOR2I(pcbnew.wxPointMM(x, y)))

# v10：wxPointMM() 返回 pcbnew.wxPoint，而 VECTOR2I(wxPoint) 重载已被移除
track.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
```

共 4 处（`track_generator.py` 中的 `PCB_TRACK.SetStart/SetEnd` 与 `PCB_SHAPE.SetStart/SetEnd`）。

---

## 二、无界面生成蛇形加热器 footprint

不依赖 KiCad GUI，直接调用算法层：

```bash
git clone https://github.com/bliepp/PCB-Heater-Generator.git ../PCB-Heater-Generator

python -m venv .venv
.venv/Scripts/python.exe -m pip install streamlit prefixed sexpdata

export HEATER_GEN_REPO=../PCB-Heater-Generator      # 指向上游源码
.venv/Scripts/python.exe scripts/gen_heater_footprint.py
```

可选环境变量覆盖参数：`HV_VOLTAGE`（默认 12）、`HV_CURRENT`（10）、`HV_TEMP_RISE`（225）、`HV_HEIGHT`（100）。
输出写入 `examples/heater_<电压>v_<功率>W.kicad_mod`，可直接拖进 KiCad PCB Editor。

### 实测记录（默认参数）

参数：12 V / 10 A / 温升 225 °C / 1 oz 铜（0.035 mm）/ 间距 0.2 mm / 板高 100 mm

| 指标 | 数值 |
|---|---|
| 线宽 | 1.0286 mm |
| 蛇形条数 | 26 |
| 走线总长 | 2620.3 mm（下限 2511.8 mm） |
| 电阻 | 1.252 Ω（下限 1.20 Ω） |
| 12 V 下功率 / 电流 | 115.03 W / 9.59 A |
| PCB 尺寸 | 31.1 × 100 mm |
| footprint 结构 | 54 条 `fp_line`、2 个 SMD 焊盘、`net_tie_pad_groups "1,2"` |

生成的 `.kicad_mod` 已用 `kicad-cli fp export svg` 在 KiCad 10 下成功解析并渲染，可确认文件格式合法：

```bash
"D:\KiCad\10.0\bin\kicad-cli.exe" fp export svg --layers F.Cu,F.SilkS -o examples examples/heater.pretty
```

---

## 三、插件算法无 GUI 验证

`scripts/test_heater_plugin.py` 用 monkeypatch 替换 `pcbnew.GetBoard()` / `pcbnew.Refresh()`，在没有 GUI 的情况下完整跑一遍 `draw_heater()`：

```
tracks      : 3248
total length: 1687.8 mm
est. R      : 2.765 ohm
power @12V  : 52.08 W   @24V: 208.34 W
layer       : F.Cu   net: HEATER
```

用于快速判断插件在某个 KiCad 版本上是否还能正常工作。

---

## 相关项目

- [steltze/KiCad-Heater-Generator-Plugin](https://github.com/steltze/KiCad-Heater-Generator-Plugin) — 插件上游（MIT）
- [bliepp/PCB-Heater-Generator](https://github.com/bliepp/PCB-Heater-Generator) — 蛇形走线 Web 计算器（AGPL-3.0，本仓库未内置其代码）

## License

本仓库自有的脚本与文档以 **MIT** 发布；`kicad-plugin/` 目录沿用上游 MIT 许可，版权归 Stelios Tzelepis。
