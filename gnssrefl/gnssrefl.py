import numpy as np

def convert(my_name):
    """
    Print a line about converting a notebook.
    Args:
        my_name (str): person's name
    Returns:
        None
    """
    tv = np.empty(shape=[0, 4])
    year = 2020; mm = 6 ; dd = 1
    for i in range(0,10):
        hh = i
        newl = [year, mm, dd, hh ]
        tv = np.append(tv, [newl],axis=0)
    print(tv)

    print(f"I'll convert a notebook for you some day, {my_name}.")
