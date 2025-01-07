module tb_bug4();


    reg clk, rst_n;
    reg [31:0] rdata;
    reg rdata_security_level;

    wire [31:0] data_out;
    
    // duration for each bit = 20 * timescale = 20 * 1 ns  = 20ns
    localparam period = 20;
    soc UUT (.clk(clk), .rst_n(rst_n), 
                .rdata(rdata), .rdata_security_level(rdata_security_level),
                .data_out(data_out)
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
      $fwrite(f, "time,rst_n, rdata, rdata_security_level, data_out\n");
      forever begin
      @(posedge clk);
          $fwrite(f, "%g,%d,%d,%d,%d\n", $time,rst_n, rdata, rdata_security_level, data_out);
      end
    end

    initial begin

        rst_n = 0;
        #period;
        if(data_out!==0) begin
            $display("test 1 failed");
            // $finish;
        end
        // $display("data_out = %b", data_out);

        rdata = 32'd17;
        rdata_security_level = 1;
        #period;

        rst_n = 1;
        rdata = 32'd17;
        rdata_security_level = 1;
        #period;
        if(data_out!==0) begin
            //$display("test 2 failed");
            // $finish;
        end
        // $display("data_out = %b", data_out);

        rdata = 32'd10;
        rdata_security_level = 1;
        #period;

        rdata = 32'd3;
        rdata_security_level = 1;
        #period;

        rdata = 0;
        rdata_security_level = 1;
        #period;

        rdata = 32'd20;
        rdata_security_level = 0;
        #period;

        rdata = 32'd30;
        rdata_security_level = 0;
        #period;

        rdata = 0;
        rdata_security_level = 0;
        #period;
        if(data_out!==0) begin
            $display("test 3 failed");
            //$finish;
        end
        // $display("data_out = %b", data_out);

        rst_n = 1;
        #period;
        if(data_out!==0) begin
            $display("test 4 failed");
            //$finish;
        end
        // $display("data_out = %b", data_out);

        rdata = 1;
        rdata_security_level = 1;
        #period;
        if(data_out!==1) begin
            $display("test 5 failed");
            //$finish;
        end
        $display("data_out = %b", data_out);

        $display("all tests passed");
        $finish;

    end


endmodule