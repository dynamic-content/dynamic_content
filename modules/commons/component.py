import inspect
import dynamic_content
from dynamic_content.includes import log

__author__ = 'Justus Adam'


@dynamic_content.component('CommonsMap')
class Mapper(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def register(self, name, val):
        if not isinstance(name, str):
            raise TypeError('expected type <str>, got ' + repr(type(name)))
        if name in self:
            log.write_warning(
                'in CommonsMap, register: Overwriting commons handler ', name
                )
        self.__setitem__(name, val)


_mapper = dynamic_content.get_component('CommonsMap')


def register(name, handler):
    _mapper.register(name, handler)


def implements(element_type, *args, **kwargs):
    def _register(func):
        if inspect.isclass(func):
            register(element_type, func(*args, **kwargs))
        elif callable(func):
            register(element_type, func)
        else:
            raise TypeError(
                'Expected class or callable, got {}'.format(type(func))
                )
        return func
    if (not args
        and not kwargs
        and (inspect.isclass(element_type)
            or callable(element_type)
            )
        ):
        element, element_type = element_type, element_type.type
        return _register(element)
    else:
        return _register
