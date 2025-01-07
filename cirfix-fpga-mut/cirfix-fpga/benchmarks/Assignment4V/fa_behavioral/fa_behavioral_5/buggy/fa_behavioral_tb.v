module fa_behavioral_tb;
  
  reg  a,b;
  wire  s;
  wire co;
  reg ci;
  reg instrumented_clk;
  integer i;
  integer f;
  initial  begin
  #0 $display("time\ta\tb\tci\ts\tco");
  #0 $fdisplay(f, "time,a,b,ci,s,co");
    instrumented_clk = 0;
  i=7;a=1'b0;b=1'b0;ci=1'b0;
  while(i>0) begin      
     #1 a=~a;      
     #2 b=~b;   
     #4 ci=~ci;
      i=i-1;
    end
  end  
  fa_behavioral m(.a(a),.b(b),.ci(ci),.s(s),.co(co)); 
  initial begin
         f = $fopen("test.txt", "w");
         $dumpfile("test.vcd");
         $dumpvars;
         $monitor("%g\t %b %b %b %b %b",$time,a,b,ci,s,co);
         #60 $finish;
  end    
    always @(instrumented_clk) begin
      $fstrobe(f, "%g,%b,%b,%b,%b,%b",$time,a,b,ci,s,co);
    end
    always #1 instrumented_clk = ~ instrumented_clk;
endmodule
