`timescale 1ns/1ns
module decoder3e_tb;
  reg [2:0] a;
  reg ena;
  reg instrumented_clk;
  wire[7:0] y;
  integer i; 
  integer f;
  initial  begin
        f = $fopen("test.txt", "w");
        $dumpfile("test.vcd");  
        $dumpvars(1, decoder3e_tb);        
        $monitor("%1d\t%b\t%b\t%b",
                $time,ena,a,y);
  end
  initial  begin
    #0 $display("time\tena\ta\ty");
    #0 $fdisplay(f, "time,ena,a,y");
    instrumented_clk = 0;
    #0 ena=1;a=0;
    for(i=1;i<8;i=i+1)begin
    #1 a=i;
    end
    #1 ena=0;
    #1 ena=1;a=0;
    #1 $finish;
  end
    always @(instrumented_clk) begin
      $fstrobe(f, "%1d,%b,%b,%b",
                $time,ena,a,y);
    end
    always #1 instrumented_clk = ~ instrumented_clk;
   decoder3e_test dec3e(a,ena,y);
endmodule
