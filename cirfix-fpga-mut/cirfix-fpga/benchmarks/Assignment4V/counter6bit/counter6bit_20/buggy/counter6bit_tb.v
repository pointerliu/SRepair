

module counter6bit_tb();
    reg ENA,CLR,F_IN;
  reg instrumented_clk;
   
    wire [23:0] Q;
    integer f;
   
    initial
    begin
        F_IN = 0;
        forever
        #1 F_IN = ~F_IN;
       
    end
   
    initial
    begin
    ENA = 1;
    CLR = 1;
    #8 CLR = 0;
    #160 ENA = 0;
    #20 ENA = 1;CLR = 1;
    #6 CLR = 0;
    end
   
   counter6bit_test M(ENA,CLR,F_IN,Q);

  initial begin
    f = $fopen("test.txt", "w");
      $display("time\t ENA CLR F_IN Q");
      $fdisplay(f, "time,ENA,CLR,F_IN,Q");
    instrumented_clk = 0;
         
  $dumpfile("test.vcd");
         
  $dumpvars;
         
  $monitor("%g\t %b %b %b %b",$time,ENA,CLR,F_IN,Q);   
         
  #200 $finish;
  
  end
    always @(instrumented_clk) begin
      $fstrobe(f, "%g,%b,%b,%b,%b",$time,ENA,CLR,F_IN,Q);
    end
    always #1 instrumented_clk = ~ instrumented_clk;
endmodule