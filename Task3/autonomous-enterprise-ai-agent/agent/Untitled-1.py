
def karatsuba(x, y):

    if x < 10 or y < 10:
        return x * y

    n = max(len(str(x)), len(str(y)))
    m = n // 2

    power = 10 ** m
    a = x // power
    b = x % power

    c = y // power
    d = y % power

    z0 = karatsuba(b, d)
    z2 = karatsuba(a, c)

    z1 = karatsuba(a + b, c + d) - z2 - z0

    return z2 * (10 ** (2 * m)) + z1 * power + z0


x = 1234
y = 5678

result = karatsuba(x, y)

print("First Number:", x)
print("Second Number:", y)
print("Multiplication Result:", result)
