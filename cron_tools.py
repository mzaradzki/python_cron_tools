

MAX_CRON_PROCESSES = 5 # TO BE CONFIGURED FOR YOUR NEEDS

MIN_VM_SHARE = 0.10    # TO BE CONFIGURED FOR YOUR NEEDS

MAX_RUN_MINUTES = 120  # TO BE CONFIGURED FOR YOUR NEEDS


assert (0. < MIN_VM_SHARE) and (MIN_VM_SHARE < 1.)


from psutil import process_iter

def __get_cron_processes():
	"""
		This function identifies processes that are *likely* CRON processes
		This approach is HEURISTIC only !

		As we work with python we assume :
		   - the process name is python
		   - python is part of the command
		Furthermore we assume :
		   - the process was NOT launched by root user (consistent with crontab)
		   - ipykernel is NOT part of the command to avoid killing Jupyter notebooks

		YOU MAY ADD/REMOVE CONDITIONS
	"""
	processes = [proc for proc in process_iter() if ('python' == proc.name())]
	processes = [proc for proc in processes if ('python' in proc.cmdline())]
	processes = [proc for proc in processes if not(proc.username() is 'root')]
	processes = [proc for proc in processes if not('ipykernel' in proc.cmdline())]
	return processes



from psutil import virtual_memory
from functools import wraps

def cron_control(func=None):
	"""
		A decorator to wrap around each function called by crontab
	"""

	@wraps(func)
	def wrapped(*args, **kwargs):
		vm = virtual_memory()
		if vm.free < MIN_VM_SHARE * vm.total:
			return None # virtual memory usage over limit
		elif len(__get_cron_processes()) > MAX_CRON_PROCESSES: # strict inequality
			return None # process count over limit
		#elif ...:
		#   # ADD MORE CONDITIONS HERE
		# 	return None
		else:
			return func(*args, **kwargs)

	return wrapped



from time import localtime, mktime

def __run_minutes(proc):
	t_start = localtime(proc.create_time())
	t_now = localtime()
	return (mktime(t_now) - mktime(t_start)) / 60.



def cron_killer():
	"""
		This function gets rid of stale CRON processes
	"""
	for proc in __get_cron_processes():
		if __run_minutes(proc) > MAX_RUN_MINUTES:
			if proc.status() in ['sleeping', 'zombie']: # you may want to kill long running processes too
				for sub_proc in proc.children(recursive=True):
					sub_proc.kill()
				proc.kill()
		else:
			None # keep running


