import copy

class Dataframe(dict):
    def __init__(self, *args, filler=None, **kwargs):
        super().__init__()
        self._width = 0
        self._filler = filler

        if args and isinstance(args[0], list) and all(isinstance(item, dict) for item in args[0]):
            self._init_from_list_of_dicts(args[0])
        else:
            self._update_initial(*args, **kwargs)

    def _init_from_list_of_dicts(self, list_of_dicts):
        if not list_of_dicts:
            return

        keys = list(list_of_dicts[0].keys()) # the keys are determined by the first dict (order is important!)
        for key in keys:
            self[key] = [d.get(key, self._filler) for d in list_of_dicts]

        self._width = len(list_of_dicts)

    def _update_initial(self, *args, **kwargs):
        if args:
            if len(args) > 1:
                raise TypeError("update expected at most 1 arguments, got %d" % len(args))
            other = dict(args[0])
            other.update(kwargs)
        else:
            other = kwargs

        for key, value in other.items():
            if isinstance(value, list):
                self[key] = value
            else:
                self[key] = [value]

        self._width = max(len(value) for value in self.values()) if self else 0
        self._validate_and_fill_data()

    def _validate_and_fill_data(self):
        if not self:
            return

        for key, value in self.items():
            if len(value) < self._width:
                self[key] = value + [self._filler] * (self._width - len(value))

    def update(self, *args, **kwargs):
        if args:
            if len(args) > 1:
                raise TypeError("update expected at most 1 arguments, got %d" % len(args))
            other = dict(args[0])
            other.update(kwargs)
        else:
            other = kwargs

        # Convert all values to lists if they aren't already
        for key, value in other.items():
            if not isinstance(value, list):
                other[key] = [value]

        # Find the maximum length of any value in both self and other
        max_length = max(
            [len(value) for value in self.values()] +
            [len(value) for value in other.values()] +
            [self._width]
        )
        
        # Update existing keys and add new ones
        for key, value in other.items():
            self[key] = value + [self._filler] * (max_length - len(value))

        # Adjust existing keys that weren't in the update data
        for key in self:
            if key not in other:
                if len(self[key]) < max_length:
                    self[key] = self[key] + [self._filler] * (max_length - len(self[key]))
                else:
                    self[key] = self[key][:max_length]

        # Update width
        self._width = max_length
    
    def append(self, value, strict=True):
        if isinstance(value, Dataframe):
            for key in self.keys():
                if key in value:
                    self[key].append(value[key][0] if len(value[key]) > 0 else self._filler)
                else:
                    self[key].append(self._filler)

            if not strict:
                for key in value.keys():
                    if key not in self:
                        self[key] = [self._filler] * self._width + [value[key][0] if len(value[key]) > 0 else self._filler]

        elif isinstance(value, dict):
            for key in self.keys():
                if key in value:
                    self[key].append(value[key])
                else:
                    self[key].append(self._filler)

            if not strict:
                for key in value.keys():
                    if key not in self:
                        self[key] = [self._filler] * self._width + [value[key]]

        else:  # any other type
            for key in self.keys():
                self[key].append(value)

        self._width += 1

    def extend(self, value, strict=True):
        if isinstance(value, Dataframe):
            other_width = value.width
            for key in self.keys():
                if key in value:
                    self[key].extend(value[key] + [self._filler] * (other_width - len(value[key])))
                else:
                    self[key].extend([self._filler] * other_width)

            if not strict:
                for key in value.keys():
                    if key not in self:
                        self[key] = [self._filler] * self._width + value[key] + [self._filler] * (other_width - len(value[key]))

            self._width += other_width

        elif isinstance(value, dict):
            max_len = max(len(v) if isinstance(v, list) else 1 for v in value.values())
            
            for key in self.keys():
                if key in value:
                    v = value[key]
                    if isinstance(v, list):
                        self[key].extend(v + [self._filler] * (max_len - len(v)))
                    else:
                        self[key].extend([v] * max_len)
                else:
                    self[key].extend([self._filler] * max_len)

            if not strict:
                for key in value.keys():
                    if key not in self:
                        v = value[key]
                        if isinstance(v, list):
                            self[key] = [self._filler] * self._width + v + [self._filler] * (max_len - len(v))
                        else:
                            self[key] = [self._filler] * self._width + [v] * max_len

            self._width += max_len

        elif isinstance(value, list):
            for key in self.keys():
                self[key].extend(value)
            
            self._width += len(value)

        else:  # any other type
            raise ValueError("Cannot extend Dataframe with this type. Use 'append' for single values.")
        
    def __add__(self, other):
        # if not isinstance(other, Dataframe):
        #     raise ValueError("Can only add Dataframe to Dataframe")
        result = copy.deepcopy(Dataframe(self))
        result.extend(other, strict=False)
        return result
    
    def __or__(self, other):
        # if not isinstance(other, Dataframe):
        #     raise ValueError("Can only perform '|' operation with Dataframe")
        result = copy.deepcopy(Dataframe(self))
        result.update(other)
        return result

    @property
    def width(self):
        return self._width

    @property
    def length(self):
        return len(self)

    @property
    def shape(self):
        return (self.length, self.width)

    def __repr__(self):
        return f"Dataframe({self.dict_repr()}, shape={self.shape})"

    def dict_repr(self):
        return super().__repr__()

    def print_dict(self):
        print(self.dict_repr())        
        
        
        
from typing import List, Union, Dict


def create_dataframe(
    keys: List[str],
    width: int,
    seed: Union[any, List, Dict, "Dataframe"] = None,
    default_value: any = None,
) -> Dataframe:

    df = Dataframe()

    if not isinstance(seed, (list, dict, Dataframe)):
        # Single value seed (can be of any type)
        for key in keys:
            df[key] = [seed] * width

    elif isinstance(seed, list):
        # List seed (applies to all rows)
        seed_list = seed[:width] + [default_value] * (width - len(seed))
        for key in keys:
            df[key] = seed_list.copy()

    elif isinstance(seed, Dataframe):
        for key in keys:
            if key in seed:
                df[key] = seed[key][:width] + [default_value] * (
                    width - len(seed[key])
                )
            else:
                df[key] = [default_value] * width

    elif isinstance(seed, dict):
        for key in keys:
            if key in seed:
                if isinstance(seed[key], list):
                    # List value for this row
                    df[key] = seed[key][:width] + [default_value] * (
                        width - len(seed[key])
                    )
                else:
                    # Single value for this row
                    df[key] = [seed[key]] * width
            else:
                df[key] = [default_value] * width

    # Fill any missing rows with default_value
    for key in keys:
        if key not in df:
            df[key] = [default_value] * width

    return df
