import os
from pathlib import Path
from cocotb_tools.runner import get_runner
 
SIM_DIR = Path(__file__).resolve().parent
ROOT_DIR = SIM_DIR.parent
RTL_DIR = ROOT_DIR / "rtl"
TB_DIR = ROOT_DIR / "tb"
 
SIM = os.getenv("SIM", "icarus")
 
 
def build_and_test(hdl_toplevel, sources, test_module, parameters=None):
  runner = get_runner(SIM)
  build_dir = SIM_DIR / "sim_build" / hdl_toplevel

  runner.build(
    sources=sources,
    hdl_toplevel=hdl_toplevel,
    parameters=parameters or {},
    build_dir=build_dir,
    always=True,
    timescale=("1ns", "1ps"),
  )

  runner.test(
    hdl_toplevel=hdl_toplevel,
    test_module=test_module,
    test_dir=TB_DIR,
    build_dir=build_dir,
    results_xml=f"results_{hdl_toplevel}.xml",
  )
 

def test_axis_fifo_runner():
  build_and_test(
    hdl_toplevel="axis_fifo",
    sources=[
      str(RTL_DIR / "reset_sync.sv"),
      str(RTL_DIR / "gray_sync.sv"),
      str(RTL_DIR / "axis_fifo.sv"),
    ],
    test_module="test_axis_fifo",
    parameters={"DATA_WIDTH": 32, "DEPTH": 16, "USE_TLAST": 1},
  )
 
 
if __name__ == "__main__":
  test_axis_fifo_runner()

