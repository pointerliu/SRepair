// IP definition
module tz_peripheral(clk, rst_n, data_in, data_in_security_level, data_out);
input clk, rst_n;
input data_in_security_level;
input [31:0] data_in;
output reg [31:0] data_out;

always @ (posedge clk)
begin
    if (!rst_n)
        data_out <= 0;
    else if (data_in_security_level)
        data_out <= data_in;
    else 
        data_out <= data_out;
end

endmodule


// Instantiation of IP in a parent system
module soc(clk, rst_n, rdata, rdata_security_level, data_out);

input clk, rst_n;
input [31:0] rdata;
input rdata_security_level;

output [31:0]  data_out;


    tz_peripheral u_tz_peripheral(
    .clk(clk),
    .rst_n(rst_n),
    .data_in(rdata),
    //Copy-and-paste error or typo grounds data_in_security_level (in this example 0=secure, 1=non-secure) effectively promoting all data to "secure")
    .data_out(data_out)
    );

endmodule