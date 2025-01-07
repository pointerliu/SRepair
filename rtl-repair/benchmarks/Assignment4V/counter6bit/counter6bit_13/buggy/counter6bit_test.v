module counter6bit_test(ENA,CLR,F_IN,Q);
    input ENA;
    input CLR;
    input F_IN;
    output [23:0] Q;  
    
   
    reg [23:0] Q;
    reg F_OUT;
    


		

always @(posedge F_IN)
begin
if(Q[3:0]>8) 
begin
Q=Q+24'b000000000000000000010000;
Q[3:0]=4'b0000;
end
else
Q=Q+24'b000000000000000000000001;
if(CLR == 1)
Q=24'b000000000000000000000000;



		


  end
  endmodule