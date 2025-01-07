module lock_on_reset
(
input wire clk,
input wire resetn,
input wire unlock,
input wire d,
output reg locked
);

always @(posedge clk) begin

    if(unlock) locked <= d;
    else locked <= 0;
end

endmodule