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

df1 = Dataframe({"a": [1, 2], "b": [3, 4]})
df2 = Dataframe({"b": [7], "c": [9]})
df3 = df1 | df2
print(df3)


print(Dataframe([]))

