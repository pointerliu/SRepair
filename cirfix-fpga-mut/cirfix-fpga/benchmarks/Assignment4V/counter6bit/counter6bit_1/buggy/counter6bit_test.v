module counter6bit_test(ENA,CLR,F_IN,Q);
    input ENA;
    input CLR;
    input F_IN;
    output [23:0] Q;  
    
    reg F_OUT;
    reg [20:0] tmp;
		

    always@(posedge F_IN,posedge CLR)
    begin

        if(CLR)
        begin
        tmp<=0;
        end
        else
        begin
        if(ENA==1)
        begin
        if(tmp<=999999)
        begin
            tmp<=tmp+1;
        end
        else
        begin
            tmp<=0;
        end
        end

        end

    end
    
    assign Q[23:20]=(tmp/100000)%10;
    assign Q[19:16]=(tmp/10000)%10;
    assign Q[15:12]=(tmp/1000)%10;
    assign Q[11:8]=(tmp/100)%10;
    assign Q[7:4]=(tmp/10)%10;
    assign Q[3:0]=(tmp)%10;
 

  endmodule