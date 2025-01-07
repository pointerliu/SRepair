module Calculator(
input bclk,
input ena,
input clr,
input clk,
output wire[3:0] caout,
output  reg mf);
reg [3:0] moutq;
assign caout = moutq;
always@(posedge bclk) begin
if(clr)
    moutq <= 4'b0000;
end
always@(posedge clk) begin
  if(!ena)
    moutq = moutq;
  else if(moutq >= 4'b1001)begin
    moutq = 0;
    mf=1;
  end
  else begin
    moutq = moutq + 1;
    mf=0;
    end
end
endmodule
module counter6bit_test(ENA,CLR,F_IN,Q);
    input ENA;
    input CLR;
    input F_IN;
    output wire[23:0] Q;
    wire F_OUT;
    wire [4:0]cout=0;
Calculator U0(F_IN,ENA,CLR,F_IN,Q[3:0],cout[0]);
Calculator U1(F_IN,ENA,CLR,cout[0],Q[7:4],cout[1]);
Calculator U2(F_IN,ENA,CLR,cout[1],Q[11:8],cout[2]);
Calculator U3(F_IN,ENA,CLR,cout[2],Q[15:12],cout[3]);
Calculator U4(F_IN,ENA,CLR,cout[3],Q[19:16],cout[4]);
Calculator U5(F_IN,ENA,CLR,cout[4],Q[23:20],F_OUT);
endmodule