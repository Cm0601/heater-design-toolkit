"""无界面复现 PCB-Heater-Generator 的计算与 footprint 生成。

依赖上游项目 bliepp/PCB-Heater-Generator（AGPL-3.0）的 application 模块：

    git clone https://github.com/bliepp/PCB-Heater-Generator.git

本脚本不内置其代码，通过环境变量指向克隆位置：

    set HEATER_GEN_REPO=D:\\path\\to\\PCB-Heater-Generator
"""
import os
import sys

REPO = os.environ.get("HEATER_GEN_REPO") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "PCB-Heater-Generator"
)
if not os.path.isdir(os.path.join(REPO, "application")):
    sys.exit(
        "找不到 PCB-Heater-Generator 源码。请 git clone 后设置环境变量 HEATER_GEN_REPO 指向它。\n"
        "当前查找路径: %s" % REPO
    )
sys.path.insert(0, REPO)

from application.materials import ALL_MATERIALS
from application.traces import TraceCalculator
from main import kicad_footprint  # 上游 main.py 中的 footprint 生成函数

# ---- 设计参数（与 Web 界面默认值一致，可用环境变量覆盖）----
voltage = float(os.environ.get("HV_VOLTAGE", 12.0))          # V
max_current = float(os.environ.get("HV_CURRENT", 10.0))      # A
temperature_rise = float(os.environ.get("HV_TEMP_RISE", 225.0))  # °C
material = ALL_MATERIALS[0]   # Copper
thickness = 1 * 0.035     # mm (1 oz/ft²)
spacing = 0.2             # mm
min_clearance = 0.2       # mm
pcb_height = float(os.environ.get("HV_HEIGHT", 100.0))       # mm

trace = TraceCalculator(material, temperature_rise, thickness, max_current)

clearance = min_clearance
if spacing > min_clearance + trace.width:
    clearance = spacing - trace.width

min_resistance = voltage / max_current
minimal_track_length = trace.length_from_resistance(min_resistance)
n, track_length = trace.serpentine_data(
    height=pcb_height - 2 * clearance,
    clearance=clearance,
    min_length=minimal_track_length,
)
pcb_width = (n - 1) * (clearance + trace.width) + 2 * clearance

resistance = trace.resistance_from_length(track_length)
current = voltage / resistance

print("--- 计算结果 ---")
print("Trace width      : %.4f mm" % trace.width)
print("Serpentines (n)  : %d" % n)
print("Track length     : %.1f mm (min %.1f mm)" % (track_length, minimal_track_length))
print("Resistance       : %.3f ohm (min %.3f ohm)" % (resistance, min_resistance))
print("Current @%gV      : %.3f A" % (voltage, current))
print("Power            : %.2f W (max %.1f W)" % (voltage * current, max_current * voltage))
print("PCB width        : %.1f mm" % pcb_width)
print("PCB height       : %.1f mm" % pcb_height)

content = kicad_footprint(n, pcb_height, trace.width, clearance)

out_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples"
)
os.makedirs(out_dir, exist_ok=True)
out = os.path.join(out_dir, "heater_%gv_%dW.kicad_mod" % (voltage, round(voltage * current)))
with open(out, "w", encoding="utf-8") as f:
    f.write(content)

print("--- footprint ---")
print("file  :", out)
print("bytes :", len(content))
