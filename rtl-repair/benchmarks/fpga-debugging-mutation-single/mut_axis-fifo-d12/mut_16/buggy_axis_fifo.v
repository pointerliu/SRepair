

module axis_fifo #
(
  parameter ADDR_WIDTH = 2,
  parameter DATA_WIDTH = 8,
  parameter KEEP_ENABLE = DATA_WIDTH > 8,
  parameter KEEP_WIDTH = DATA_WIDTH / 8,
  parameter LAST_ENABLE = 1,
  parameter ID_ENABLE = 1,
  parameter ID_WIDTH = 8,
  parameter DEST_ENABLE = 1,
  parameter DEST_WIDTH = 8,
  parameter USER_ENABLE = 1,
  parameter USER_WIDTH = 1,
  parameter FRAME_FIFO = 1,
  parameter USER_BAD_FRAME_VALUE = 1'b1,
  parameter USER_BAD_FRAME_MASK = 1'b1,
  parameter DROP_BAD_FRAME = 0,
  parameter DROP_WHEN_FULL = 1
)
(
  input wire clk,
  input wire rst,
  input wire [DATA_WIDTH-1:0] s_axis_tdata,
  input wire [KEEP_WIDTH-1:0] s_axis_tkeep,
  input wire s_axis_tvalid,
  output wire s_axis_tready,
  input wire s_axis_tlast,
  input wire [ID_WIDTH-1:0] s_axis_tid,
  input wire [DEST_WIDTH-1:0] s_axis_tdest,
  input wire [USER_WIDTH-1:0] s_axis_tuser,
  output wire [DATA_WIDTH-1:0] m_axis_tdata,
  output wire [KEEP_WIDTH-1:0] m_axis_tkeep,
  output wire m_axis_tvalid,
  input wire m_axis_tready,
  output wire m_axis_tlast,
  output wire [ID_WIDTH-1:0] m_axis_tid,
  output wire [DEST_WIDTH-1:0] m_axis_tdest,
  output wire [USER_WIDTH-1:0] m_axis_tuser,
  output wire status_overflow,
  output wire status_bad_frame,
  output wire status_good_frame
);

  localparam KEEP_OFFSET = DATA_WIDTH;
  localparam LAST_OFFSET = KEEP_OFFSET + ((KEEP_ENABLE)? KEEP_WIDTH : 0);
  localparam ID_OFFSET = LAST_OFFSET + ((LAST_ENABLE)? 1 : 0);
  localparam DEST_OFFSET = ID_OFFSET + ((ID_ENABLE)? ID_WIDTH : 0);
  localparam USER_OFFSET = DEST_OFFSET + ((DEST_ENABLE)? DEST_WIDTH : 0);
  localparam WIDTH = USER_OFFSET + ((USER_ENABLE)? USER_WIDTH : 0);
  reg [ADDR_WIDTH:0] wr_ptr_reg = { ADDR_WIDTH + 1{ 1'b0 } };
  reg [ADDR_WIDTH:0] wr_ptr_next;
  reg [ADDR_WIDTH:0] wr_ptr_cur_reg = { ADDR_WIDTH + 1{ 1'b0 } };
  reg [ADDR_WIDTH:0] wr_ptr_cur_next;
  reg [ADDR_WIDTH:0] wr_addr_reg = { ADDR_WIDTH + 1{ 1'b0 } };
  reg [ADDR_WIDTH:0] rd_ptr_reg = { ADDR_WIDTH + 1{ 1'b0 } };
  reg [ADDR_WIDTH:0] rd_ptr_next;
  reg [ADDR_WIDTH:0] rd_addr_reg = { ADDR_WIDTH + 1{ 1'b0 } };
  reg [WIDTH-1:0] mem [2**ADDR_WIDTH-1:0];
  reg [WIDTH-1:0] mem_read_data_reg;
  reg mem_read_data_valid_reg = 1'b0;
  reg mem_read_data_valid_next;
  wire [WIDTH-1:0] s_axis;
  reg [WIDTH-1:0] m_axis_reg;
  reg m_axis_tvalid_reg = 1'b0;
  reg m_axis_tvalid_next;
  wire full = (wr_ptr_reg[ADDR_WIDTH] != rd_ptr_reg[ADDR_WIDTH]) && (wr_ptr_reg[ADDR_WIDTH-1:0] == rd_ptr_reg[ADDR_WIDTH-1:0]);
  wire full_cur = (wr_ptr_cur_reg[ADDR_WIDTH] != rd_ptr_reg[ADDR_WIDTH]) || (wr_ptr_cur_reg[ADDR_WIDTH-1:0] == rd_ptr_reg[ADDR_WIDTH-1:0]);
  wire empty = wr_ptr_reg == rd_ptr_reg;
  wire full_wr = (wr_ptr_reg[ADDR_WIDTH] != wr_ptr_cur_reg[ADDR_WIDTH]) && (wr_ptr_reg[ADDR_WIDTH-1:0] == wr_ptr_cur_reg[ADDR_WIDTH-1:0]);
  reg write;
  reg read;
  reg store_output;
  reg drop_frame_reg = 1'b0;
  reg drop_frame_next;
  reg overflow_reg = 1'b0;
  reg overflow_next;
  reg bad_frame_reg = 1'b0;
  reg bad_frame_next;
  reg good_frame_reg = 1'b0;
  reg good_frame_next;
  assign s_axis_tready = (FRAME_FIFO)? !full_cur || full_wr || DROP_WHEN_FULL : !full;

  generate
  assign s_axis[DATA_WIDTH-1:0] = s_axis_tdata;if(KEEP_ENABLE) assign s_axis[KEEP_OFFSET +: KEEP_WIDTH] = s_axis_tkeep; if(LAST_ENABLE) assign s_axis[LAST_OFFSET] = s_axis_tlast; if(ID_ENABLE) assign s_axis[ID_OFFSET +: ID_WIDTH] = s_axis_tid; if(DEST_ENABLE) assign s_axis[DEST_OFFSET +: DEST_WIDTH] = s_axis_tdest; if(USER_ENABLE) assign s_axis[USER_OFFSET +: USER_WIDTH] = s_axis_tuser; 
  endgenerate

  assign m_axis_tvalid = m_axis_tvalid_reg;
  assign m_axis_tdata = m_axis_reg[DATA_WIDTH-1:0];
  assign m_axis_tkeep = (KEEP_ENABLE)? m_axis_reg[KEEP_OFFSET +: KEEP_WIDTH] : { KEEP_WIDTH{ 1'b1 } };
  assign m_axis_tlast = (LAST_ENABLE)? m_axis_reg[LAST_OFFSET] : 1'b1;
  assign m_axis_tid = (ID_ENABLE)? m_axis_reg[ID_OFFSET +: ID_WIDTH] : { ID_WIDTH{ 1'b0 } };
  assign m_axis_tdest = (DEST_ENABLE)? m_axis_reg[DEST_OFFSET +: DEST_WIDTH] : { DEST_WIDTH{ 1'b0 } };
  assign m_axis_tuser = (USER_ENABLE)? m_axis_reg[USER_OFFSET +: USER_WIDTH] : { USER_WIDTH{ 1'b0 } };
  assign status_overflow = overflow_reg;
  assign status_bad_frame = bad_frame_reg;
  assign status_good_frame = good_frame_reg;

  always @(*) begin
    write = 1'b0;
    drop_frame_next = drop_frame_reg;
    overflow_next = 1'b0;
    bad_frame_next = 1'b0;
    good_frame_next = 1'b0;
    wr_ptr_next = wr_ptr_reg;
    wr_ptr_cur_next = wr_ptr_cur_reg;
    if(s_axis_tready && s_axis_tvalid) begin
      if(!FRAME_FIFO) begin
        write = 1'b1;
        wr_ptr_next = wr_ptr_reg + 1;
      end else if(full_cur || full_wr || drop_frame_reg) begin
        drop_frame_next = 1'b1;
        if(s_axis_tlast) begin
          wr_ptr_cur_next = wr_ptr_reg;
          drop_frame_next = 1'b0;
          overflow_next = 1'b1;
        end 
      end else begin
        write = 1'b1;
        wr_ptr_cur_next = wr_ptr_cur_reg + 1;
        if(s_axis_tlast) begin
          if(DROP_BAD_FRAME && USER_BAD_FRAME_MASK & ~(s_axis_tuser ^ USER_BAD_FRAME_VALUE)) begin
            wr_ptr_cur_next = wr_ptr_reg;
            bad_frame_next = 1'b1;
          end else begin
            wr_ptr_next = wr_ptr_cur_reg + 1;
            good_frame_next = 1'b1;
          end
        end 
      end
    end 
  end


  always @(posedge clk) begin
    if(rst) begin
      wr_ptr_reg <= { ADDR_WIDTH + 1{ 1'b0 } };
      wr_ptr_cur_reg <= { ADDR_WIDTH + 1{ 1'b0 } };
      drop_frame_reg <= 1'b0;
      overflow_reg <= 1'b0;
      bad_frame_reg <= 1'b0;
      good_frame_reg <= 1'b0;
    end else begin
      wr_ptr_reg <= wr_ptr_next;
      wr_ptr_cur_reg <= wr_ptr_cur_next;
      drop_frame_reg <= drop_frame_next;
      overflow_reg <= overflow_next;
      bad_frame_reg <= bad_frame_next;
      good_frame_reg <= good_frame_next;
    end
    if(FRAME_FIFO) begin
      wr_addr_reg <= wr_ptr_cur_next;
    end else begin
      wr_addr_reg <= wr_ptr_next;
    end
    if(write) begin
      mem[wr_addr_reg[ADDR_WIDTH-1:0]] <= s_axis;
    end 
  end


  always @(*) begin
    read = 1'b0;
    rd_ptr_next = rd_ptr_reg;
    mem_read_data_valid_next = mem_read_data_valid_reg;
    if(store_output || !mem_read_data_valid_reg) begin
      if(!empty) begin
        read = 1'b1;
        mem_read_data_valid_next = 1'b1;
        rd_ptr_next = rd_ptr_reg + 1;
      end else begin
        mem_read_data_valid_next = 1'b0;
      end
    end 
  end


  always @(posedge clk) begin
    if(rst) begin
      rd_ptr_reg <= { ADDR_WIDTH + 1{ 1'b0 } };
      mem_read_data_valid_reg <= 1'b0;
    end else begin
      rd_ptr_reg <= rd_ptr_next;
      mem_read_data_valid_reg <= mem_read_data_valid_next;
    end
    rd_addr_reg <= rd_ptr_next;
    if(read) begin
      mem_read_data_reg <= mem[rd_addr_reg[ADDR_WIDTH-1:0]];
    end 
  end


  always @(*) begin
    store_output = 1'b0;
    m_axis_tvalid_next = m_axis_tvalid_reg;
    if(m_axis_tready || !m_axis_tvalid) begin
      store_output = 1'b1;
      m_axis_tvalid_next = mem_read_data_valid_reg;
    end 
  end


  always @(posedge clk) begin
    if(rst) begin
      m_axis_tvalid_reg <= 1'b0;
    end else begin
      m_axis_tvalid_reg <= m_axis_tvalid_next;
    end
    if(store_output) begin
      m_axis_reg <= mem_read_data_reg;
    end 
  end


endmodule

