module lock_on_reset
(
input wire clk,
input wire resetn,
input wire unlock,
input wire d,
output reg locked
);

always @(posedge clk) begin

    if(unlock) locked <= 0;
    else locked <= locked;
end

endmodule