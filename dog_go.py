import task

[task.collect_profile.delay(page) for page in range(1,task.get_tt_pages())]