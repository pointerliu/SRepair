module tb_bug2;

    reg clk, resetn, unlock, d;
    wire locked;

    reg locked_imm_value;
    
    // duration for each bit = 20 * timescale = 20 * 1 ns  = 20ns
    localparam period = 20;
    lock_on_reset UUT (
        .clk(clk), .resetn(resetn), .unlock(unlock), .locked(locked), .d(d)
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
      $fwrite(f, "time,resetn,unlock,d,locked\n");
      forever begin
      @(posedge clk);
          $fwrite(f, "%g,%d,%d,%d,%d\n", $time,resetn,unlock,d,locked);
      end
    end

    initial begin

        resetn=0;
        unlock=0;
        d=1;
        # period;

        // get out of reset
        resetn=1;
        # period;

        // unlock and assign 1 to locked
        unlock = 1;
        d = 1;
        # period;
        if(locked !== 1 ) begin
            $display("test 1 failed");
            //$finish;
        end

        // assign 0 to locked
        d = 0;
        # period;
        if(locked !== 0 ) begin
            $display("test 2 failed");
            //$finish;
        end

        // lock and assign 1 to locked. locked should not change, should remain 0
        unlock = 0;
        #period;
        d = 1;
        # period;
        if(locked !== 0 ) begin
            $display("test 3 failed");
            //$finish;
        end

        // assign 1 to locked
        unlock=1;
        # period;
        d = 1;
        # period;

        // lock and assign 0 to locked. locked should not change, should remain 1
        unlock = 0;
        #period;
        d = 0;
        # period;
        if(locked !== 1 ) begin
            $display("test 4 failed");
            //$finish;
        end
        
        $display("all tests passed");
        $finish;

    end


endmodule