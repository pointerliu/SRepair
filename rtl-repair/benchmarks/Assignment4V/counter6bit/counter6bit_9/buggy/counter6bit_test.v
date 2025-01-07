module counter6bit_test(ENA,CLR,F_IN,Q);
    input ENA;
    input CLR;
    input F_IN;
    output [23:0] Q;  
    
   
    reg [23:0] Q;
    reg F_OUT;
    


		

    always@(posedge F_IN,posedge CLR) begin
        if(CLR==1)
            Q=24'b0;
        else begin
            Q=Q+ENA;
            Q[7:4]=Q[7:4]+(Q[3:0]==4'ha);
            Q[11:8]=Q[11:8]+(Q[7:4]==4'ha);
            Q[15:12]=Q[15:12]+(Q[11:8]==4'ha);
            Q[19:16]=Q[19:16]+(Q[15:12]==4'ha);
            Q[23:20]=Q[23:20]+(Q[19:16]==4'ha);
            Q[3:0]=Q[3:0]-(Q[3:0]==4'ha)*4'ha;
            Q[7:4]=Q[7:4]-(Q[7:4]==4'ha)*4'ha;
            Q[11:8]=Q[11:8]-(Q[11:8]==4'ha)*4'ha;
            Q[15:12]=Q[15:12]-(Q[15:12]==4'ha)*4'ha;
            Q[19:16]=Q[19:16]-(Q[19:16]==4'ha)*4'ha;
            Q[23:20]=Q[23:20]-(Q[23:20]==4'ha)*4'ha;
        end
    end

		


  
  endmodule