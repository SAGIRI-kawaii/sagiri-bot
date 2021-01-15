import psutil

# async def get_all_status(group_id: int) -> str:


# print(psutil.cpu_times(percpu=True))
# print(psutil.cpu_times().user)
print(psutil.cpu_count())
print(psutil.cpu_percent(1))
# print(round(sum([psutil.cpu_percent(x) for x in range(psutil.cpu_count())]) / psutil.cpu_count(), 2))
print(psutil.virtual_memory())