module JG3_tb;
  
  reg  [2:0] ABC;
  reg instrumented_clk;
  wire  X;
  wire Y;
  
  integer i;
  integer f;
  initial  begin
  #0 $display("time\tABC\tX\tY");
  #0 $fdisplay(f, "time,ABC,X,Y");
    instrumented_clk = 0;
  i=7;ABC=3'b000;
  while(i>0) begin      
     #1 ABC=ABC+3'b001;      
      i=i-1;
    end
  end  
  JG3 m(.ABC(ABC),.X(X),.Y(Y)); 
  initial begin
         f = $fopen("test.txt", "w");
         $dumpfile("test.vcd");
         $monitor("%1d\t%b\t%b\t%b",$time,ABC,X,Y);
         $dumpvars;
         #60 $finish;
  end    
    always @(instrumented_clk) begin
      $fstrobe(f, "%1d,%b,%b,%b",$time,ABC,X,Y);
    end
    always #1 instrumented_clk = ~ instrumented_clk;
endmodule
