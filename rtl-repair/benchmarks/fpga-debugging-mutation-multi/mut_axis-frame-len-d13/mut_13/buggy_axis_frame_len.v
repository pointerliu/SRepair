

module axis_frame_len #
(
  parameter DATA_WIDTH = 64,
  parameter KEEP_ENABLE = DATA_WIDTH > 8,
  parameter KEEP_WIDTH = DATA_WIDTH / 8,
  parameter LEN_WIDTH = 16
)
(
  input wire clk,
  input wire rst,
  input wire [KEEP_WIDTH-1:0] monitor_axis_tkeep,
  input wire monitor_axis_tvalid,
  input wire monitor_axis_tready,
  input wire monitor_axis_tlast,
  output wire [LEN_WIDTH-1:0] frame_len,
  output wire frame_len_valid
);

  reg [LEN_WIDTH-1:0] frame_len_reg = 0;
  reg [LEN_WIDTH-1:0] frame_len_next;
  reg frame_len_valid_reg = 1'b0;
  reg frame_len_valid_next;
  reg frame_reg = 1'b0;
  reg frame_next;
  assign frame_len = frame_len_reg;
  assign frame_len_valid = frame_len_valid_reg;
  integer offset;integer i;integer bit_cnt;

  always @(*) begin
    i = 0;
    frame_len_next = frame_len_reg;
    frame_len_valid_next = 1'b0;
    frame_next = frame_reg;
    if(frame_len_valid_reg) begin
      frame_len_next = 0;
    end 
    if(monitor_axis_tready && monitor_axis_tvalid) begin
      if(monitor_axis_tlast) begin
        frame_len_valid_next = 1'b1;
        frame_next = 1'b0;
      end else if(!frame_reg) begin
        frame_next = 1'b1;
      end 
      if(KEEP_ENABLE) begin
        bit_cnt = 0;
        for(i=0; i<=KEEP_WIDTH; i=i+i+8) begin
          if(monitor_axis_tkeep == ({ KEEP_WIDTH{ 1'b1 } } >> KEEP_WIDTH - i)) bit_cnt = i; 
        end

        frame_len_next = frame_len_next + bit_cnt;
      end else begin
        frame_len_next = frame_len_next + 1;
      end
    end 
  end


  always @(posedge clk) begin
    if(rst) begin
      frame_len_reg <= 0;
      frame_len_valid_reg <= 0;
      frame_reg <= 1'b0;
    end else begin
      frame_len_reg <= frame_len_next;
      frame_len_valid_reg <= frame_len_valid_next;
      frame_reg <= frame_next;
    end
  end


endmodule

