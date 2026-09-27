module reset_sync (
  input  logic clk,
  input  logic async_rst_n,
  output logic rst_n_sync     // sync'd to clk
);
  logic metastable;

  always_ff @(posedge clk or negedge async_rst_n) begin
    if (!async_rst_n) begin
      metastable <= 1'b0;
      rst_n_sync <= 1'b0;
    end else begin
      metastable <= 1'b1;
      rst_n_sync <= metastable;
    end
  end
endmodule
 
