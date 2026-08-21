with open('.env','rb') as f:
    data=f.read()
print('BYTES_LEN', len(data))
for i,line in enumerate(data.splitlines()):
    print(i, repr(line))
