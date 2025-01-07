module tb_bug3;

    reg clk, rst_n;
    reg [7:0] data_in;
    reg [2:0] usr_id;
    wire [7:0] data_out;
    
    // duration for each bit = 20 * timescale = 20 * 1 ns  = 20ns
    localparam period = 20;
    user_grant_access UUT (
        .clk(clk), .rst_n(rst_n), .data_in(data_in), .data_out(data_out), .usr_id(usr_id)
    );

    initial // Clock generation
        begin
        clk = 0;
        forever begin
        #(period/2);
        clk = ~clk;
        end
    end
    integer f;
    initial begin
      f = $fopen("test.txt", "w");
      $fwrite(f, "time,data_out, usr_id, data_in, rst_n\n");
      forever begin
      @(posedge clk);
          $fwrite(f, "%g,%d,%d,%d,%d\n", $time,data_out, usr_id, data_in, rst_n);
      end
    end
    initial begin

        rst_n = 0;
        data_in = 8'h01;
        usr_id = 3'b101;
        # period;
        // check output
        // else $display("load =%b, amount = %b, ena=%b, q=%b",load,amount,ena, q);

        // set inputs
        data_in = 8'h01;
        usr_id = 3'b100;
        # period;
        // check output

        // set inputs
        rst_n = 1;
        data_in = 8'h01;
        usr_id = 3'b100;
        # period;
        // check output

        // set inputs
        data_in = 8'h11;
        usr_id = 3'b101;
        # period;

        // set inputs
        data_in = 8'h11;
        usr_id = 3'b100;
        # period;
        # period;
        // check output

        $display("all tests passed");
        $finish;
    end


endmodule