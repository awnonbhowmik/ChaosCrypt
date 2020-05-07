import time


def numdigit(n):
    count = 0
    while n > 0:
        n = n//10
        count += 1

    return count


while True:
    seed = int(input("Enter four-digit starting seed:"))
    if numdigit(seed) == 4:
        break
    else:
        print("Four digit starting seed required!\n")


number = seed
lst = []

print("Optional parameters", end="")
for i in range(3):
    print(".", end="")
    time.sleep(1)

print("\n\nUsing Linear Congruential Generator as a safety net,\nso that the sequence doesn't converge to zero")
print("\nEquation: X(n+1) = (a x(n) + b) mod m")

a = int(input("Enter a:"))
while True:
    b = int(input("Enter b:"))
    if b==0:
        print("b has to be non-zero to increase chances of sequence converging to 0.\n")
    elif b<0:
        print("try using positive integers for b.\n")
    else:
        break

while True:
    m = int(input("Enter modulo m (preferably large positive integer):"))
    if m > 2**12-1:
        break
    print("Increased risk of compromising secure info. Try again!\n")


while number not in lst:
    lst.append(number)
    # Consider a string length of 8.
    # Fills the string with zeros from left
    # From position [0,1,2,3,4,5,6,7,8], choose from 2 to 5
    # That gives the new 4 digit number
    number = int(str(number*number).zfill(8)[2:6])

    if number == 0:
        number = (a*number+b) % m

    print(number)

print("\nLength of sequence:", len(lst))