module counter6bit_test(ENA,CLR,F_IN,Q);
    input ENA;
    input CLR;
    input F_IN;
    output [23:0] Q;  
    
   
    reg [23:0] Q;
    reg F_OUT;

    initial
        Q = 0;


		

    always @(posedge F_IN) begin
        if (CLR)
            Q <= 0;
        
		

        else if (Q[3:0] != 9)
            Q[3:0] <= Q[3:0] + 1;
        else begin
            Q[3:0] <= 0;
            if (Q[7:4] != 9)
                Q[7:4] <= Q[7:4] + 1;
            else begin
                Q[7:4] <= 0;
                if (Q[11:8] != 9)
                    Q[11:8] <= Q[11:8] + 1;
                else begin
                    Q[11:8] <= 0;
                    if (Q[15:12] != 9)
                        Q[15:12] <= Q[15:12] + 1;
                    else begin
                        Q[15:12] <= 0;
                        if (Q[19:16] != 9)
                            Q[19:16] <= Q[19:16] + 1;
                        else begin
                            Q[19:16] <= 0;
                            if (Q[23:20] != 9)
                                Q[23:20] <= Q[23:20] + 1;
                            else
                                Q[23:20] <= 0;
                    end
                end
            end
        end
    end
  end
  endmodule