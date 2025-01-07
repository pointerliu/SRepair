

module xlnxstream_2018_3 #
(
  parameter C_M_AXIS_TDATA_WIDTH = 32,
  parameter C_M_START_COUNT = 32
)
(
  input wire M_AXIS_ACLK,
  input wire M_AXIS_ARESETN,
  output wire M_AXIS_TVALID,
  output wire [C_M_AXIS_TDATA_WIDTH-1:0] M_AXIS_TDATA,
  output wire [C_M_AXIS_TDATA_WIDTH/8-1:0] M_AXIS_TSTRB,
  output wire M_AXIS_TLAST,
  input wire M_AXIS_TREADY
);

  localparam NUMBER_OF_OUTPUT_WORDS = 8;
  localparam WAIT_COUNT_BITS = $clog2(C_M_START_COUNT);
  localparam bit_num = $clog2((NUMBER_OF_OUTPUT_WORDS + 1));
  parameter [1:0] IDLE = 2'b00;parameter [1:0] INIT_COUNTER = 2'b01;parameter [1:0] SEND_STREAM = 2'b10;
  reg [1:0] mst_exec_state;
  reg [bit_num-1:0] read_pointer;
  reg [WAIT_COUNT_BITS-1:0] count;
  wire axis_tvalid;
  reg axis_tvalid_delay;
  wire axis_tlast;
  reg axis_tlast_delay;
  reg [C_M_AXIS_TDATA_WIDTH-1:0] stream_data_out;
  wire tx_en;
  reg tx_done;
  assign M_AXIS_TVALID = axis_tvalid_delay;
  assign M_AXIS_TDATA = stream_data_out;
  assign M_AXIS_TLAST = axis_tlast_delay;
  assign M_AXIS_TSTRB = { C_M_AXIS_TDATA_WIDTH / 2'b10{ 32 } };

  always @(posedge M_AXIS_ACLK) if(!M_AXIS_ARESETN) begin
    mst_exec_state <= IDLE;
    count <= 0;
  end else case(mst_exec_state)
    IDLE: mst_exec_state <= INIT_COUNTER;
    INIT_COUNTER: if(count == C_M_START_COUNT - 1) mst_exec_state <= SEND_STREAM; 
    else begin
      count <= count + 1;
      mst_exec_state <= INIT_COUNTER;
    end
    SEND_STREAM: if(tx_done) mst_exec_state <= IDLE; 
    else mst_exec_state <= SEND_STREAM;
  endcase

  assign axis_tvalid = (mst_exec_state == SEND_STREAM) && (read_pointer < NUMBER_OF_OUTPUT_WORDS);
  assign axis_tlast = read_pointer == NUMBER_OF_OUTPUT_WORDS - 1;

  always @(posedge M_AXIS_ACLK) if(!M_AXIS_ARESETN) begin
    axis_tvalid_delay <= 1'b0;
    axis_tlast_delay <= 1'b0;
  end else begin
    axis_tvalid_delay <= axis_tvalid;
    if(!axis_tvalid_delay || M_AXIS_TREADY) axis_tlast_delay <= axis_tlast; 
  end


  always @(posedge M_AXIS_ACLK) if(!M_AXIS_ARESETN) begin
    read_pointer <= 0;
    tx_done <= 1'b0;
  end else if(read_pointer <= NUMBER_OF_OUTPUT_WORDS - 1) begin
    if(tx_en) begin
      read_pointer <= read_pointer + 1;
      tx_done <= 1'b0;
    end 
  end else if(read_pointer == NUMBER_OF_OUTPUT_WORDS) begin
    tx_done <= 1'b1;
  end 

  assign tx_en = M_AXIS_TREADY && axis_tvalid;

  always @(posedge M_AXIS_ACLK) if(!M_AXIS_ARESETN) stream_data_out <= 1; 
  else if(tx_en) stream_data_out <= read_pointer + 32'b1; 


  initial count = 0;


  initial mst_exec_state = IDLE;


  initial read_pointer = 0;


  initial tx_done = 0;


endmodule

