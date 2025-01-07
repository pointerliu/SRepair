module tb;
  reg clk;
  reg rstn;
  reg t;

  reg ENA;
  reg CLR;
  wire F_IN;
  wire [23:0] Q;

  counter6bit_test u0 (
        .ENA(ENA),
        .CLR(CLR),
        .F_IN(F_IN),
        .Q(Q)
    );

  always #5 clk = ~clk;
  assign F_IN = clk;
  integer f;

`ifdef DUMP_TRACE // used for our OSDD calculations
  initial begin
    $dumpfile("dump.vcd");
    $dumpvars(0, u0);
  end
`endif // DUMP_TRACE

  initial begin
    f = $fopen("test.txt", "w");
    $fwrite(f, "time,ENA,CLR,F_IN,Q\n");
    forever begin
     @(posedge clk);
         $fwrite(f, "%g,%d,%d,%d,%d\n", $time,ENA,CLR,F_IN,Q);
    end
  end

    reg [3:0] i = 0;
  initial begin
    {rstn, clk, t} <= 0;
    // $monitor ("T=%0t rstn=%0b x=%0d y=%0d", $time, rstn, x, y);
    repeat(2) @(posedge clk);
    CLR = 1;
    #20
    CLR = 0;
    ENA = 1;

  // #20 $fclose(f);
  #835
  CLR = 1;
  #20
  CLR = 0;
  #400 $finish;
  end
endmodule
