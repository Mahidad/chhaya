"""
Intentionally empty.

This used to re-export models so `from app.models import User` would work.
Nothing in the codebase imports that way -- every module imports from the
concrete file (`from app.models.user import User`) -- and the shim had
drifted to cover only 8 of the 19 model modules, so following it for one of
the other 11 gave you an ImportError instead of the convenience it promised.

If you want the short import style back, re-export ALL of them, and add new
models here as they're created.
"""
