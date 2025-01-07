module user_grant_access(data_out, usr_id, data_in, clk, rst_n);

output reg [7:0] data_out;
input wire [2:0] usr_id;
input wire [7:0] data_in;
input wire clk, rst_n;

reg grant_access;

always @ (posedge clk)
begin
    if (!rst_n)
        data_out = 0;
    else begin
        data_out = (usr_id == 3'h4) ? data_in : data_out;
    end
end

endmodule