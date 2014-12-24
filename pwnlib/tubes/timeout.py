#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import time
from ..context import context

class _DummyContextClass(object):
    def __enter__(self):        pass
    def __exit__(self,*a): pass

_DummyContext = _DummyContextClass()

class _countdown_handler(object):
    def __init__(self, obj, timeout):
        self.obj     = obj
        self.timeout = timeout
    def __enter__(self):
        self.saved = (self.obj._timeout, self.obj._start)
        self.obj._start  = time.time()
        if self.timeout is not None:
            self.obj.timeout = self.timeout # leverage validation
    def __exit__(self, *a):
        (self.obj._timeout, self.obj._start) = self.saved

class _local_handler(object):
    def __init__(self, obj, timeout):
        self.obj     = obj
        self.timeout = timeout
    def __enter__(self):
        self.saved = (self.obj._timeout, self.obj._start)
        self.obj._start  = 0
        if self.timeout is not None:
            self.obj.timeout = self.timeout # leverage validation
        self.obj.timeout_change()
    def __exit__(self, *a):
        (self.obj._timeout, self.obj._start) = self.saved
        self.obj.timeout_change()



class Timeout(object):
    """
    Implements a basic class which has a timeout, and support for
    scoped timeout countdowns.

    Example:

        >>> context.timeout = 30
        >>> t = Timeout()
        >>> t.timeout == 30
        True
        >>> t = Timeout(5)
        >>> t.timeout == 5
        True
        >>> i = 0
        >>> with t.countdown():
        ...     print (4 < t.timeout and t.timeout < 5)
        ...
        True
        >>> remaining = []
        >>> with t.countdown(0.5):
        ...     while t.timeout:
        ...         print round(t.timeout,1)
        ...         time.sleep(0.1)
        0.5
        0.4
        0.3
        0.2
        0.1
        >>> with t.local(0.5)
        ...     for i in range(5):
        ...         print round(t.timeout,1)
        ...         time.sleep(0.1)
        0.5
        0.5
        0.5
        0.5
        0.5

    """
    def __init__(self, timeout=None):
        with context.local(timeout=timeout):
            self._timeout = context.timeout
        self._start   = 0


    @property
    def timeout(self):
        """
        Timeout for obj operations.  By default, uses ``context.timeout``.

        Subject to the same rules and restrictions as ``context.timeout``.
        """
        if self._timeout is None:
            log.error("This shouldn't happen.  Tell Zach.")

        timeout = self._timeout
        start   = self._start

        if start:
            timeout -= (time.time() - start)

        if timeout < 0:
            return 0

        return timeout

    @timeout.setter
    def timeout(self, value):
        # Leverage context validation
        with context.local(timeout=value):
            self._timeout = context.timeout
        self.timeout_change()

    def timeout_change(self):
        """
        Callback for subclasses to hook a timeout change.
        """
        pass

    def countdown(self, timeout=None):
        """
        Scoped timeout setter.  Sets the timeout within the scope,
        and restores it when leaving the scope.

        When accessing :attr:`timeout` within the scope, it will be
        calculated against the time when the scope was entered, in a
        countdown fashion.

        If ``None`` is specified for ``timeout``, then the current
        timeout is used is made.  This allows ``None`` to be specified
        as a default argument with less complexity.

        Implementation Detail:

            This reaches around the property() for ``timeout``.
            If we did not do this, we would effectively be setting
            the ``timeout`` property to ``context.timeout`` if the
            former was not set.
        """
        if timeout is None and self.timeout >= context.forever:
            return _DummyContext
        return _countdown_handler(self, timeout)

    def local(self, timeout = None):
        """
        Scoped timeout setter.  Sets the timeout within the scope,
        and restores it when leaving the scope.
        """
        if timeout is None:
            return _DummyContext
        return _local_handler(self, timeout)
