module counter6bit_test(ENA,CLR,F_IN,Q);
    input ENA;
    input CLR;
    input F_IN;
    output [23:0] Q;  
    
   
    reg [23:0] Q;
    reg F_OUT;
    


		

always@(posedge F_IN)
if(ENA)begin
if(CLR)begin
if(Q!=24'bxxxxxxxxxxxxxxxxxxxxxxxx) Q<=0;
if(F_IN) Q<=0;
end
else begin
      if(Q[3:0] != 4'd9)
                Q[3:0] <= Q[3:0]+1;
        else begin
          Q[7:4] <= Q[7:4]+1;
        Q[3:0] <= 0;
                if(Q[7:4] == 4'd9)begin
                    Q[7:4] <= 0;
                    Q[11:8] <= Q[11:8]+1;
                    if(Q[11:8] == 4'd9)begin
                        Q[11:8] <= 0;
                        Q[15:12] <= Q[15:12]+1;
                        if(Q[15:12] == 4'd9)begin
                            Q[15:12] <= 0;
                            Q[19:16] <= Q[19:16]+1;
                            if(Q[19:16] == 4'd9)begin 
                                Q[19:16]<=0;
                                Q[23:20]<= Q[23:20]+1;
                                if(Q[23:20] == 4'd9)begin 
                                    Q<=0;
       
                             end                        
                        end
                    end
                end
            end
        end
   end
end
		

  endmodule