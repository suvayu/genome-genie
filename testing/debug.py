from dask.distributed import LocalCluster

class DummyCluster(LocalCluster):

    # Override class variables
    submit_command = 'bash'
    cancel_command = 'qdel'
    scheduler_name = 'sge'
