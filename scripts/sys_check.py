import platform
import os

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

os_name = platform.system()
cpu_cores = os.cpu_count()

if HAS_PSUTIL:
    ram = psutil.virtual_memory()
    ram_percent = ram.percent
else:
    ram_percent = "psutil not installed (pip install psutil)"

print(f"OS: {os_name}")
print(f"CPU Cores: {cpu_cores}")
print(f"RAM Utilization: {ram_percent}%")
