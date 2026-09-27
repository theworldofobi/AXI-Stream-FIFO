module axis_fifo #(
  // params: data width 32, depth 16, use tlast true
) (
  // slave: in s_aclk, in s_aresetn, in s_axis_tdata, in s_axis_tlast, in s_axis_tvalid, out s_axis_tready

  // master: in m_aclk, out m_axis_tdata, out m_axis_tlast, out m_axis_tvalid, in m_axis_tready

  // flags: out s_full, out m_empty
);
  // log2 data width for addr width
  // mem_width is data width unless tlast then datawidth + 1
  // ptr width is addr_width + 1 for extra msb trick

  
endmodule

