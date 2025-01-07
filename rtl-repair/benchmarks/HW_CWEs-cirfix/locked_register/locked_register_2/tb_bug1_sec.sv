module tb_bug1;

    reg clk, resetn, write, lock_status, debug_unlocked;
    reg [15:0] Data_in;
    wire [15:0] Data_out; 
    
    // duration for each bit = 20 * timescale = 20 * 1 ns  = 20ns
    localparam period = 20;
    locked_register UUT (
        .clk(clk),
        .resetn(resetn),
        .write(write),
        .Data_in(Data_in),
        .lock_status(lock_status),
        .debug_unlocked(debug_unlocked),
        .Data_out(Data_out)
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
      $fwrite(f, "time,Data_in,resetn,write,lock_status,debug_unlocked,Data_out\n");
      forever begin
      @(posedge clk);
          $fwrite(f, "%g,%d,%d,%d,%d,%d,%d\n", $time,Data_in,resetn,write,lock_status,debug_unlocked,Data_out);
      end
    end

    initial begin

        // set inputs
        resetn=0;
        Data_in=16'h0010;
        write=0;
        lock_status=0;
        debug_unlocked=0;
        # period;

        resetn=1;
        Data_in=16'h1010;
        write=1;
        lock_status=0;
        debug_unlocked=0;
        # period;
        // check output
        if(Data_out !== 16'h1010 ) begin
            $display("test 1 failed");
            // $finish;
        end
        // else $display("load =%b, amount = %b, ena=%b, q=%b",load,amount,ena, q);

        // set inputs
        resetn=1;
        Data_in=16'h0010;
        write=1;
        lock_status=0;
        debug_unlocked=0;
        # period;
        // check output
        if(Data_out !== 16'h0010 ) begin
            $display("test 2 failed");
            // $finish;
        end

        // set inputs
        resetn=1;
        Data_in=16'h1010;
        write=0;
        lock_status=0;
        debug_unlocked=0;
        # period;

        resetn=1;
        Data_in=16'h1111;
        write=1;
        lock_status=1;
        debug_unlocked=1;
        # period;

        resetn=1;
        Data_in=16'h1011;
        write=0;
        lock_status=1;
        debug_unlocked=1;
        # period;

        resetn=1;
        Data_in=16'h1101;
        write=1;
        lock_status=0;
        debug_unlocked=1;
        # period;

        resetn=0;
        Data_in=16'h0101;
        write=1;
        lock_status=1;
        debug_unlocked=1;
        # period;


        resetn=1;
        Data_in=16'h1001;
        write=0;
        lock_status=1;
        debug_unlocked=1;
        # period;


        // set inputs
        resetn=1;
        Data_in=16'h0011;
        write=1;
        lock_status=1;
        debug_unlocked=0;
        # period;
        // check output

        $display("all tests passed");
        $finish;

    end


endmodule