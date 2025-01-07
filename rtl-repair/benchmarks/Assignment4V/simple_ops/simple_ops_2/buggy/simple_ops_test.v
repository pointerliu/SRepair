module simple_ops_test(
    input wire clk,
    input wire rstn,
    output reg [1:0] x
);

always @(posedge clk) begin
    if (!rstn) begin
        x <= 2'b00;
    end else begin
        x <= x << 2'd1;
    end
end

endmodule