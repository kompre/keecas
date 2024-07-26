# test_dataframe.py
import pytest
from keecas.dataframe import Dataframe, create_dataframe


def test_init_with_list_of_dicts():
    data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    df = Dataframe(data)
    assert df["a"] == [1, 3]
    assert df["b"] == [2, 4]
    assert df.width == 2


def test_init_with_dict():
    data = {"a": [1, 2], "b": [3, 4]}
    df = Dataframe(data)
    assert df["a"] == [1, 2]
    assert df["b"] == [3, 4]
    assert df.width == 2


def test_update():
    df = Dataframe({"a": [1, 2]})
    df.update({"b": [3, 4, 5]})
    assert df["a"] == [1, 2, None]
    assert df["b"] == [3, 4, 5]
    assert df.width == 3


def test_append():
    df = Dataframe({"a": [1, 2], "b": [3, 4]})
    df.append({"a": 5, "b": 6})
    assert df["a"] == [1, 2, 5]
    assert df["b"] == [3, 4, 6]
    assert df.width == 3


def test_extend_with_dict():
    df = Dataframe({"a": [1, 2], "b": [3, 4]})
    df.extend({"a": [5, 6], "b": [7, 8], "c": [9, 10, 11]})
    assert df["a"] == [1, 2, 5, 6]
    assert df["b"] == [3, 4, 7, 8]
    with pytest.raises(KeyError):
        _ = df["c"]
    assert df.width == 4


def test_add_operator():
    df1 = Dataframe({"a": [1, 2], "b": [3, 4]})
    df2 = Dataframe({"a": [5, 6], "b": [7, 8]})
    df3 = df1 + df2
    assert df3["a"] == [1, 2, 5, 6]
    assert df3["b"] == [3, 4, 7, 8]
    assert df3.width == 4


def test_or_operator():
    df1 = Dataframe({"a": [1, 2], "b": [3, 4]})
    df2 = Dataframe({"b": [7, 8], "c": [9, 10]})
    df3 = df1 | df2
    assert df3["a"] == [1, 2]
    assert df3["b"] == [7, 8]
    assert df3["c"] == [9, 10]
    assert df3.width == 2


def test_create_dataframe():
    keys = ["a", "b"]
    width = 3
    df = create_dataframe(keys, width, seed=0, default_value=-1)
    assert df["a"] == [0, 0, 0]
    assert df["b"] == [0, 0, 0]


def test_create_dataframe_with_list_seed():
    keys = ["a", "b"]
    width = 3
    seed = [1, 2]
    df = create_dataframe(keys, width, seed=seed, default_value=-1)
    assert df["a"] == [1, 2, -1]
    assert df["b"] == [1, 2, -1]


def test_create_dataframe_with_dataframe_seed():
    keys = ["a", "b"]
    width = 3
    seed_df = Dataframe({"a": [1, 2], "b": [3, 4]})
    df = create_dataframe(keys, width, seed=seed_df, default_value=-1)
    assert df["a"] == [1, 2, -1]
    assert df["b"] == [3, 4, -1]


def test_create_dataframe_with_dict_seed():
    keys = ["a", "b"]
    width = 3
    seed = {"a": [1, 2], "b": 3}
    df = create_dataframe(keys, width, seed=seed, default_value=-1)
    assert df["a"] == [1, 2, -1]
    assert df["b"] == [3, 3, 3]


def test_properties():
    df = Dataframe({"a": [1, 2, 3], "b": [4, 5, 6]})
    assert df.width == 3
    assert df.length == 2
    assert df.shape == (2, 3)


def test_extend_with_strict():
    df1 = Dataframe({"a": [1, 2], "b": [3, 4]})
    df2 = Dataframe({"c": [4, 5, 6]})
    df1.extend(df2, strict=True)
    assert df1["a"] == [1, 2]
    assert df1["b"] == [3, 4]
    assert df1.shape == (2, 2)
    df1.extend(df2, strict=False)
    assert df1["a"] == [1, 2, None, None, None]
    assert df1["b"] == [3, 4, None, None, None]
    assert df1["c"] == [None, None, 4, 5, 6]
    assert df1.shape == (3, 5)
