f1 = open('orig_tb.csv', 'r')
lines1 = f1.readlines()
f2 = open('output_sdram_controller_tb_t1.csv', 'r')
lines2 = f2.readlines()

for i, line in enumerate(lines2):
    a1 = lines1[i].split(',')
    a2 = lines2[i].split(',')
    for j in range(len(a1)):
        if a1[j].strip() != a2[j].strip():
            print(f'line = {i}, col = {j}')
