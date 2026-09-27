module gray_sync #(
  parameter int WIDTH = 5
) (
  input  logic             clk,
  input  logic             rst_n,
  input  logic [WIDTH-1:0] gray_in,
  output logic [WIDTH-1:0] gray_out_sync
);
  logic [WIDTH-1:0] stage1;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      stage1        <= '0;
      gray_out_sync <= '0;
    end else begin
      stage1        <= gray_in;
      gray_out_sync <= stage1;
    end
  end
endmodule
 
