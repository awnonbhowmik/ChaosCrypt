#Chinese remainder theorem
from functools import reduce
"""Considering the system of linear congruence of the form
x = a1 mod m1
x = a2 mod m2
x = a3 mod m3
.   .      .
.   .      .
.   .      .
.   .      .
.   .      .
x = an mod mn
"""


def multiplicative_inverse(a, m):
    for x in range(1, m):
        if a * x % m == 1:
            return x
        return -1


def crt(a, m):
    sum = 0
    prod = reduce(lambda a, b: a * b, m)
    for m_i, a_i in zip(m, a):
        p = prod / m_i
        sum += a_i * multiplicative_inverse(p, m_i) * p
    return (sum % prod, prod)


if __name__ == '__main__':
    num = int(input("Enter number of equations: "))

    a = []
    m = []

    for i in range(num):
        c, d = [
            int(x) for x in input("Given x = a mod m, enter (a,m): ").split()
        ]

        a.append(c)
        m.append(d)

sol, mod = crt(a,m)
print("Solution: {} mod {}".format(int(sol),mod))
