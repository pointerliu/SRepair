

module decoder3e_test(a,ena,y);
  input [2:0] a;
  input ena;
  output [7:0] y; 
  reg[7:0] Y;
  


always @(ena or a)
begin
if(ena==0)
Y=8'b0000_0000;
else
case (a)
3'b000: Y=8'b0000_0001;
3'b001: Y=8'b0000_0010;
3'b010: Y=8'b0000_0100;
3'b011: Y=8'b0000_1000;
3'b100: Y=8'b0001_000;
3'b101: Y=8'b0010_0000;
3'b110: Y=8'b0100_0000;
3'b111: Y=8'b100_0000;
endcase
end
assign y=Y;





endmodule
