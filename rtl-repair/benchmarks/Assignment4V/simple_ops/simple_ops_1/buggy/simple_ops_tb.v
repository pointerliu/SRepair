module tb;
  reg clk;
  reg instrumented_clk;
  reg rstn;
  reg t;


  reg [3:0] x;
  wire [3:0] y;

  simple_ops_test u0 (
    .x(x),
    .y(y)
  );

  always #5 clk = ~clk;
  always #20 instrumented_clk = ~instrumented_clk;

  integer f;

`ifdef DUMP_TRACE // used for our OSDD calculations
  initial begin
    $dumpfile("dump.vcd");
    $dumpvars(0, u0);
  end
`endif // DUMP_TRACE

  initial begin
    f = $fopen("test.txt", "w");
    $fwrite(f, "time,x,y\n");
    forever begin
        @(posedge clk);
        $fwrite(f, "%g,%d,%d\n", $time,x,y);
    end

  end
reg [3:0] i;
  initial begin
    {rstn, clk, t, instrumented_clk} <= 0;
    $monitor ("T=%0t rstn=%0b q=%0d", $time, x, y);
    repeat(2) @(posedge clk);
    rstn <= 1;

    for(i=1;i<8;i=i+1)begin
        #20 x=i;
    end

  // #20 $fclose(f);
  #10 $finish;
  end
endmodule
