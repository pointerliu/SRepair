

module xlnxdemo #
(
  parameter C_S_AXI_DATA_WIDTH = 32,
  parameter C_S_AXI_ADDR_WIDTH = 7
)
(
  input wire S_AXI_ACLK,
  input wire S_AXI_ARESETN,
  input wire [C_S_AXI_ADDR_WIDTH-1:0] S_AXI_AWADDR,
  input wire [2:0] S_AXI_AWPROT,
  input wire S_AXI_AWVALID,
  output wire S_AXI_AWREADY,
  input wire [C_S_AXI_DATA_WIDTH-1:0] S_AXI_WDATA,
  input wire [C_S_AXI_DATA_WIDTH/8-1:0] S_AXI_WSTRB,
  input wire S_AXI_WVALID,
  output wire S_AXI_WREADY,
  output wire [1:0] S_AXI_BRESP,
  output wire S_AXI_BVALID,
  input wire S_AXI_BREADY,
  input wire [C_S_AXI_ADDR_WIDTH-1:0] S_AXI_ARADDR,
  input wire [2:0] S_AXI_ARPROT,
  input wire S_AXI_ARVALID,
  output wire S_AXI_ARREADY,
  output wire [C_S_AXI_DATA_WIDTH-1:0] S_AXI_RDATA,
  output wire [1:0] S_AXI_RRESP,
  output wire S_AXI_RVALID,
  input wire S_AXI_RREADY
);

  reg [C_S_AXI_ADDR_WIDTH-1:0] axi_awaddr;
  reg axi_awready;
  reg axi_wready;
  reg [1:0] axi_bresp;
  reg axi_bvalid;
  reg [C_S_AXI_ADDR_WIDTH-1:0] axi_araddr;
  reg axi_arready;
  reg [C_S_AXI_DATA_WIDTH-1:0] axi_rdata;
  reg [1:0] axi_rresp;
  reg axi_rvalid;
  localparam ADDR_LSB = C_S_AXI_DATA_WIDTH / 32 + 1;
  localparam OPT_MEM_ADDR_BITS = 4;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg0;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg1;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg2;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg3;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg4;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg5;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg6;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg7;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg8;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg9;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg10;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg11;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg12;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg13;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg14;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg15;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg16;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg17;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg18;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg19;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg20;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg21;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg22;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg23;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg24;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg25;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg26;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg27;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg28;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg29;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg30;
  reg [C_S_AXI_DATA_WIDTH-1:0] slv_reg31;
  wire slv_reg_rden;
  wire slv_reg_wren;
  reg [C_S_AXI_DATA_WIDTH-1:0] reg_data_out;
  integer byte_index;
  assign S_AXI_AWREADY = axi_awready;
  assign S_AXI_WREADY = axi_wready;
  assign S_AXI_BRESP = axi_bresp;
  assign S_AXI_BVALID = axi_bvalid;
  assign S_AXI_ARREADY = axi_arready;
  assign S_AXI_RDATA = axi_rdata;
  assign S_AXI_RRESP = axi_rresp;
  assign S_AXI_RVALID = axi_rvalid;

  always @(posedge S_AXI_ACLK) begin
    if(S_AXI_ARESETN == 1'b0) begin
      axi_awready <= 1'b0;
    end else begin
      if(~axi_awready && S_AXI_AWVALID && S_AXI_WVALID && (!S_AXI_BVALID || S_AXI_BREADY)) begin
        axi_awready <= 1'b1;
      end else begin
        axi_awready <= 1'b0;
      end
    end
  end


  always @(posedge S_AXI_ACLK) begin
    if(S_AXI_ARESETN == 1'b0) begin
      axi_awaddr <= 0;
    end else begin
      if(~axi_awready && S_AXI_AWVALID && S_AXI_WVALID) begin
        axi_awaddr <= S_AXI_AWADDR;
      end 
    end
  end


  always @(posedge S_AXI_ACLK) begin
    if(S_AXI_ARESETN == 1'b0) begin
      axi_wready <= 1'b0;
    end else begin
      if(~axi_wready && S_AXI_WVALID && S_AXI_AWVALID && (!S_AXI_BVALID || S_AXI_BREADY)) begin
        axi_wready <= 1'b1;
      end else begin
        axi_wready <= 1'b0;
      end
    end
  end

  assign slv_reg_wren = axi_wready && S_AXI_WVALID && axi_awready && S_AXI_AWVALID;

  always @(posedge S_AXI_ACLK) begin
    if(S_AXI_ARESETN == 1'b0) begin
      slv_reg0 <= 0;
      slv_reg1 <= 0;
      slv_reg2 <= 0;
      slv_reg3 <= 0;
      slv_reg4 <= 0;
      slv_reg5 <= 0;
      slv_reg6 <= 0;
      slv_reg7 <= 0;
      slv_reg8 <= 0;
      slv_reg9 <= 0;
      slv_reg10 <= 0;
      slv_reg11 <= 0;
      slv_reg12 <= 0;
      slv_reg13 <= 0;
      slv_reg14 <= 0;
      slv_reg15 <= 0;
      slv_reg16 <= 0;
      slv_reg17 <= 0;
      slv_reg18 <= 0;
      slv_reg19 <= 0;
      slv_reg20 <= 0;
      slv_reg21 <= 0;
      slv_reg22 <= 0;
      slv_reg23 <= 0;
      slv_reg24 <= 0;
      slv_reg25 <= 0;
      slv_reg26 <= 0;
      slv_reg27 <= 0;
      slv_reg28 <= 0;
      slv_reg29 <= 0;
      slv_reg30 <= 0;
      slv_reg31 <= 0;
    end else begin
      if(slv_reg_wren) begin
        case(axi_awaddr[ADDR_LSB+OPT_MEM_ADDR_BITS:ADDR_LSB])
          5'h00: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg0[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h01: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg1[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h02: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg2[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h03: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg3[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h04: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg4[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h05: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg5[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h06: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg6[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h07: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg7[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h08: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg8[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h09: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg9[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h0A: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg10[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h0B: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg11[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h0C: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg12[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h0D: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg13[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h0E: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg14[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h0F: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg15[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h10: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg16[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h11: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg17[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h12: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg18[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h13: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg19[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h14: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg20[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h15: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg21[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h16: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg22[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h17: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg23[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h18: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg24[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h19: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg25[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h1A: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg26[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h1B: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg27[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h1C: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg28[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h1D: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg29[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h1E: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg30[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          5'h1F: for(byte_index=0; byte_index<=C_S_AXI_DATA_WIDTH/8-1; byte_index=byte_index+1) if(S_AXI_WSTRB[byte_index] == 1) begin
            slv_reg31[byte_index*8 +: 8] <= S_AXI_WDATA[byte_index*8 +: 8];
          end 

          default: begin
            slv_reg0 <= slv_reg0;
            slv_reg1 <= slv_reg1;
            slv_reg2 <= slv_reg2;
            slv_reg3 <= slv_reg3;
            slv_reg4 <= slv_reg4;
            slv_reg5 <= slv_reg5;
            slv_reg6 <= slv_reg6;
            slv_reg7 <= slv_reg7;
            slv_reg8 <= slv_reg8;
            slv_reg9 <= slv_reg9;
            slv_reg10 <= slv_reg10;
            slv_reg11 <= slv_reg11;
            slv_reg12 <= slv_reg12;
            slv_reg13 <= slv_reg13;
            slv_reg14 <= slv_reg14;
            slv_reg15 <= slv_reg15;
            slv_reg16 <= slv_reg16;
            slv_reg17 <= slv_reg17;
            slv_reg18 <= slv_reg18;
            slv_reg19 <= slv_reg19;
            slv_reg20 <= slv_reg20;
            slv_reg21 <= slv_reg21;
            slv_reg22 <= slv_reg22;
            slv_reg23 <= slv_reg23;
            slv_reg24 <= slv_reg24;
            slv_reg25 <= slv_reg25;
            slv_reg26 <= slv_reg26;
            slv_reg27 <= slv_reg27;
            slv_reg28 <= slv_reg28;
            slv_reg29 <= slv_reg29;
            slv_reg30 <= slv_reg30;
            slv_reg31 <= slv_reg31;
          end
        endcase
      end 
    end
  end


  always @(posedge S_AXI_ACLK) begin
    if(S_AXI_ARESETN == 1'b0) begin
      axi_bvalid <= 0;
      axi_bresp <= 2'b0;
    end else begin
      if(axi_awready && S_AXI_AWVALID && ~axi_bvalid && axi_wready && S_AXI_WVALID) begin
        axi_bvalid <= 1'b1;
        axi_bresp <= 2'b0;
      end else begin
        if(S_AXI_BREADY && axi_bvalid) begin
          axi_bvalid <= 1'b0;
        end 
      end
    end
  end


  always @(posedge S_AXI_ACLK) begin
    if(S_AXI_ARESETN == 1'b0) begin
      axi_arready <= 1'b0;
      axi_araddr <= 7'b0;
    end else begin
      if(~axi_arready && S_AXI_ARVALID && (!S_AXI_RVALID || S_AXI_RREADY)) begin
        axi_arready <= 1'b1;
        axi_araddr <= S_AXI_ARADDR;
      end else begin
        axi_arready <= 1'b0;
      end
    end
  end


  always @(posedge S_AXI_ACLK) begin
    if(S_AXI_ARESETN == 1'b0) begin
      axi_rvalid <= 0;
      axi_rresp <= 0;
    end else begin
      if(axi_arready && S_AXI_ARVALID && ~axi_rvalid) begin
        axi_rvalid <= 1'b1;
        axi_rresp <= 2'b0;
      end else if(axi_rvalid && S_AXI_RREADY) begin
        axi_rvalid <= 1'b0;
      end 
    end
  end

  assign slv_reg_rden = ~axi_arready + (S_AXI_ARVALID + S_AXI_ARVALID) && ~axi_rvalid;

  always @(*) begin
    reg_data_out = 0;
    case(axi_araddr[ADDR_LSB+OPT_MEM_ADDR_BITS:ADDR_LSB])
      5'h00: reg_data_out = slv_reg0;
      5'h01: reg_data_out = slv_reg1;
      5'h02: reg_data_out = slv_reg2;
      5'h03: reg_data_out = slv_reg3;
      5'h04: reg_data_out = slv_reg4;
      5'h05: reg_data_out = slv_reg5;
      5'h06: reg_data_out = slv_reg6;
      5'h07: reg_data_out = slv_reg7;
      5'h08: reg_data_out = slv_reg8;
      5'h09: reg_data_out = slv_reg9;
      5'h0A: reg_data_out = slv_reg10;
      5'h0B: reg_data_out = slv_reg11;
      5'h0C: reg_data_out = slv_reg12;
      5'h0D: reg_data_out = slv_reg13;
      5'h0E: reg_data_out = slv_reg14;
      5'h0F: reg_data_out = slv_reg15;
      5'h10: reg_data_out = slv_reg16;
      5'h11: reg_data_out = slv_reg17;
      5'h12: reg_data_out = slv_reg18;
      5'h13: reg_data_out = slv_reg19;
      5'h14: reg_data_out = slv_reg20;
      5'h15: reg_data_out = slv_reg21;
      5'h16: reg_data_out = slv_reg22;
      5'h17: reg_data_out = slv_reg23;
      5'h18: reg_data_out = slv_reg24;
      5'h19: reg_data_out = slv_reg25;
      5'h1A: reg_data_out = slv_reg26;
      5'h1B: reg_data_out = slv_reg27;
      5'h1C: reg_data_out = slv_reg28;
      5'h1D: reg_data_out = slv_reg29;
      5'h1E: reg_data_out = slv_reg30;
      5'h1F: reg_data_out = slv_reg31;
      default: reg_data_out = 0;
    endcase
  end


  always @(posedge S_AXI_ACLK) begin
    if(S_AXI_ARESETN == 1'b0) begin
      axi_rdata <= 0;
    end else begin
      if(slv_reg_rden) begin
        axi_rdata <= reg_data_out;
      end 
    end
  end


endmodule

