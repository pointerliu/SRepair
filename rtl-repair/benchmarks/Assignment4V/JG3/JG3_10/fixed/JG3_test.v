module JG3(ABC,X,Y);
	
	input [2:0] ABC;
	
	output X, Y;
	reg X, Y;
	
	always@(ABC)
    
        

		case(ABC)
			3'd0: begin X<=0;Y<=1; end
			3'd5: begin X<=1;Y=0; end
			3'd6: begin X<=1;Y=0; end
			3'd7: begin X<=1;Y=0; end
			default: begin X<=0;Y=0; end
		endcase	
		
        

	
endmodule