module tb;
  reg clk;
  reg rstn;
  reg t;
  reg [3:0] x;
  reg [3:0] c;
  wire [3:0] y;

  simple_ops_test u0 (
        .clk(clk),
        .rstn(rstn),
        .x(x),
        .c(c),
        .y(y)
    );

  always #5 clk = ~clk;

  integer f;

`ifdef DUMP_TRACE // used for our OSDD calculations
  initial begin
    $dumpfile("dump.vcd");
    $dumpvars(0, u0);
  end
`endif // DUMP_TRACE

  initial begin
    f = $fopen("test.txt", "w");
    $fwrite(f, "time,rstn,x,c,y\n");
    forever begin
     @(posedge clk);
         $fwrite(f, "%g,%d,%d,%d,%d\n", $time,rstn,x,c,y);
    end
  end

    reg [3:0] i = 0;
  initial begin
    {rstn, clk, t} <= 0;
    $monitor ("T=%0t rstn=%0b x=%0d y=%0d", $time, rstn, x, y);
    repeat(2) @(posedge clk);
    rstn <= 1;

    repeat(2)
    for (i = 1; i < 15; i++) begin
        #5
        x = i;
        c = 15 - x;
    end

  // #20 $fclose(f);
  #5 $finish;
  end
endmodule
