module mux21_tb;
  
  reg  a,b;
  wire  y;
  reg s;
  reg instrumented_clk;
  integer i;
  integer f;
  initial  begin
  #0 $display("time\ta\tb\ts\ty");
  #0 $fdisplay(f, "time,a,b,s,y");
    instrumented_clk = 0;
  i=7;a=1'b0;b=1'b0;s=1'b0;
  while(i>0) begin      
     #1 a=~a;      
     #2 b=~b;   
     #4 s=~s;
      i=i-1;
    end
  end  
  mux21 m(.a(a),.b(b),.s(s),.y(y)); 
  initial begin
         f = $fopen("test.txt", "w");
         $dumpfile("test.vcd");
         $dumpvars(1, mux21_tb);
         $monitor("%1d\t%b\t%b\t%b\t%b",$time,a,b,s,y);
         #60 $finish;
  end    
    always @(instrumented_clk) begin
      $fstrobe(f,"%1d,%b,%b,%b,%b",$time,a,b,s,y);
    end
    always #1 instrumented_clk = ~ instrumented_clk;
endmodule
