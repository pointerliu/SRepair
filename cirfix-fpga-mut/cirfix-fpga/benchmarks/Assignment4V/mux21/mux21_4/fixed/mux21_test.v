module mux21(a,b,s,y);
	input a,b,s;
	output y;
	reg y;
	always @(a,b,s)
    
        

if(s==1'B0)begin y=a;end
else begin y=b;end
        

	
endmodule