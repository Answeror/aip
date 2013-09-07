from functools import partial
from fn.op import identity, flip


def _compose(f, g, *args, **kargs):
    return f(g(*args, **kargs))


class F(object):
    """Provide simple syntax for functions composition
    (through << and >> operators) and partial function
    application (through simple tuple syntax).

    Usage example:

    >>> func = F() << (_ + 10) << (_ + 5)
    >>> print(func(10))
    25
    >>> func = F() >> (filter, _ < 6) >> sum
    >>> print(func(range(10)))
    15
    """

    __slots__ = "f",

    def __init__(self, f = identity, *args, **kwargs):
        self.f = partial(f, *args, **kwargs) if any([args, kwargs]) else f

    @classmethod
    def __compose(cls, f, g):
        """Produces new class intance that will
        execute given functions one by one. Internal
        method that was added to avoid code duplication
        in other methods.
        """
        return cls(partial(f, g))

    def __ensure_callable(self, f):
        """Simplify partial execution syntax.
        Rerurn partial function built from tuple
        (func, arg1, arg2, ...)
        """
        return self.__class__(*f) if isinstance(f, tuple) else f

    def __rshift__(self, g):
        """Overload << operator for F instances"""
        return self.__class__.__compose(self.__ensure_callable(g), self.f)

    def __lshift__(self, g):
        """Overload >> operator for F instances"""
        return self.__class__.__compose(self.f, self.__ensure_callable(g))

    def  __call__(self, *args, **kwargs):
        """Overload apply operator"""
        return self.f(*args, **kwargs)
