

module decoder3e_test(a,ena,y);
  input [2:0] a;
  input ena;
  output reg [7:0] y; 

  


always@(ena or a)
casex (a) 
  4'b0xxx:y=8'b00000000;
  4'b1000:y=8'b00000001;
  4'b1001:y=8'b00000010;
  4'b1010:y=8'b00000100;
  4'b1011:y=8'b00001000;
  4'b1100:y=8'b00010000;
  4'b1101:y=8'b00100000;
  4'b1110:y=8'b01000000;
  4'b1111:y=8'b10000000;
endcase


endmodule
