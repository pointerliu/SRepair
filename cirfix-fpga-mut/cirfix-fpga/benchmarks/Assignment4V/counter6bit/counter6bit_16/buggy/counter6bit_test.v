module counter6bit_test(ENA,CLR,F_IN,Q);
    input ENA;
    input CLR;
    input F_IN;
    output [23:0] Q;  
    
   
    reg [23:0] Q;
    reg F_OUT;
    


		

always@(posedge F_IN)
begin 
    if(CLR) Q=24'b000000000000000000000000;
    else if(ENA==0)
        Q=Q;
    else if(ENA==1)
    begin 
        if(Q==24'b000000000000000000001001)
            Q=Q-24'b000000000000000000001001+24'b000000000000000000010000;
        else if(Q==24'b000000000000000010010000)
            Q=Q-24'b000000000000000010010000+24'b000000000000000100000000;        
		else if(Q==24'b000000000000100100000000)
            Q=Q-24'b000000000000100100000000+24'b000000000001000000000000;
        else if(Q==24'b000000001001000000000000)
            Q=Q-24'b000000001001000000000000+24'b000000010000000000000000;
        else 
            Q=Q+1;
    end
        


  end
  endmodule