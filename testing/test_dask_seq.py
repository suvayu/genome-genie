import numpy as np
from time import sleep
from datetime import datetime
# from itertools import product
# import asyncio
# from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# from glom import glom, Coalesce, Inspect
from dask import delayed
from dask.distributed import LocalCluster, Client

# from genomegenie.utils import flatten

@delayed
def dosomething(name):
    res = {"name": name, "beg": datetime.now()}
    sleep(np.random.randint(10))
    res.update(rand=np.random.rand())
    res.update(end=datetime.now())
    return res


# async def arange(n):
#     for j in [i for i in range(n)]:
#         yield j


# def execute(client, pipeline):
#     res = []
#     for entry in pipeline:
#         if isinstance(entry, tuple):
#             _res = [None] * len(entry)
#             for idx in range(len(entry)):
#                 seq = entry[idx]
#                 if isinstance(seq, list):
#                     _res[idx] = [task.compute() for task in seq]
#                 else:
#                     _res[idx] = seq.compute()
#             res.append(_res)
#         else:
#             res.append(entry.compute())
#     return res


# pipeline = [
#     (
#         [dosomething(f"{a}_{b}") for a, b in product(["foo", "bar", "baz"], [1])],
#         [dosomething(f"{a}_{b}") for a, b in product(["foo", "bar", "baz"], [2])],
#         dosomething("whaat"),
#     ),
#     dosomething("ahem"),
# ]


# loop = asyncio.get_event_loop()
# res = loop.run_until_complete(execute(pipeline))
# loop.close()


seq1 = [dosomething(name) for name in ["foo", "bar", "baz"]]
par1 = dosomething("whaat")
par2 = dosomething("ahem")
pipeline = [seq1, par1, par2]
