import numpy as np
from random import randint

def cantor_pair(k1, k2, safe=True):
    z = int(0.5 * (k1 + k2) * (k1 + k2 + 1) + k2)
    if safe and (k1, k2) != cantor_unpair(z):
        raise ValueError("{} and {} cannot be paired".format(k1, k2))
    return z


def cantor_unpair(z):
    w = np.floor((np.sqrt(8 * z + 1) - 1) / 2)
    t = (w**2 + w) / 2
    y = int(z - t)
    x = int(w - y)
    # assert z != pair(x, y, safe=False):
    return (x, y)

lst = []
n=int(input("Initial list:"))

for i in range(n):
    x=randint(0,100)
    if x not in lst:
        lst.append(x)

print(lst)

for i in range(len(lst)):
    for j in range(len(lst)-1):
        y=cantor_pair(lst[j],lst[j+1])
        print(y,end = " ")