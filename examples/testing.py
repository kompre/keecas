from keecas import Dataframe
from sympy import Dict


a = {
    'a': 1,
    'b': 2,
    'c': 3,
    'd': 4
}

b = {
    'a': 11,
    'b': 22,
    'c': 33,
    'd': 44
}

df = Dataframe([a, b])

print(
    df
)

print(f'{df.width=}')
print(f'{df.length=}')
print(f'{df.shape=}')
