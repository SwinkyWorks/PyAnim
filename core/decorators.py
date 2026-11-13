import functools
import cProfile
import pstats
import time


def analyzed(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()

        try:
            function(*args, **kwargs)
        finally:
            profiler.disable()
            pstats.Stats(profiler).sort_stats("cumulative").print_stats(30)
    return wrapper


def timed(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return function(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start
            if elapsed > 0.01:
                print(f"{function.__qualname__}: {elapsed:.3f}s")
    return wrapper
