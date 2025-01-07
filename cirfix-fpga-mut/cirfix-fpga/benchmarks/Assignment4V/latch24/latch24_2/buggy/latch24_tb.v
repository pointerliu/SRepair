
module latch24_tb;
  
 parameter bit_width=24;
  
 reg [bit_width-1:0] d;
  
 wire [bit_width-1:0] q;
  
 reg clk;
  reg instrumented_clk;
 integer f;
  
 initial
  
 begin
      f = $fopen("test.txt", "w");
      $display("time\t d clk q");
      $fdisplay(f, "time,d,clk,q");
    instrumented_clk = 0;
    
      clk=0;
      d=24'b1111_1111_1111_1111_1111_1111;     
     
 end 
 always #4 d=d-1;

  
 always #1 clk=~clk;
  
 
 latch24_test m(.d(d),.clk(clk),.q(q));  
   

 initial begin
         
    $dumpfile("test.vcd");
            
    $dumpvars;
            
    $monitor("%g\t %b %b %b",$time,d,clk,q);    
            
    #200 $finish;
  
 end   
    always @(instrumented_clk) begin
      $fstrobe(f, "%g,%b,%b,%b",$time,d,clk,q);
    end
    always #1 instrumented_clk = ~ instrumented_clk;

endmodule
