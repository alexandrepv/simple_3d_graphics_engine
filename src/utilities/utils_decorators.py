
class hooked:
    def __init__(self, fn):
        self.fn = fn

    def __set_name__(self, owner, name):
        func = self.fn

        def _decorator(self, *args, **kwargs):
            super_obj = super(owner, self)
            super_fn = getattr(super_obj, func.__name__)
            super_fn(*args, **kwargs)
            return func(self, *args, **kwargs)

        setattr(owner, name, _decorator)

    def __call__(self):
        assert (
            False
        ), "@hooked decorator object should never be called directly. This can happen if you apply this decorator to a function that is not a method."
