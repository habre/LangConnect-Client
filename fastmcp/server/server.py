"""Stub server module for fastmcp.
"""


class FastMCP:
    def __init__(self, name=None):
        self.name = name

    def tool(self, func=None, **kwargs):
        if func is None:

            def decorator(f):
                return f

            return decorator
        return func

    def run(self):
        pass
