import subprocess


def prime_factors(n):
    i = 2
    factors = []
    while i * i <= n:
        if n % i:
            i += 1
        else:
            n //= i
            factors.append(i)
    if n > 1:
        factors.append(n)
    return factors


# for i in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]:
# for i in [509728320]:
for i in [5 * 7, 11 * 13]:
    inp = i.to_bytes(4, "little") + b"\n"
    x = subprocess.check_output(
        [
            "gdb",
            "--batch",
            "--command=batch.gdb",
            "one",
        ],
        input=inp,
    )

    line = x.splitlines()[-1]
    prime = int(line)
    print(prime)
    if prime:
        print(prime_factors(prime))
