import os 

def test_bot(iterations):
    output = []
    wins = 0
    for i in range(iterations):
        os.system("python3 engine.py")
        with open('gamelog.txt', 'rb') as f:
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
            last_line = f.readline().decode()
        output.append(last_line)

    for line in output:
        s1 = line.find('(')
        s2 = line.find(')')
        hero = int(line[s1+1:s2])
        temp = line[s2+1:]
        v1 = temp.find('(')
        v2 = temp.find(')')
        villian = int(temp[v1+1:v2])
        if hero > villian: wins += 1

    return output, wins, float(wins)/iterations


if __name__ == "__main__":

    print(test_bot(1))

        

