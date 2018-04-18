# noinspection PyPep8Naming, PyMethodOverriding
class classproperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()
