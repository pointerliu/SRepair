module mux21(a,b,s,y);
	input a,b,s;
	output y;
	reg y;
	always @(a,b,s)
    
        

	if(s<=0)
	 	y=a;
	else
	 	y=b;
        

	
endmodule