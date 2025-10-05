"""Package contains all functions accountant is able to logically do.

>>> do_task(conf, mem, "do_get_help", {}, b'')


>>> with Perform(conf, mem, "do_get_help", {}, b'') as job:
>>>     print(job.status, job.attachment, job.attachment_filename)
>>>     assert job.status == "Done"
"""
from .main import do_task, generate_cmd_list, Perform

__all__ = ["do_task", "generate_cmd_list", "Perform"]
