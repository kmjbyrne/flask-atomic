def default_decorator(func):
    """
    Just acts as a pass-through decorator to avoid more complex conditions in
    the endpoint registration function. It is not a hack, it is just avoiding
    silly over-engineered approaches. What does this do? Essentially nothing.

    CAVEAT: This should NOT be modified!

    :param func: pass-through function to be executed.
    :return: unchanged implementation of the function passed in
    """

    def inner_function(*args, **kwargs):
        return func(*args, **kwargs)

    return inner_function
