module counter6bit_test(ENA,CLR,F_IN,Q);
    input ENA;
    input CLR;
    input F_IN;
    output [23:0] Q;  
    
   
    reg [23:0] Q;
    reg F_OUT;
    


		

always@(posedge F_IN )
begin
    if(CLR) Q<=24'b0000_0000_0000_0000_0000_0000;
    else if(!ENA) Q[3:0]<=Q[3:0];
        else  if (Q[3:0] < 4'b1001)       
                Q[3:0] <= Q[3:0] +4'b0001;
            else begin
                Q[3:0] <= 4'b0000;
                if  (Q[7:4] < 4'b1001)
                    Q[7:4] <= Q[7:4] + 4'b0001;
                else
                begin
                  Q[7:4] <= 4'b0000;
                  if  (Q[11:8] < 4'b1001)
                    Q[11:8] <= Q[11:8] + 4'b0001;
                  else
                  begin
                    Q[11:8] <= 4'b0000;
                    if  (Q[15:12] < 4'b1001)
                    Q[15:12] <= Q[15:12] + 4'b0001;
                  else
                  begin
                  Q[15:12] <= 4'b0000;
                  if  (Q[19:16] < 4'b1001)
                    Q[19:16] <= Q[19:16] + 4'b0001;
                  else
                  begin
                  Q[19:16] <= 4'b0000;
                  if (Q[23:20] < 4'b1001)
                    Q[23:20] <= Q[23:20] + 4'b0001;
                  else
                      Q[23:20] <= 4'b0000;
                  end
              end
          end
          end
          end
          end



		


  
  endmodule