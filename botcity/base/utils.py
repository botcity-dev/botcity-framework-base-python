from functools import wraps
import platform
import subprocess


def is_retina():
    """
    Check whether or not the system is running in "retina" display mode.

    Returns:
    (bool)
    """
    if platform.system() == 'Darwin':
        check = subprocess.call("system_profiler SPDisplaysDataType | grep -i 'retina'", shell=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if check == 0:
            return True
    return False


def only_if_element(func):
    """
    Decorator which raises if element is None in class State.

    Args:
        func (callable): The function to be wrapped

    Returns:
        wrapper (callable): The decorated function
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.state.element is None:
            raise ValueError(f'Element not available. Cannot invoke {func.__name__}.')
        return func(self, *args, **kwargs)

    return wrapper


def find_bot_class(module):
    """
    Args:
        module (module): The module in which to search for the BaseBot class.

    Returns:
        klass (type): A class that inherits from BaseBot.
    """
    import inspect
    from botcity.base import BaseBot

    klass = [obj for name, obj in inspect.getmembers(module) if
             inspect.isclass(obj) and issubclass(obj, BaseBot) and 'botcity.' not in obj.__module__
             and module.__name__ in obj.__module__]

    if not klass:
        raise ValueError('No BaseBot class could be found. Please add at least one class'
                         'inheriting from DesktopBot or similar.')

    return klass
