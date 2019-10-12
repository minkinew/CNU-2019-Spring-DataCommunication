import random
import numpy as np
import pandas as pd
from hamming_practice import hamming

df = pd.read_csv('sample.csv', names=['word', 'bin'])

count = 1
min = hamming(df.iloc[0,1], df.iloc[1,1])
leng = len(df)

for i in range(0, leng):
    for j in range(0, leng):
        if i < j:
            hd = hamming(df.iloc[i,1], df.iloc[j,1])
            print(count, "(", df.iloc[i,0],df.iloc[j,0],") hamming_distance : ", hd);
            if min > hd:
                min = hd
            count = count+1
print("min hamming distance", min)

