# RTL-Repair

## Cirfix

### sha3_keccak_round_ssscrazy_buggy1_oracle-full

- Human

```diff
-   assign update = (accept | state) & ~done;
---
+   assign update = (accept | state & ~buffer_full) & ~done;
```

- RTL-Repair

```diff
34c34
-   assign update = (accept | state) & ~done;
---
+   assign update = (accept | state) & ~done & !f_ack;
```

### sdram_controller_wadden_buggy2_oracle-full

- Human

```diff
-   localparam READ_ACT = 5'b10000;localparam READ_NOP1 = 5'b10000;localparam READ_CAS = 5'b10010;localparam READ_NOP2 = 5'b10011;localparam READ_READ = 5'b10100;
---
+   localparam READ_ACT = 5'b10000;localparam READ_NOP1 = 5'b10001;localparam READ_CAS = 5'b10010;localparam READ_NOP2 = 5'b10011;localparam READ_READ = 5'b10100;

```

- RTL-Repair

```diff
210c210
-         next = READ_NOP1;
---
+         next = 5'b11101;
213c213
-       READ_NOP1: begin
---
+       5'b11101: begin
```
