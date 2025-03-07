/*
 * Copyright 2013, Homer Hsing <homer.hsing@gmail.com>
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

`timescale 1ns / 1ps
`define P 20

module test_padder;

    // Inputs
    reg clk;
    reg instrumented_clk;
    reg reset;
    reg [31:0] in;
    reg in_ready;
    reg is_last;
    reg [1:0] byte_num;
    reg f_ack;

    // Outputs
    wire buffer_full;
    wire [575:0] out;
    wire out_ready;

    // Var
    integer i;

    integer f;

    // Instantiate the Unit Under Test (UUT)
    padder uut (
        .clk(clk),
        .reset(reset),
        .in(in),
        .in_ready(in_ready),
        .is_last(is_last),
        .byte_num(byte_num),
        .buffer_full(buffer_full),
        .out(out),
        .out_ready(out_ready),
        .f_ack(f_ack)
    );

`ifdef DUMP_TRACE // used for our OSDD calculations
initial begin
  $dumpfile("dump.vcd");
  $dumpvars(0, uut);
end
`endif // DUMP_TRACE

    initial begin
      f = $fopen("output_test_padder_t1.txt");
      $fwrite(f, "time,buffer_full,out[575],out[574],out[573],out[572],out[571],out[570],out[569],out[568],out[567],out[566],out[565],out[564],out[563],out[562],out[561],out[560],out[559],out[558],out[557],out[556],out[555],out[554],out[553],out[552],out[551],out[550],out[549],out[548],out[547],out[546],out[545],out[544],out[543],out[542],out[541],out[540],out[539],out[538],out[537],out[536],out[535],out[534],out[533],out[532],out[531],out[530],out[529],out[528],out[527],out[526],out[525],out[524],out[523],out[522],out[521],out[520],out[519],out[518],out[517],out[516],out[515],out[514],out[513],out[512],out[511],out[510],out[509],out[508],out[507],out[506],out[505],out[504],out[503],out[502],out[501],out[500],out[499],out[498],out[497],out[496],out[495],out[494],out[493],out[492],out[491],out[490],out[489],out[488],out[487],out[486],out[485],out[484],out[483],out[482],out[481],out[480],out[479],out[478],out[477],out[476],out[475],out[474],out[473],out[472],out[471],out[470],out[469],out[468],out[467],out[466],out[465],out[464],out[463],out[462],out[461],out[460],out[459],out[458],out[457],out[456],out[455],out[454],out[453],out[452],out[451],out[450],out[449],out[448],out[447],out[446],out[445],out[444],out[443],out[442],out[441],out[440],out[439],out[438],out[437],out[436],out[435],out[434],out[433],out[432],out[431],out[430],out[429],out[428],out[427],out[426],out[425],out[424],out[423],out[422],out[421],out[420],out[419],out[418],out[417],out[416],out[415],out[414],out[413],out[412],out[411],out[410],out[409],out[408],out[407],out[406],out[405],out[404],out[403],out[402],out[401],out[400],out[399],out[398],out[397],out[396],out[395],out[394],out[393],out[392],out[391],out[390],out[389],out[388],out[387],out[386],out[385],out[384],out[383],out[382],out[381],out[380],out[379],out[378],out[377],out[376],out[375],out[374],out[373],out[372],out[371],out[370],out[369],out[368],out[367],out[366],out[365],out[364],out[363],out[362],out[361],out[360],out[359],out[358],out[357],out[356],out[355],out[354],out[353],out[352],out[351],out[350],out[349],out[348],out[347],out[346],out[345],out[344],out[343],out[342],out[341],out[340],out[339],out[338],out[337],out[336],out[335],out[334],out[333],out[332],out[331],out[330],out[329],out[328],out[327],out[326],out[325],out[324],out[323],out[322],out[321],out[320],out[319],out[318],out[317],out[316],out[315],out[314],out[313],out[312],out[311],out[310],out[309],out[308],out[307],out[306],out[305],out[304],out[303],out[302],out[301],out[300],out[299],out[298],out[297],out[296],out[295],out[294],out[293],out[292],out[291],out[290],out[289],out[288],out[287],out[286],out[285],out[284],out[283],out[282],out[281],out[280],out[279],out[278],out[277],out[276],out[275],out[274],out[273],out[272],out[271],out[270],out[269],out[268],out[267],out[266],out[265],out[264],out[263],out[262],out[261],out[260],out[259],out[258],out[257],out[256],out[255],out[254],out[253],out[252],out[251],out[250],out[249],out[248],out[247],out[246],out[245],out[244],out[243],out[242],out[241],out[240],out[239],out[238],out[237],out[236],out[235],out[234],out[233],out[232],out[231],out[230],out[229],out[228],out[227],out[226],out[225],out[224],out[223],out[222],out[221],out[220],out[219],out[218],out[217],out[216],out[215],out[214],out[213],out[212],out[211],out[210],out[209],out[208],out[207],out[206],out[205],out[204],out[203],out[202],out[201],out[200],out[199],out[198],out[197],out[196],out[195],out[194],out[193],out[192],out[191],out[190],out[189],out[188],out[187],out[186],out[185],out[184],out[183],out[182],out[181],out[180],out[179],out[178],out[177],out[176],out[175],out[174],out[173],out[172],out[171],out[170],out[169],out[168],out[167],out[166],out[165],out[164],out[163],out[162],out[161],out[160],out[159],out[158],out[157],out[156],out[155],out[154],out[153],out[152],out[151],out[150],out[149],out[148],out[147],out[146],out[145],out[144],out[143],out[142],out[141],out[140],out[139],out[138],out[137],out[136],out[135],out[134],out[133],out[132],out[131],out[130],out[129],out[128],out[127],out[126],out[125],out[124],out[123],out[122],out[121],out[120],out[119],out[118],out[117],out[116],out[115],out[114],out[113],out[112],out[111],out[110],out[109],out[108],out[107],out[106],out[105],out[104],out[103],out[102],out[101],out[100],out[99],out[98],out[97],out[96],out[95],out[94],out[93],out[92],out[91],out[90],out[89],out[88],out[87],out[86],out[85],out[84],out[83],out[82],out[81],out[80],out[79],out[78],out[77],out[76],out[75],out[74],out[73],out[72],out[71],out[70],out[69],out[68],out[67],out[66],out[65],out[64],out[63],out[62],out[61],out[60],out[59],out[58],out[57],out[56],out[55],out[54],out[53],out[52],out[51],out[50],out[49],out[48],out[47],out[46],out[45],out[44],out[43],out[42],out[41],out[40],out[39],out[38],out[37],out[36],out[35],out[34],out[33],out[32],out[31],out[30],out[29],out[28],out[27],out[26],out[25],out[24],out[23],out[22],out[21],out[20],out[19],out[18],out[17],out[16],out[15],out[14],out[13],out[12],out[11],out[10],out[9],out[8],out[7],out[6],out[5],out[4],out[3],out[2],out[1],out[0],out_ready\n");
      forever begin
        @(posedge clk);
        $fwrite(f, "%g,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b,%b\n", $time,buffer_full,out[575],out[574],out[573],out[572],out[571],out[570],out[569],out[568],out[567],out[566],out[565],out[564],out[563],out[562],out[561],out[560],out[559],out[558],out[557],out[556],out[555],out[554],out[553],out[552],out[551],out[550],out[549],out[548],out[547],out[546],out[545],out[544],out[543],out[542],out[541],out[540],out[539],out[538],out[537],out[536],out[535],out[534],out[533],out[532],out[531],out[530],out[529],out[528],out[527],out[526],out[525],out[524],out[523],out[522],out[521],out[520],out[519],out[518],out[517],out[516],out[515],out[514],out[513],out[512],out[511],out[510],out[509],out[508],out[507],out[506],out[505],out[504],out[503],out[502],out[501],out[500],out[499],out[498],out[497],out[496],out[495],out[494],out[493],out[492],out[491],out[490],out[489],out[488],out[487],out[486],out[485],out[484],out[483],out[482],out[481],out[480],out[479],out[478],out[477],out[476],out[475],out[474],out[473],out[472],out[471],out[470],out[469],out[468],out[467],out[466],out[465],out[464],out[463],out[462],out[461],out[460],out[459],out[458],out[457],out[456],out[455],out[454],out[453],out[452],out[451],out[450],out[449],out[448],out[447],out[446],out[445],out[444],out[443],out[442],out[441],out[440],out[439],out[438],out[437],out[436],out[435],out[434],out[433],out[432],out[431],out[430],out[429],out[428],out[427],out[426],out[425],out[424],out[423],out[422],out[421],out[420],out[419],out[418],out[417],out[416],out[415],out[414],out[413],out[412],out[411],out[410],out[409],out[408],out[407],out[406],out[405],out[404],out[403],out[402],out[401],out[400],out[399],out[398],out[397],out[396],out[395],out[394],out[393],out[392],out[391],out[390],out[389],out[388],out[387],out[386],out[385],out[384],out[383],out[382],out[381],out[380],out[379],out[378],out[377],out[376],out[375],out[374],out[373],out[372],out[371],out[370],out[369],out[368],out[367],out[366],out[365],out[364],out[363],out[362],out[361],out[360],out[359],out[358],out[357],out[356],out[355],out[354],out[353],out[352],out[351],out[350],out[349],out[348],out[347],out[346],out[345],out[344],out[343],out[342],out[341],out[340],out[339],out[338],out[337],out[336],out[335],out[334],out[333],out[332],out[331],out[330],out[329],out[328],out[327],out[326],out[325],out[324],out[323],out[322],out[321],out[320],out[319],out[318],out[317],out[316],out[315],out[314],out[313],out[312],out[311],out[310],out[309],out[308],out[307],out[306],out[305],out[304],out[303],out[302],out[301],out[300],out[299],out[298],out[297],out[296],out[295],out[294],out[293],out[292],out[291],out[290],out[289],out[288],out[287],out[286],out[285],out[284],out[283],out[282],out[281],out[280],out[279],out[278],out[277],out[276],out[275],out[274],out[273],out[272],out[271],out[270],out[269],out[268],out[267],out[266],out[265],out[264],out[263],out[262],out[261],out[260],out[259],out[258],out[257],out[256],out[255],out[254],out[253],out[252],out[251],out[250],out[249],out[248],out[247],out[246],out[245],out[244],out[243],out[242],out[241],out[240],out[239],out[238],out[237],out[236],out[235],out[234],out[233],out[232],out[231],out[230],out[229],out[228],out[227],out[226],out[225],out[224],out[223],out[222],out[221],out[220],out[219],out[218],out[217],out[216],out[215],out[214],out[213],out[212],out[211],out[210],out[209],out[208],out[207],out[206],out[205],out[204],out[203],out[202],out[201],out[200],out[199],out[198],out[197],out[196],out[195],out[194],out[193],out[192],out[191],out[190],out[189],out[188],out[187],out[186],out[185],out[184],out[183],out[182],out[181],out[180],out[179],out[178],out[177],out[176],out[175],out[174],out[173],out[172],out[171],out[170],out[169],out[168],out[167],out[166],out[165],out[164],out[163],out[162],out[161],out[160],out[159],out[158],out[157],out[156],out[155],out[154],out[153],out[152],out[151],out[150],out[149],out[148],out[147],out[146],out[145],out[144],out[143],out[142],out[141],out[140],out[139],out[138],out[137],out[136],out[135],out[134],out[133],out[132],out[131],out[130],out[129],out[128],out[127],out[126],out[125],out[124],out[123],out[122],out[121],out[120],out[119],out[118],out[117],out[116],out[115],out[114],out[113],out[112],out[111],out[110],out[109],out[108],out[107],out[106],out[105],out[104],out[103],out[102],out[101],out[100],out[99],out[98],out[97],out[96],out[95],out[94],out[93],out[92],out[91],out[90],out[89],out[88],out[87],out[86],out[85],out[84],out[83],out[82],out[81],out[80],out[79],out[78],out[77],out[76],out[75],out[74],out[73],out[72],out[71],out[70],out[69],out[68],out[67],out[66],out[65],out[64],out[63],out[62],out[61],out[60],out[59],out[58],out[57],out[56],out[55],out[54],out[53],out[52],out[51],out[50],out[49],out[48],out[47],out[46],out[45],out[44],out[43],out[42],out[41],out[40],out[39],out[38],out[37],out[36],out[35],out[34],out[33],out[32],out[31],out[30],out[29],out[28],out[27],out[26],out[25],out[24],out[23],out[22],out[21],out[20],out[19],out[18],out[17],out[16],out[15],out[14],out[13],out[12],out[11],out[10],out[9],out[8],out[7],out[6],out[5],out[4],out[3],out[2],out[1],out[0],out_ready);
      end
    end

    initial begin
        // Initialize Inputs
        clk = 0;
        instrumented_clk = 0;
        reset = 1;
        in = 0;
        in_ready = 0;
        is_last = 0;
        byte_num = 0;
        f_ack = 0;

        // Wait 100 ns for global reset to finish
        #100;

        // Add stimulus here
        @ (negedge clk);

        // pad an empty string, should not eat next input
        reset = 1; #(`P); reset = 0;
        #(7*`P); // wait some cycles
        if (buffer_full !== 0) error;
        in_ready = 1;
        is_last = 1;
        #(`P);
        in_ready = 1; // next input
        is_last = 1;
        #(`P);
        in_ready = 0;
        is_last = 0;

        while (out_ready !== 1)
            #(`P);
        check({8'h1, 560'h0, 8'h80});
        f_ack = 1; #(`P); f_ack = 0;
        for(i=0; i<5; i=i+1)
          begin
            #(`P);
            if (buffer_full !== 0) error; // should be 0
          end

        // pad an (576-8) bit string
        reset = 1; #(`P); reset = 0;
        #(4*`P); // wait some cycles
        in_ready = 1; is_last = 0;
        byte_num = 3; /* should have no effect */
        for (i=0; i<8; i=i+1)
          begin
            in = 32'h12345678; #(`P);
            in = 32'h90ABCDEF; #(`P);
          end
        in = 32'h12345678; #(`P);
        in = 32'h90ABCDEF; is_last = 1; #(`P);
        in_ready = 0;
        is_last = 0;
        check({ {8{64'h1234567890ABCDEF}}, 64'h1234567890ABCD81 });

        // pad an (576-64) bit string
        reset = 1; #(`P); reset = 0;
        // don't wait any cycle
        in_ready = 1; is_last = 0;
        byte_num = 1; /* should have no effect */
        for (i=0; i<8; i=i+1)
          begin
            in = 32'h12345678; #(`P);
            in = 32'h90ABCDEF; #(`P);
          end
        is_last = 1;
        byte_num = 0;
        #(`P);
        in_ready = 0;
        is_last = 0;
        #(`P);
        check({ {8{64'h1234567890ABCDEF}}, 64'h0100000000000080 });

        // pad an (576*2-16) bit string
        reset = 1; #(`P); reset = 0;
        in_ready = 1;
        byte_num = 7; /* should have no effect */
        is_last = 0;
        for (i=0; i<9; i=i+1)
          begin
            in = 32'h12345678; #(`P);
            in = 32'h90ABCDEF; #(`P);
          end
        if (out_ready !== 1) error;
        check({9{64'h1234567890ABCDEF}});
        #(`P/2);
        if (buffer_full !== 1) error; // should not eat
        #(`P/2);
        in = 64'h999; // should not eat this
        #(`P/2);
        if (buffer_full !== 1) error; // should not eat
        #(`P/2);
        f_ack = 1; #(`P); f_ack = 0;
        if (out_ready !== 0) error;
        // feed next (576-16) bit
        for (i=0; i<8; i=i+1)
          begin
            in = 32'h12345678; #(`P);
            in = 32'h90ABCDEF; #(`P);
          end
        in = 32'h12345678; #(`P);
        byte_num = 2;
        is_last = 1;
        in = 32'h90ABCDEF; #(`P);
        if (out_ready !== 1) error;
        check({ {8{64'h1234567890ABCDEF}}, 64'h1234567890AB0180 });
        is_last = 0;
        // eat these bits
        f_ack = 1; #(`P); f_ack = 0;
        // should not provide any more bits, if user provides nothing
        in_ready = 0;
        is_last = 0;
        for (i=0; i<10; i=i+1)
          begin
            if (out_ready === 1) error;
            #(`P);
          end
        in_ready = 0;

        $display("Good!");
        $finish;
    end

    always #(`P/2) clk = ~ clk;
    always #(`P*2) instrumented_clk = ~ instrumented_clk;

    task error;
        begin
              $display("E");
              $finish;
        end
    endtask

    task check;
        input [575:0] wish;
        begin
          if (out !== wish)
            begin
              $display("out:%h wish:%h", out, wish);
              error;
            end
        end
    endtask
endmodule

`undef P
