module counter6bit_test(ENA,CLR,F_IN,Q);
    input ENA;
    input CLR;
    input F_IN;
    output [23:0] Q;  
    
   
    reg [23:0] Q;
    reg F_OUT;
    


		

        always@(posedge CLR or posedge F_IN  ) begin
       if(F_IN) begin
       if(CLR) Q<=0;
        else if(!ENA) Q<=Q;
         else if(Q[3:0]==4'd9) begin Q[7:4]<=Q[7:4]+1;Q[3:0]=0;end
         else Q<=Q+1;end
        
          
           
      
    
        




		


  end
endmodule