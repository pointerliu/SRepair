module locked_register
(
input [15:0] Data_in,
input clk,
input resetn,
input write,
input lock_status,
input debug_unlocked,
output reg [15:0] Data_out
);

always @(posedge clk) begin

    if (~resetn) begin
        Data_out <= 16'h0000;
    end
    else if (write & (~lock_status | debug_unlocked)  ) begin
        Data_out <= Data_in;
    end
    else if (~write) begin
        Data_out <= Data_out;
    end

end

endmodule
