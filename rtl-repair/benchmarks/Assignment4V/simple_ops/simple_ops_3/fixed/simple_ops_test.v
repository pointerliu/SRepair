module simple_ops_test(
    input wire clk,
    input wire rstn,
    input wire [3:0] x,
    input wire [3:0] c,
    output reg [3:0] y
);

always @(posedge clk) begin
    if (!rstn) begin
        y <= 4'd0;
    end else begin
        y <= x - c;
    end
end

endmodule