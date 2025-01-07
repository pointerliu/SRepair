

module decoder3e_test(a,ena,y);
  input [2:0] a;
  input ena;
  output [7:0] y; 

  


reg [7:0]y;
always@(a or ena)begin
  if(~ena) y=8'd0;
  else 
    case(a)
      3'b000: y<=8'd0;
      3'b001: y<=8'd1;
      3'b010: y<=8'd2;
      3'b011: y<=8'd3;
      3'b100: y<=8'd4;
      3'b101: y<=8'd5;
      3'b110: y<=8'd6;
      3'b111: y<=8'd7;
  endcase
end





endmodule
