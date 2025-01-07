module counter6bit_test(ENA,CLR,F_IN,Q);
    input ENA;
    input CLR;
    input F_IN;
    output [23:0] Q;  
    
   
    reg [23:0] Q;
    reg F_OUT;
    


		

always@(posedge F_IN or negedge CLR)
begin
if (CLR)
  Q <= 8'b00000000;
else if (ENA == 1'b0)
  Q <= Q;
  else if (Q[3:0]== 4'b1001)
  begin
    Q[3:0] <= 4'b0000;
    Q[7:4] <= Q[7:4] + 1'b1;
  end
  else 
    begin
     Q[7:4] <= Q[7:4];
     Q[3:0] <= Q[3:0] + 1'b1;
    end
		

  end
  endmodule