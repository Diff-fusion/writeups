#!/usr/bin/python3

import subprocess
import string
import itertools


def run(payload):
    return subprocess.run(("strace", "./one"), stdout=subprocess.PIPE, stderr=subprocess.PIPE, input=payload)


def foo():
    counts = {}
    # for c in range(256):
    for c in string.printable:
        print(f"{c:3}", end=": ")
        for i in range(1, 2):
            # payload = bytes((c,)) * i
            payload = b"yfc3" + c.encode() * i
            # payload = c.encode() * i
            payload += b"\n"
            x = run(payload)

            # print(x.stdout)
            # print(x.stderr.decode())
            count = x.stderr.count(b"--- SIGILL")
            print(f"{count:5}", end=" ")
            num = counts.get(count, 0)
            counts[count] = num + 1
        print()

    # print("counts:")
    # for k, v in counts.items():
    #     print(f"{k:3}, {v:2}")


def brute():
    for (a, b, c, d) in itertools.product(string.printable, repeat=4):
        # print(a, b, c, d)
        payload = a + b + c + d
        payload = payload.encode()
        x = run(payload)
        count = x.stderr.count(b"--- SIGILL")
        print(f"{count:5}")


brute()
