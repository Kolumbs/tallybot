"""Package contains all functions accountant is able to logically do.

>>> do_task(conf, mem, "do_get_help", {}, b'')
"""
from .main import do_task, generate_cmd_list

__all__ = ["do_task", "generate_cmd_list"]
