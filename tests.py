print("-- for loop range...")
for i in range(10):
    print(i)

print("-- f string...")
print(f">>{i:33.4f} + {5*839} {5} {i}")

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

print("-- comprehension list...")
lst = [i for i in range(100)]
print(lst)

print("-- comprehension set...")
st = {i for i in range(100)}
print(st)

print("-- comprehension dict...")
dtc = {i: i for i in range(100)}
print(dtc)

# print("-- comprehension tuple...")
# tpl = tuple(i for i in range(100))
# print(tpl)


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

print("-- import ...")
import datetime

print(datetime.datetime.now())

print("-- from X import ...")
from datetime import datetime as renamed

print(renamed.now())
