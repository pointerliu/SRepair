
//`timescale 1 ns / 1 ps
module RS_dec_tb;

parameter pclk = 5;     /// period of clk/2 

parameter number = 100;  ///  number of input codewords

parameter OracleCycles = 166160; // the number of cycles that are executed according to the oracle.txt

reg clk,reset;
reg instrumented_clk;
reg CE;
reg [7:0] input_byte;

wire [7:0] Out_byte;
wire CEO;
wire Valid_out;

integer f;

RS_dec  DUT 
(
  .clk(clk), // input clock 
  .reset(reset), // active high asynchronous reset
  .CE(CE), // chip enable active high flag for one clock with every input byte
  .input_byte(input_byte), // input byte
  
  .Out_byte(Out_byte),   // output byte
  .CEO(CEO),  // chip enable for the next block will be active high for one clock , every 8 clks
  .Valid_out(Valid_out) /// valid out for every output block (188 byte)
);

reg [7:0] in_mem [0:(number*204)-1];
reg [7:0] out_mem [0:(number*188)-1];

reg enable;
reg [7:0]true_out;
integer h,k,err;

always #(pclk*4) instrumented_clk=~instrumented_clk; // this is 2*clk

initial
begin
	clk=0;
	instrumented_clk=0;
	forever 
		#pclk clk=~clk;
end 

`ifdef DUMP_TRACE // used for our OSDD calculations
initial begin
   $dumpfile("dump.vcd");
   $dumpvars(0, DUT);
end
`endif // DUMP_TRACE

integer cycle_count = 0;

initial begin
	f = $fopen("output_RS_dec_tb_t1.txt");
	$fwrite(f, "time,Out_byte[7],Out_byte[6],Out_byte[5],Out_byte[4],Out_byte[3],Out_byte[2],Out_byte[1],Out_byte[0],CEO,Valid_out\n");
	forever begin
		@(posedge clk);
		$fwrite(f, "%g,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b\n",
		$time,Out_byte[7],Out_byte[6],Out_byte[5],Out_byte[4],Out_byte[3],Out_byte[2],Out_byte[1],Out_byte[0],CEO,Valid_out);
`ifdef LIMIT_CYCLES
		// exit if we are exceeding the oracle length
		// this can easily happen when we have a malfunctioning circuit
		cycle_cout = cycle_count + 1;
		if(cycle_count > (OracleCycles + 1000)) $finish();
`endif
	end
end

integer ce_t,in_t;
integer lim; // minimum  6

initial 
begin
	err=0;
	lim=6;
	$readmemb("input_RS_blocks", in_mem);
	$readmemb("output_RS_blocks", out_mem);
end


initial
begin
	CE=0;
	@(posedge enable);
	forever
	begin
		@(posedge clk);
		#2 CE=1;
		@(posedge clk);
		#2 CE=0;
		for(ce_t=0; ce_t<lim; ce_t=ce_t+1)
			@(posedge clk); 
	end 
end

initial 

begin
	h=0;
	k=0;
	enable = 0;
	reset =1;
	@(posedge clk); @(posedge clk); @(posedge clk);
	@(posedge clk); @(posedge clk); @(posedge clk);
	reset=0;
	@(posedge clk); @(posedge clk);
	enable=1;
end


///////////////////// inputs///////////////

initial 
begin

	input_byte=0;
	
	@(posedge enable);

	for(k=0;k<(number*204);k=k+1)
	begin

		input_byte=in_mem[k];
		
		@(posedge clk);@(posedge clk);
		for(in_t=0; in_t < lim; in_t=in_t+1)
			@(posedge clk); 
	end 

end

//////////////////////////////outputs////////////////////////
always @ (posedge(clk))
begin
	if(Valid_out && CEO)
		begin
			true_out = out_mem[h];
			
			if(true_out !== Out_byte)
				begin
					//$display("Error at out no. %d !!!!!!!!!!!!!",h);
					err=err+1;
				end
			h=h+1;
			
			if(h == (number*188) )
				begin
					if (err == 0)
						$display("No Errors !!!!!!!!!!!!!");
					else
						$display("Total Errors =  %d !!!!!!!!!!!!!",err);
					$finish;
				end
			
		end
end

endmodule
