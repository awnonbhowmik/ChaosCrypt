from time import time_ns
import math
from matplotlib import pyplot as plt
import numpy as np


def num_digit(n):
    count = 0
    while n > 0:
        n = n // 10
        count += 1

    return count


"""
print(2**32)
print(len(str(2**32)))

"""

if __name__=='__main__':
    loop = []
    log = []
    string = []
    result = []
    print("Using loop\tUsing log\tUsing string\tFastest")
    for i in range(1, 33):
        t1 = time_ns()
        num_digit(2**i)
        t2 = time_ns()
        loop.append(t2 - t1)
        print(t2 - t1, end="\t\t")

        t3 = time_ns()
        digits = int(math.log10(2**i)) + 1
        t4 = time_ns()
        log.append(t4 - t3)
        print(t4 - t3, end="\t\t")

        t5 = time_ns()
        count = len(str(2**i))
        t6 = time_ns()
        string.append(t6 - t5)
        print(t6 - t5, end="\t\t\t")

        pair = {"loop": t2 - t1, "log": t4 - t3, "string": t6 - t5}

        a = min(pair, key=pair.get)
        result.append(a)
        print(a)

    print("P(loop) = {}/32\tP(log) = {}/32\tP(string) = {}/32".format(result.count('loop'),result.count('log'),result.count('string')))


    x = np.arange(32)  # the label locations
    width = 0.25  # the width of the bars

    fig, ax = plt.subplots()
    # Set position of bar on X axis
    r1 = np.arange(32)
    r2 = [x + width for x in r1]
    r3 = [x + width for x in r2]

    # Make the plot
    plt.bar(r1, loop, color='red', width=width, edgecolor='white', label='Using loops')
    plt.bar(r2, log, color='blue', width=width, edgecolor='white', label='Using log')
    plt.bar(r3,string,color='green',width=width,edgecolor='white',label='Using string')

    plt.legend()
    plt.show()