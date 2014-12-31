__author__ = 'justusadam'


class DCException(Exception):
    pass


class ControllerError(DCException):
    pass


class UnexpectedControllerArgumentError(ControllerError):
    pass


class PathResolving(ControllerError):
    pass


class MethodHandlerNotFound(ControllerError):
    pass