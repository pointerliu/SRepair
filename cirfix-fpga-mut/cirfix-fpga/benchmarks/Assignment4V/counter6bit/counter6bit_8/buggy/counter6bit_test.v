module counter6bit_test(ENA,CLR,F_IN,Q);
    input ENA;
    input CLR;
    input F_IN;
    output [23:0] Q;  
    
   
    reg [23:0] Q;
    reg F_OUT;
    


		

always @(posedge F_IN)
begin
if(CLR==1) Q<=0;
else
begin
if(ENA==1) Q<=Q+1;
end
end
		


  endmodule