import unittest
from dataframe import Dataframe, create_dataframe

class TestDataframe(unittest.TestCase):
    # Initialization Tests
    def test_initialization_with_list_of_dicts(self):
        data = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]
        df = Dataframe(data)
        self.assertEqual(df['a'], [1, 3])
        self.assertEqual(df['b'], [2, 4])

    def test_initialization_with_kwargs(self):
        df = Dataframe(a=[1, 2], b=[3, 4])
        self.assertEqual(df['a'], [1, 2])
        self.assertEqual(df['b'], [3, 4])

    def test_initialization_with_args_and_kwargs(self):
        df = Dataframe({'a': [1, 2]}, b=[3, 4])
        self.assertEqual(df['a'], [1, 2])
        self.assertEqual(df['b'], [3, 4])

    def test_initialization_empty(self):
        df = Dataframe()
        self.assertEqual(df.width, 0)
        self.assertEqual(df.length, 0)

    # Update Tests
    def test_update_with_dict(self):
        df = Dataframe(a=[1, 2])
        df.update({'b': [3, 4]})
        self.assertEqual(df['a'], [1, 2])
        self.assertEqual(df['b'], [3, 4])

    def test_update_with_kwargs(self):
        df = Dataframe(a=[1, 2])
        df.update(b=[3, 4])
        self.assertEqual(df['a'], [1, 2])
        self.assertEqual(df['b'], [3, 4])

    # Append Tests
    def test_append_dataframe(self):
        df1 = Dataframe(a=[1, 2], b=[3, 4])
        df2 = Dataframe(a=[5], b=[6])
        df1.append(df2)
        self.assertEqual(df1['a'], [1, 2, 5])
        self.assertEqual(df1['b'], [3, 4, 6])

    def test_append_dict(self):
        df = Dataframe(a=[1, 2], b=[3, 4])
        df.append({'a': 5, 'b': 6})
        self.assertEqual(df['a'], [1, 2, 5])
        self.assertEqual(df['b'], [3, 4, 6])

    def test_append_value(self):
        df = Dataframe(a=[1, 2], b=[3, 4])
        df.append(5)
        self.assertEqual(df['a'], [1, 2, 5])
        self.assertEqual(df['b'], [3, 4, 5])

    # Extend Tests
    def test_extend_dataframe(self):
        df1 = Dataframe(a=[1, 2], b=[3, 4])
        df2 = Dataframe(a=[5, 6], b=[7, 8])
        df1.extend(df2)
        self.assertEqual(df1['a'], [1, 2, 5, 6])
        self.assertEqual(df1['b'], [3, 4, 7, 8])

    def test_extend_dict(self):
        df = Dataframe(a=[1, 2], b=[3, 4])
        df.extend({'a': [5, 6], 'b': [7, 8]})
        self.assertEqual(df['a'], [1, 2, 5, 6])
        self.assertEqual(df['b'], [3, 4, 7, 8])

    def test_extend_list(self):
        df = Dataframe(a=[1, 2], b=[3, 4])
        df.extend([5, 6])
        self.assertEqual(df['a'], [1, 2, 5, 6])
        self.assertEqual(df['b'], [3, 4, 5, 6])

    def test_extend_with_longer_lists(self):
        df = Dataframe(a=[1, 2], b=[3, 4])
        df.extend({'a': [5, 6, 7, 8], 'b': [9, 10]})
        self.assertEqual(df['a'], [1, 2, 5, 6, 7, 8])
        self.assertEqual(df['b'], [3, 4, 9, 10, None, None])

    def test_extend_with_missing_values(self):
        df = Dataframe(a=[1, 2], b=[3, 4])
        df.extend({'a': [5, 6], 'c': [7, 8]}, strict=False)
        self.assertEqual(df['a'], [1, 2, 5, 6])
        self.assertEqual(df['b'], [3, 4, None, None])
        self.assertEqual(df['c'], [None, None, 7, 8])

    # Operator Tests
    def test_add_operator(self):
        df1 = Dataframe(a=[1, 2], b=[3, 4])
        df2 = Dataframe(a=[5, 6], c=[7, 8])
        df3 = df1 + df2
        self.assertEqual(df3['a'], [1, 2, 5, 6])
        self.assertEqual(df3['b'], [3, 4, None, None])
        self.assertEqual(df3['c'], [None, None, 7, 8])

    # Property Tests
    def test_width_property(self):
        df = Dataframe(a=[1, 2], b=[3, 4, 5])
        self.assertEqual(df.width, 3)

    def test_length_property(self):
        df = Dataframe(a=[1, 2], b=[3, 4])
        self.assertEqual(df.length, 2)

    def test_shape_property(self):
        df = Dataframe(a=[1, 2], b=[3, 4, 5])
        self.assertEqual(df.shape, (2, 3))

    # Function Tests
    def test_create_dataframe_single_value_seed(self):
        df = create_dataframe(['a', 'b'], 3, seed=1)
        self.assertEqual(df['a'], [1, 1, 1])
        self.assertEqual(df['b'], [1, 1, 1])

    def test_create_dataframe_list_seed(self):
        df = create_dataframe(['a', 'b'], 3, seed=[1, 2])
        self.assertEqual(df['a'], [1, 2, None])
        self.assertEqual(df['b'], [1, 2, None])

    def test_create_dataframe_dict_seed(self):
        df = create_dataframe(['a', 'b'], 3, seed={'a': [1, 2], 'b': [3]})
        self.assertEqual(df['a'], [1, 2, None])
        self.assertEqual(df['b'], [3, None, None])

    def test_create_dataframe_dataframe_seed(self):
        seed_df = Dataframe(a=[1, 2], b=[3, 4])
        df = create_dataframe(['a', 'b', 'c'], 3, seed=seed_df, default_value=0)
        self.assertEqual(df['a'], [1, 2, 0])
        self.assertEqual(df['b'], [3, 4, 0])
        self.assertEqual(df['c'], [0, 0, 0])
    
    def test_or_operator(self):
        df1 = Dataframe(a=[1, 2], b=[3, 4])
        df2 = Dataframe(a=[5, 6], c=[7, 8])
        df3 = df1 | df2
        self.assertEqual(df3['a'], [5, 6])
        self.assertEqual(df3['b'], [3, 4])
        self.assertEqual(df3['c'], [7, 8])

    # additional tests for longer lists and missing values
    def test_or_operator_with_longer_lists_and_missing_values(self):
        df1 = Dataframe(a=[1, 2], b=[3, 4, 9])
        df2 = Dataframe(a=[5, 6], c=[7, 8, 10, 11])
        df3 = df1 | df2
        self.assertEqual(df3['a'], [5, 6, None, None])
        self.assertEqual(df3['b'], [3, 4, 9, None])
        self.assertEqual(df3['c'], [7, 8, 10, 11])
        
    def test_add_operator(self):
        df1 = Dataframe(a=[1, 2], b=[3, 4])
        df2 = Dataframe(a=[5, 6], c=[7, 8])
        df3 = df1 + df2
        self.assertEqual(df1['a'], [1, 2])  # Ensure df1 is not modified
        self.assertEqual(df1['b'], [3, 4])  # Ensure df1 is not modified
        self.assertEqual(df3['a'], [1, 2, 5, 6])
        self.assertEqual(df3['b'], [3, 4, None, None])
        self.assertEqual(df3['c'], [None, None, 7, 8])

    def test_add_operator_with_longer_lists_and_missing_values(self):
        df1 = Dataframe(a=[1, 2, 9], b=[3, 4])
        df2 = Dataframe(a=[5, 6, 7, 8], c=[7, 8])
        df3 = df1 + df2
        self.assertEqual(df1['a'], [1, 2, 9])  # Ensure df1 is not modified
        self.assertEqual(df1['b'], [3, 4, None])  # Ensure df1 is not modified
        self.assertEqual(df3['a'], [1, 2, 9, 5, 6, 7, 8])
        self.assertEqual(df3['b'], [3, 4, None, None, None, None, None])
        self.assertEqual(df3['c'], [None, None, None, 7, 8, None, None])

    def test_or_operator(self):
        df1 = Dataframe(a=[1, 2], b=[3, 4])
        df2 = Dataframe(a=[5, 6], c=[7, 8])
        df3 = df1 | df2
        self.assertEqual(df1['a'], [1, 2])  # Ensure df1 is not modified
        self.assertEqual(df1['b'], [3, 4])  # Ensure df1 is not modified
        self.assertEqual(df3['a'], [5, 6])
        self.assertEqual(df3['b'], [3, 4])
        self.assertEqual(df3['c'], [7, 8])

    def test_or_operator_with_longer_lists_and_missing_values(self):
        df1 = Dataframe(a=[1, 2], b=[3, 4, 9])
        df2 = Dataframe(a=[5, 6], c=[7, 8, 10, 11])
        df3 = df1 | df2
        self.assertEqual(df1['a'], [1, 2, None])  # Ensure df1 is not modified
        self.assertEqual(df1['b'], [3, 4, 9])  # Ensure df1 is not modified
        self.assertEqual(df3['a'], [5, 6, None, None])
        self.assertEqual(df3['b'], [3, 4, 9, None])
        self.assertEqual(df3['c'], [7, 8, 10, 11])


if __name__ == '__main__':
    unittest.main()
