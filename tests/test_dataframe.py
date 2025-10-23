# test_dataframe.py
import pytest

from keecas.dataframe import Dataframe, create_dataframe


def test_init_with_list_of_dicts():
    """Test initialization from list of dictionaries creates columns correctly"""
    data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    df = Dataframe(data)
    assert df["a"] == [1, 3]
    assert df["b"] == [2, 4]
    assert df.width == 2
    assert df.length == 2
    assert df.shape == (2, 2)


def test_init_with_dict():
    """Test initialization from dictionary with list values"""
    data = {"a": [1, 2], "b": [3, 4]}
    df = Dataframe(data)
    assert df["a"] == [1, 2]
    assert df["b"] == [3, 4]
    assert df.width == 2
    assert df.length == 2
    assert df.shape == (2, 2)


def test_update():
    """Test updating dataframe extends width and fills missing values"""
    df = Dataframe({"a": [1, 2]})
    df.update({"b": [3, 4, 5]})
    assert df["a"] == [1, 2, None]
    assert df["b"] == [3, 4, 5]
    assert df.width == 3
    assert df.length == 2
    assert df.shape == (2, 3)


def test_append():
    """Test appending single row to existing dataframe"""
    df = Dataframe({"a": [1, 2], "b": [3, 4]})
    df.append({"a": 5, "b": 6})
    assert df["a"] == [1, 2, 5]
    assert df["b"] == [3, 4, 6]
    assert df.width == 3
    assert df.length == 2
    assert df.shape == (2, 3)


def test_extend_with_dict():
    """Test extending dataframe with dictionary in strict mode (ignores extra keys)"""
    df = Dataframe({"a": [1, 2], "b": [3, 4]})
    df.extend({"a": [5, 6], "b": [7, 8], "c": [9, 10, 11]})
    assert df["a"] == [1, 2, 5, 6]
    assert df["b"] == [3, 4, 7, 8]
    with pytest.raises(KeyError):
        _ = df["c"]
    assert df.width == 4
    assert df.length == 2
    assert df.shape == (2, 4)


def test_add_operator():
    """Test + operator extends one dataframe with another"""
    df1 = Dataframe({"a": [1, 2], "b": [3, 4]})
    df2 = Dataframe({"a": [5, 6], "b": [7, 8]})
    df3 = df1 + df2
    assert df3["a"] == [1, 2, 5, 6]
    assert df3["b"] == [3, 4, 7, 8]
    assert df3.width == 4
    assert df3.length == 2
    assert df3.shape == (2, 4)


def test_or_operator():
    """Test | operator merges dataframes (like dict merge)"""
    df1 = Dataframe({"a": [1, 2], "b": [3, 4]})
    df2 = Dataframe({"b": [7, 8], "c": [9, 10]})
    df3 = df1 | df2
    assert df3["a"] == [1, 2]
    assert df3["b"] == [7, 8]
    assert df3["c"] == [9, 10]
    assert df3.width == 2
    assert df3.length == 3
    assert df3.shape == (3, 2)

def test_or_operator_with_unequal_width():
    """Test | operator merges dataframes with unequal width (like dict merge)"""
    df1 = Dataframe({"a": [1, 2], "b": [3, 4]})
    df2 = Dataframe({"b": [7], "c": [9]})
    df3 = df1 | df2
    assert df3["a"] == [1, 2]
    assert df3["b"] == [7, None]
    assert df3["c"] == [9, None]
    assert df3.width == 2
    assert df3.length == 3
    assert df3.shape == (3, 2)


def test_create_dataframe():
    """Test create_dataframe utility function with scalar seed"""
    keys = ["a", "b"]
    width = 3
    df = create_dataframe(keys, width, seed=0, default_value=-1)
    assert df["a"] == [0, 0, 0]
    assert df["b"] == [0, 0, 0]
    assert df.width == 3
    assert df.length == 2
    assert df.shape == (2, 3)


def test_create_dataframe_with_list_seed():
    """Test create_dataframe utility function with list seed"""
    keys = ["a", "b"]
    width = 3
    seed = [1, 2]
    df = create_dataframe(keys, width, seed=seed, default_value=-1)
    assert df["a"] == [1, 2, -1]
    assert df["b"] == [1, 2, -1]
    assert df.width == 3
    assert df.length == 2
    assert df.shape == (2, 3)


def test_create_dataframe_with_dataframe_seed():
    """Test create_dataframe utility function with Dataframe seed"""
    keys = ["a", "b"]
    width = 3
    seed_df = Dataframe({"a": [1, 2], "b": [3, 4]})
    df = create_dataframe(keys, width, seed=seed_df, default_value=-1)
    assert df["a"] == [1, 2, -1]
    assert df["b"] == [3, 4, -1]
    assert df.width == 3
    assert df.length == 2
    assert df.shape == (2, 3)


def test_create_dataframe_with_dict_seed():
    """Test create_dataframe utility function with dict seed (mixed list/scalar values)"""
    keys = ["a", "b"]
    width = 3
    seed = {"a": [1, 2], "b": 3}
    df = create_dataframe(keys, width, seed=seed, default_value=-1)
    assert df["a"] == [1, 2, -1]
    assert df["b"] == [3, 3, 3]
    assert df.width == 3
    assert df.length == 2
    assert df.shape == (2, 3)


def test_properties():
    """Test dataframe shape properties (width, length, shape)"""
    df = Dataframe({"a": [1, 2, 3], "b": [4, 5, 6]})
    assert df.width == 3
    assert df.length == 2
    assert df.shape == (2, 3)


def test_extend_with_strict():
    """Test extend behavior with strict=True vs strict=False"""
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


# Edge case tests
def test_init_with_empty_list_of_dicts():
    """Test initialization with empty list should create empty Dataframe"""
    df = Dataframe([])
    assert len(df) == 0
    assert df.width == 0
    assert df.shape == (0, 0)


def test_init_with_inconsistent_dict_keys():
    """Test initialization with dicts having different keys"""
    data = [{"a": 1, "b": 2}, {"a": 3, "c": 4}, {"b": 5}]
    df = Dataframe(data)
    # Should use keys from first dict only
    assert "a" in df
    assert "b" in df
    assert "c" not in df
    assert df["a"] == [1, 3, None]  # missing key gets filler (None)
    assert df["b"] == [2, None, 5]  # missing key gets filler (None)
    assert df.width == 3
    assert df.length == 2
    assert df.shape == (2, 3)


def test_operations_on_empty_dataframe():
    """Test various operations on empty Dataframe"""
    df = Dataframe()

    # Test update on empty (this should work)
    df.update({"a": [1], "b": [2]})
    assert df["a"] == [1]
    assert df["b"] == [2]
    assert df.width == 1
    assert df.length == 2
    assert df.shape == (2, 1)

    # Test append to empty doesn't work (no existing keys)
    df_empty = Dataframe()
    df_empty.append({"a": 1, "b": 2})  # Should do nothing since no existing keys
    assert len(df_empty) == 0
    assert df_empty.width == 0
    assert df_empty.length == 0
    assert df_empty.shape == (0, 0)

    # Test extend on empty
    df_empty2 = Dataframe()
    df_empty2.extend({"x": [1, 2], "y": [3, 4]}, strict=False)
    assert df_empty2["x"] == [1, 2]
    assert df_empty2["y"] == [3, 4]
    assert df_empty2.width == 2
    assert df_empty2.length == 2
    assert df_empty2.shape == (2, 2)


def test_invalid_input_types():
    """Test error handling for invalid input types"""
    df = Dataframe({"a": [1, 2], "b": [3, 4]})

    # Test extend with invalid type
    with pytest.raises(ValueError, match="Cannot extend Dataframe with this type"):
        df.extend("invalid_string")

    # Test update with too many arguments
    with pytest.raises(TypeError, match="update expected at most 1 arguments"):
        df.update({"a": [1]}, {"b": [2]})

    # Test initialization with too many arguments (for dict-style init)
    with pytest.raises(TypeError, match="update expected at most 1 arguments"):
        Dataframe({"a": [1]}, {"b": [2]})
