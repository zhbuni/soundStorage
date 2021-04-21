import string
import random


def generate_random_string(n):
    chrs = string.ascii_letters + string.digits
    return ''.join([random.choice(chrs) for _ in range(n)])
