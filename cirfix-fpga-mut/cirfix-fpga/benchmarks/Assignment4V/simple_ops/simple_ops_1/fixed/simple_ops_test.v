module simple_ops_test(
    input wire [3:0] x,
    output wire [3:0] y
);

assign y = ~x;

endmodule