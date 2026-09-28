import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer
from cocotbext.axi import AxiStreamSource, AxiStreamSink, AxiStreamBus, AxiStreamFrame

DEPTH = 16

def start_clocks(dut, s_period_ns=10, m_period_ns=7):
  cocotb.start_soon(Clock(dut.s_aclk, s_period_ns, unit="ns").start())
  cocotb.start_soon(Clock(dut.m_aclk, m_period_ns, unit="ns").start())
 
 
async def reset_dut(dut):
  dut.s_axis_tdata.value = 0
  dut.s_axis_tlast.value = 0
  dut.s_axis_tvalid.value = 0
  dut.m_axis_tready.value = 0
  
  dut.s_aresetn.value = 0
  await Timer(100, unit="ns")
  dut.s_aresetn.value = 1
  await Timer(50, unit="ns")
 
 
def make_env(dut):
  source = AxiStreamSource(
    AxiStreamBus.from_prefix(dut, "s_axis"), dut.s_aclk, dut.s_aresetn, reset_active_level=False
  )
  sink = AxiStreamSink(
    AxiStreamBus.from_prefix(dut, "m_axis"), dut.m_aclk, dut.s_aresetn, reset_active_level=False
  )
  return source, sink
 
 
@cocotb.test()
async def test_reset(dut):
  start_clocks(dut)
  await reset_dut(dut)
  assert dut.m_empty.value == 1
  assert dut.s_full.value == 0
  assert dut.s_axis_tready.value == 1
  assert dut.m_axis_tvalid.value == 0

 
@cocotb.test()
async def test_single_write_read(dut):
  start_clocks(dut)
  await reset_dut(dut)
  source, sink = make_env(dut)

  payload = bytes([0xDE, 0xAD, 0xBE, 0xEF])
  await source.send(AxiStreamFrame(payload))

  rx = await sink.recv()
  assert bytes(rx.tdata) == payload
 
 
@cocotb.test()
async def test_full_while_read_stalled(dut):
  start_clocks(dut)
  await reset_dut(dut)
  source, sink = make_env(dut)
  sink.pause = True

  frames = [bytes([i % 256] * 4) for i in range(DEPTH)]
  for f in frames:
    await source.send(AxiStreamFrame(f))

  await ClockCycles(dut.s_aclk, DEPTH + 10)
  assert dut.s_full.value == 1
  assert dut.s_axis_tready.value == 0

  sink.pause = False
  for expected in frames:
    rx = await sink.recv()
    assert bytes(rx.tdata) == expected
 
 
@cocotb.test()
async def test_tlast_passthrough(dut):
  start_clocks(dut)
  await reset_dut(dut)
  source, sink = make_env(dut)

  packet_a = bytes(range(8))
  packet_b = bytes(range(8, 16))
  await source.send(AxiStreamFrame(packet_a))
  await source.send(AxiStreamFrame(packet_b))

  rx_a = await sink.recv()
  rx_b = await sink.recv()
  assert bytes(rx_a.tdata) == packet_a
  assert bytes(rx_b.tdata) == packet_b
 
 
async def _cdc_random_stress(dut, s_period_ns, m_period_ns, n_frames=80):
  start_clocks(dut, s_period_ns, m_period_ns)
  await reset_dut(dut)
  source, sink = make_env(dut)

  async def random_pause(signal_owner):
    while True:
      signal_owner.pause = random.random() < 0.5
      await Timer(random.randint(5, 40), unit="ns")

  source_pauser = cocotb.start_soon(random_pause(source))
  sink_pauser = cocotb.start_soon(random_pause(sink))

  frames = [bytes([random.randint(0, 255) for _ in range(4)]) for _ in range(n_frames)]
  for f in frames:
    await source.send(AxiStreamFrame(f))

  for expected in frames:
    rx = await sink.recv()
    assert bytes(rx.tdata) == expected

  source_pauser.cancel()
  sink_pauser.cancel()
 
 
@cocotb.test()
async def test_cdc_random_write_faster(dut):
  await _cdc_random_stress(dut, s_period_ns=10, m_period_ns=17)
 
 
@cocotb.test()
async def test_cdc_random_read_faster(dut):
  await _cdc_random_stress(dut, s_period_ns=17, m_period_ns=10)
 
 
@cocotb.test()
async def test_cdc_random_close_ratio(dut):
  await _cdc_random_stress(dut, s_period_ns=10, m_period_ns=11, n_frames=120)
 
 
@cocotb.test()
async def test_reset_mid_transfer(dut):
  start_clocks(dut)
  await reset_dut(dut)
  source, _sink = make_env(dut)

  cocotb.start_soon(source.send(AxiStreamFrame(bytes([1, 2, 3, 4]))))
  await Timer(15, unit="ns")

  dut.s_aresetn.value = 0
  await Timer(100, unit="ns")
  dut.s_aresetn.value = 1
  await Timer(50, unit="ns")

  assert dut.m_empty.value == 1
  assert dut.s_full.value == 0
 
