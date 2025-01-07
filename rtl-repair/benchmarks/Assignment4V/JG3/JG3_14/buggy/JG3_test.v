module JG3(ABC,X,Y);
	
	input [2:0] ABC;
	
	output X, Y;
	reg X, Y;
	
	always@(ABC)
    
        

    begin
        if(ABC==3'b000)
        begin
        X=0;Y=1;
        end
        else if(ABC==3'b001)
        begin
        X=0;Y=0;
        end
        else if(ABC==3'b010)
        begin
        X=0;Y=0;
        end
        else if(ABC==3'b011)
        begin
        X=0;Y=0;
        end
        else if(ABC==3'b100)
        begin
        X=0;Y=0;
        end
        else if(ABC==3'b101)
        begin
        X=1;Y=0;
        end
        else if(ABC==3'b110)
        begin
        X=1;Y=0;
        end
        else begin X=1;Y=1;end
    end   
	    

	
endmodule