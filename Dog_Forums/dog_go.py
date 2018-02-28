import task_random

[task_random.collect_profile.delay(page) for page in range(1,task_random.get_tt_pages())]