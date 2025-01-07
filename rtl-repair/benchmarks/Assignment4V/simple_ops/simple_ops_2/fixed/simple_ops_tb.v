module tb;
  reg clk;
  reg instrumented_clk;
  reg rstn;
  reg t;
  wire [1:0] q;

  simple_ops_test u0 (  .clk(clk),
            .rstn(rstn),
          .x(q));

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
    $fwrite(f, "time,rstn,x\n");
    forever begin
        @(posedge clk);
        $fwrite(f, "%g,%d,%d\n", $time,rstn,q);
    end

  end

  initial begin
    {rstn, clk, t, instrumented_clk} <= 0;
    $monitor ("T=%0t rstn=%0b q=%0d", $time, rstn, q);
    repeat(2) @(posedge clk);
    rstn <= 1;

  // #20 $fclose(f);
  #100 $finish;
  end
endmodule
