module decl7s_tb;
  
  reg  [3:0] a;
  reg instrumented_clk;
  wire  [6:0] led7s;
  
  integer i;
  integer f;
  initial  begin
  #0 f=$fopen("test.txt", "w");
  #0 $display("time\ta\tled7s");
  #0 $fdisplay(f, "time,a,led7s");
    instrumented_clk = 0;
  i=16;a=4'b0000;
  while(i>0) begin      
     #1 a=a+4'b0001;      
      i=i-1;
    end
  end  
  decl7s_test m(.a(a),.led7s(led7s)); 
  initial begin
         $dumpfile("test.vcd");
         $dumpvars(1, decl7s_tb);
         $monitor("%g\t %b %b",$time,a,led7s);
         #60 $finish;
  end    
    always @(instrumented_clk) begin
      $fstrobe(f, "%g,%b,%b",$time,a,led7s);
    end
    always #1 instrumented_clk = ~ instrumented_clk;
endmodule
