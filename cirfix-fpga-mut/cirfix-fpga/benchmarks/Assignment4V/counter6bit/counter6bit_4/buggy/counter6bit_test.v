module counter6bit_test(ENA,CLR,F_IN,Q);
    input ENA;
    input CLR;
    input F_IN;
    output [23:0] Q;  
    
    reg [23:0] Q;
    reg [19:0] temp_bcd=0;
    reg F_OUT;
    


		

always @(posedge F_IN)
begin
if(CLR==1) Q<=0;
else
begin
if(ENA==1)
begin
if(Q[3:0]==4'b1001) 
begin
temp_bcd<=temp_bcd+1;
Q<={temp_bcd,4'b0000};
end
else if(Q[7:0]==8'b10000000)  Q<=0;
else Q=Q+1;
end
end
end
endmodule