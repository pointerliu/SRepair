module counter6bit_test(ENA,CLR,F_IN,Q);
    input ENA;
    input CLR;
    input F_IN;
    output [23:0] Q;  
    
   
   reg [23:0] num;

    reg F_OUT;
    


		

    always@(posedge F_IN, posedge CLR)
    begin
        if(CLR == 1)
            num <= 0;
        else if(ENA == 1)
        begin
        if(num == 999999)
            num <= 0;
        else
            num <= num + 1;
        end
    end

    assign Q[23:20] = num /100000;
    assign Q[19:16] = (num % 100000) / 10000;
    assign Q[15:12] = (num % 10000) / 1000;
    assign Q[11:8] = (num % 1000) /100;
    assign Q[7:4] = (num % 100) / 10;
    assign Q[3:0] = num % 10;

		


  
  endmodule