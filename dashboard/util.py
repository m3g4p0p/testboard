import functools
import time

func_names = set()


def process_time(func):
    func_names.add(func.__name__)

    def wrapper(*args, **kwargs):
        padding = max(map(len, func_names))
        start_time = time.process_time()
        result = func(*args, **kwargs)
        end_time = time.process_time()

        print(f'{func.__name__}:'.ljust(padding + 1) +
              f' {end_time - start_time:0.4f}')

        return result

    return functools.update_wrapper(wrapper, func)
