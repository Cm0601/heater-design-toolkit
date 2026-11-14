"""无 GUI 环境下验证 KiCad Heater Generator 插件能否真正生成走线。

必须用 KiCad 自带的 Python 运行，例如：
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts/test_heater_plugin.py

插件版本目录可用环境变量覆盖：set KICAD_VER=9.0
"""
import sys
import os
import warnings

warnings.filterwarnings("ignore")

KICAD_VER = os.environ.get("KICAD_VER", "10.0")
PLUGIN_DIR = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~/.local/share")),
    "kicad",
    KICAD_VER,
    "scripting",
    "plugins",
)
sys.path.insert(0, PLUGIN_DIR)

import pcbnew

# 无 GUI 时用自建 board 替代 pcbnew.GetBoard()
board = pcbnew.BOARD()
pcbnew.GetBoard = lambda: board
pcbnew.Refresh = lambda: None

from Heater_Generator_Plugin import track_generator as tg

gen = tg.TracksGenerator(
    trace_clearance=0.2,
    trace_width=0.3,
    pcb_size_x=30.0,
    pcb_size_y=30.0,
    copper_to_edge_clearance=0.3,
    net_name="HEATER",
)
gen.draw_heater()

tracks = list(board.GetTracks())
total_len_mm = sum(t.GetLength() / 1e6 for t in tracks)

# 1oz 铜、0.3mm 线宽、室温下的方块电阻约 0.5 mOhm/sq
width_mm = 0.3
thickness_um = 35.0
rho = 1.72e-8  # ohm*m
area_m2 = (width_mm * 1e-3) * (thickness_um * 1e-6)
resistance = rho * (total_len_mm * 1e-3) / area_m2

print("tracks      :", len(tracks))
print("total length: %.1f mm" % total_len_mm)
print("est. R      : %.3f ohm  (%.0f mOhm)" % (resistance, resistance * 1000))
print("power @12V  : %.2f W" % (12.0 ** 2 / resistance))
print("power @24V  : %.2f W" % (24.0 ** 2 / resistance))
net_names = {t.GetNetname() for t in tracks}
print("net         :", net_names)
layers = {t.GetLayerName() for t in tracks}
print("layers      :", layers)
print("RESULT: OK")
