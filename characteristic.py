from __future__ import absolute_import, division, print_function

"""
Python attributes without boilerplate.
"""

import sys


__version__ = "14.0dev"
__author__ = "Hynek Schlawack"
__license__ = "MIT"
__copyright__ = "Copyright 2014 Hynek Schlawack"

__all__ = [
    "Attribute",
    "NOTHING",
    "attributes",
    "immutable",
    "with_cmp",
    "with_init",
    "with_repr",
]


class _Nothing(object):
    """
    Sentinel class to indicate the lack of a value when ``None`` is ambiguous.

    .. versionadded:: 14.0
    """
    def __repr__(self):
        return "NOTHING"


NOTHING = _Nothing()
"""
Sentinel to indicate the lack of a value when ``None`` is ambiguous.

.. versionadded:: 14.0
"""


class Attribute(object):
    """
    A representation of an attribute.

    In the simplest case, it only consists of a name but more advanced
    properties like default values are possible too.

    :param name: Name of the attribute.
    :type name: str

    :param default_value: A value that is used whenever this attribute isn't
        passed as an keyword argument to a class that is decorated using
        :func:`with_init` (or :func:`attributes` with ``create_init=True``).

        Therefore, setting this makes an attribute *optional*.

        Since a default value of `None` would be ambiguous, a special sentinel
        :data:`NOTHING` is used.  Passing it means the lack of a default value.
    :param default_factory: A factory that is used for generating default
        values whenever this attribute isn't passed as an keyword
        argument to a class that is decorated using :func:`with_init` (or
        :func:`attributes` with ``create_init=True``).

        Therefore, setting this makes an attribute *optional*.
    :type default_factory: callable

    :raises ValueError: If both ``default_value`` and ``default_factory`` have
        been passed.

    .. versionadded:: 14.0
    """
    __slots__ = ["name", "_default", "_default_factory"]

    def __init__(self, name, default_value=NOTHING, default_factory=None):
        if (
                default_value is not NOTHING
                and default_factory is not None
        ):
            raise ValueError(
                "Passing both default_value and default_factory is "
                "ambiguous."
            )

        self.name = name
        if default_value is not NOTHING:
            self._default = default_value
        elif default_factory is not None:
            self._default_factory = default_factory
        else:
            self._default = NOTHING

    def __getattr__(self, name):
        """
        If no value has been set to _default, we need to call a factory.
        """
        if name == "_default" and self._default_factory:
            return self._default_factory()
        else:
            raise AttributeError


def _ensure_attributes(attrs):
    """
    Return a list of :class:`Attribute` generated by creating new instances for
    all non-Attributes.
    """
    return [
        Attribute(a) if not isinstance(a, Attribute) else a
        for a in attrs
    ]


def with_cmp(attrs):
    """
    A class decorator that adds comparison methods based on *attrs*.

    For that, each class is treated like a ``tuple`` of the values of *attrs*.
    But only instances of *identical* classes are compared!

    :param attrs: Attributes to work with.
    :type attrs: :class:`list` of :class:`str` or :class:`Attribute`\ s.
    """
    def attrs_to_tuple(obj):
        """
        Create a tuple of all values of *obj*'s *attrs*.
        """
        return tuple(getattr(obj, a.name) for a in attrs)

    def eq(self, other):
        """
        Automatically created by characteristic.
        """
        if other.__class__ is self.__class__:
            return attrs_to_tuple(self) == attrs_to_tuple(other)
        else:
            return NotImplemented

    def ne(self, other):
        """
        Automatically created by characteristic.
        """
        result = eq(self, other)
        if result is NotImplemented:
            return NotImplemented
        else:
            return not result

    def lt(self, other):
        """
        Automatically created by characteristic.
        """
        if other.__class__ is self.__class__:
            return attrs_to_tuple(self) < attrs_to_tuple(other)
        else:
            return NotImplemented

    def le(self, other):
        """
        Automatically created by characteristic.
        """
        if other.__class__ is self.__class__:
            return attrs_to_tuple(self) <= attrs_to_tuple(other)
        else:
            return NotImplemented

    def gt(self, other):
        """
        Automatically created by characteristic.
        """
        if other.__class__ is self.__class__:
            return attrs_to_tuple(self) > attrs_to_tuple(other)
        else:
            return NotImplemented

    def ge(self, other):
        """
        Automatically created by characteristic.
        """
        if other.__class__ is self.__class__:
            return attrs_to_tuple(self) >= attrs_to_tuple(other)
        else:
            return NotImplemented

    def hash_(self):
        """
        Automatically created by characteristic.
        """
        return hash(attrs_to_tuple(self))

    def wrap(cl):
        cl.__eq__ = eq
        cl.__ne__ = ne
        cl.__lt__ = lt
        cl.__le__ = le
        cl.__gt__ = gt
        cl.__ge__ = ge
        cl.__hash__ = hash_

        return cl

    attrs = _ensure_attributes(attrs)
    return wrap


def with_repr(attrs):
    """
    A class decorator that adds a human readable ``__repr__`` method to your
    class using *attrs*.

    :param attrs: Attributes to work with.
    :type attrs: ``list`` of :class:`str` or :class:`Attribute`\ s.
    """
    def repr_(self):
        """
        Automatically created by characteristic.
        """
        return "<{0}({1})>".format(
            self.__class__.__name__,
            ", ".join(a.name + "=" + repr(getattr(self, a.name))
                      for a in attrs)
        )

    def wrap(cl):
        cl.__repr__ = repr_
        return cl

    attrs = _ensure_attributes(attrs)
    return wrap


def with_init(attrs, defaults=None):
    """
    A class decorator that wraps the ``__init__`` method of a class and sets
    *attrs* using passed *keyword arguments* before calling the original
    ``__init__``.

    Those keyword arguments that are used, are removed from the `kwargs` that
    is passed into your original ``__init__``.  Optionally, a dictionary of
    default values for some of *attrs* can be passed too.

    :param attrs: Attributes to work with.
    :type attrs: ``list`` of :class:`str` or :class:`Attribute`\ s.

    :raises ValueError: If the value for a non-optional attribute hasn't been
        passed as a keyword argument.
    :raises ValueError: If both *defaults* and an instance of
        :class:`Attribute` has been passed.

    .. deprecated:: 14.0
        Use :class:`Attribute` instead of ``defaults``.

    :param defaults: Default values if attributes are omitted on instantiation.
    :type defaults: ``dict`` or ``None``
    """
    if defaults is None:
        defaults = {}

    def characteristic_init(self, *args, **kw):
        """
        Attribute initializer automatically created by characteristic.

        The original `__init__` method is renamed to `__original_init__` and
        is called at the end with the initialized attributes removed from the
        keyword arguments.
        """
        for a in attrs:
            v = kw.pop(a.name, NOTHING)
            if v is NOTHING:
                # Since ``a._default`` could be a property that calls
                # a factory, we make this a separate step.
                v = a._default
            if v is NOTHING:
                raise ValueError(
                    "Missing keyword value for '{0}'.".format(a.name)
                )
            self.__characteristic_setattr__(a.name, v)
        self.__original_init__(*args, **kw)

    def wrap(cl):
        cl.__original_init__ = cl.__init__
        cl.__init__ = characteristic_init
        # Sidestep immutability sentry completely if possible..
        cl.__characteristic_setattr__ = getattr(
            cl, "__original_setattr__", cl.__setattr__
        )
        return cl

    new_attrs = []
    for a in attrs:
        if isinstance(a, Attribute):
            if defaults != {}:
                raise ValueError(
                    "Mixing of the 'defaults' keyword argument and passing "
                    "instances of Attribute for 'attrs' is prohibited.  "
                    "Please don't use 'defaults' anymore, it has been "
                    "deprecated in 14.0."
                )
            new_attrs.append(a)
        else:
            default_value = defaults.get(a)
            if default_value:
                new_attrs.append(
                    Attribute(a, default_value=default_value)
                )
            else:
                new_attrs.append(Attribute(a))

    attrs = new_attrs
    return wrap


_VALID_INITS = frozenset(["characteristic_init", "__init__"])


def immutable(attrs):
    """
    Makes *attrs* of a class immutable.

    That means that *attrs* can only be set from an initializer.  If anyone
    else tries to set one of them, a :exc:`TypeError` is raised.

    .. versionadded:: 14.0
    """
    # In this case, we just want to compare (native) strings.
    attrs = frozenset(attr.name if isinstance(attr, Attribute) else attr
                      for attr in _ensure_attributes(attrs))

    def characteristic_immutability_sentry(self, attr, value):
        """
        Immutability sentry automatically created by characteristic.

        If an attribute is attempted to be set from any other place than
        an initializer, a TypeError is raised.  Else the original
        __setattr__ is called.
        """
        prev = sys._getframe().f_back
        if (
            attr not in attrs
            or
            prev is not None and prev.f_code.co_name in _VALID_INITS
        ):
            self.__original_setattr__(attr, value)
        else:
            raise TypeError(
                "Attribute '{0}' of class '{1}' is immutable."
                .format(attr, self.__class__.__name__)
            )

    def wrap(cl):
        cl.__original_setattr__ = cl.__setattr__
        cl.__setattr__ = characteristic_immutability_sentry
        return cl

    return wrap


def attributes(attrs, defaults=None, create_init=True, make_immutable=True):
    """
    A convenience class decorator that combines :func:`with_cmp`,
    :func:`with_repr`, and optionally :func:`with_init` and
    :func:`immutable` to avoid code duplication.

    :param attrs: Attributes to work with.
    :type attrs: ``list`` of :class:`str` or :class:`Attribute`\ s.

    :param create_init: Also apply :func:`with_init` (default: ``True``)
    :type create_init: bool

    :param make_immutable: Also apply :func:`immutable` (default: ``False``)
    :type make_immutable: bool

    :raises ValueError: If the value for a non-optional attribute hasn't been
        passed as a keyword argument.
    :raises ValueError: If both *defaults* and an instance of
        :class:`Attribute` has been passed.

    .. versionadded:: 14.0
        Added possibility to pass instances of :class:`Attribute` in ``attrs``.

    .. versionadded:: 14.0
        Added ``make_immutable``.

    .. deprecated:: 14.0
        Use :class:`Attribute` instead of ``defaults``.

    :param defaults: Default values if attributes are omitted on instantiation.
    :type defaults: ``dict`` or ``None``
    """
    def wrap(cl):
        cl = with_cmp(attrs)(with_repr(attrs)(cl))
        # Order matters here because with_init can optimize and side-step
        # immutable's sentry function.
        if make_immutable is True:
            cl = immutable(attrs)(cl)
        if create_init is True:
            cl = with_init(attrs, defaults=defaults)(cl)
        return cl
    return wrap
