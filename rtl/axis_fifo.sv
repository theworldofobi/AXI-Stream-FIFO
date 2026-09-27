module axis_fifo #(
  parameter int DATA_WIDTH = 32,
  parameter int DEPTH      = 16,
  parameter bit USE_TLAST  = 1
) (
  input  logic                  s_aclk,
  input  logic                  s_aresetn,
  input  logic [DATA_WIDTH-1:0] s_axis_tdata, 
  input  logic                  s_axis_tlast, 
  input  logic                  s_axis_tvalid,
  output logic                  s_axis_tready,

  input  logic                  m_aclk,
  output logic [DATA_WIDTH-1:0] m_axis_tdata,
  output logic                  m_axis_tlast,
  output logic                  m_axis_tvalid,
  input  logic                  m_axis_tready,
  
  output logic s_full,
  output logic m_empty
);
  localparam ADDR_WIDTH = $clog2(DEPTH);
  localparam MEM_WIDTH  = USE_TLAST ? DATA_WIDTH + 1 : DATA_WIDTH;

  // local sync of resets
  logic s_rst_n, m_rst_n;
  reset_sync u_reset_sync_wr (
    .clk        (s_aclk),
    .async_rst_n(s_aresetn),
    .rst_n_sync (s_rst_n)
  );

  reset_sync u_reset_sync_rd (
    .clk        (m_aclk),
    .async_rst_n(s_aresetn),
    .rst_n_sync (m_rst_n)
  );

  logic [MEM_WIDTH-1:0] mem [DEPTH];

  // gray and binary pointers
  logic [ADDR_WIDTH:0] wr_bin, wr_bin_next, wr_gray, wr_gray_next;
  logic [ADDR_WIDTH:0] rd_bin, rd_bin_next, rd_gray, rd_gray_next;
  logic [ADDR_WIDTH:0] rd_2_wr_gray, wr_2_rd_gray;

  // handshake
  logic rd_en, wr_en;
  assign rd_en = s_axis_tvalid && s_axis_tready;
  assign wr_en = m_axis_tvalid && m_axis_tready;

  // master writing
  assign wr_bin_next = wr_en ? wr_bin + 1'b1 : wr_bin;
  assign wr_gray_next = (wr_bin_next >> 1) ^ wr_bin_next;

  assign s_full = (wr_gray_next == {~rd_2_wr_gray[ADDR_WIDTH:ADDR_WIDTH-1], rd_2_wr_gray[ADDR_WIDTH-2:0]});
  assign s_axis_tready = !s_full;
  
  always_ff @(posedge s_aclk or negedge s_aresetn) begin
    if (!s_rst_n) begin
      wr_bin  <= '0;
      wr_gray <= '0;
    end else begin
      if (wr_en) begin
        wr_bin  <= wr_bin_next;
        wr_gray <= wr_gray_next;
        mem[wr_bin[ADDR_WIDTH-1:0]] <= USE_TLAST ? {s_axis_tdata + s_axis_tlast} : s_axis_tdata;
      end
    end
  end

  gray_sync #(
    .WIDTH(ADDR_WIDTH + 1)
   ) gray_sync (
    .clk          (s_aclk),
    .rst_n        (s_aresetn),
    .gray_in      (rd_gray),
    .gray_out_sync(rd_2_wr_gray)
  );

  // slave reading
  assign rd_bin_next  = rd_en ? rd_bin + 1'b1 : rd_bin;
  assign rd_gray_next = (rd_bin_next >> 1) ^ rd_bin_next;
  assign m_empty       = (rd_gray == wr_2_rd_gray);
  assign m_axis_tvalid = !m_empty;
 
  always_ff @(posedge m_aclk or negedge m_rst_n) begin
    if (!m_rst_n) begin
      rd_bin  <= '0;
      rd_gray <= '0;
    end else begin
      rd_bin  <= rd_bin_next;
      rd_gray <= rd_gray_next;
    end
  end

  logic [MEM_WIDTH-1:0] rd_data;
  assign rd_data      = mem[rd_bin[ADDR_WIDTH-1:0]];
  assign m_axis_tdata = rd_data[DATA_WIDTH-1:0];
  assign m_axis_tlast = USE_TLAST ? rd_data[MEM_WIDTH-1] : 1'b0;

  gray_sync #(.WIDTH(ADDR_WIDTH + 1)) u_wr_ptr_to_rd_domain (
    .clk           (m_aclk),
    .rst_n         (m_rst_n),
    .gray_in       (wr_gray),
    .gray_out_sync (wr_2_rd_gray)
  );

endmodule

