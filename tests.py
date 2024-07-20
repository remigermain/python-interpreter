print("-- for loop range...")
for i in range(10):
    print(i)

print("-- operator...")
a = b = c = 1
print(a, b, c)

a += b
print(a)

b -= c * 4449
print(b)

c //= 3
print(c)

c = a**5 % 3 - 1 & 4 | 6 - 6**888
print(c)


print("-- iterator definition...")


def iterator(nb):
    for i in range(nb):
        yield i**nb


for v in iterator(10):
    print("[yield value] " + str(v))


print("-- unpack sequences...")

a, b = ["first", "seconde"]
print(a, b)

print("-- attr call...")
print(a.upper())
