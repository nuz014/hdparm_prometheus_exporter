import os
import subprocess
import time
from prometheus_client import start_http_server, Gauge

CONFIG_PATH = "/etc/prometheus_hdparm_exporter/hdparm_exporter.conf"

# Prometheus metrics
# Changed metric names to match hdparm output
disk_buffered_read_speed = Gauge('disk_buffered_read_speed', 'Disk buffered read speed in MB/s', ['disk'])
disk_cached_read_speed = Gauge('disk_cached_read_speed', 'Disk cached read speed in MB/s', ['disk'])

def get_exporter_port():
    port = 9100  # default
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            for line in f:
                if line.strip().startswith("PORT="):
                    try:
                        port = int(line.strip().split("=", 1)[1])
                    except Exception:
                        pass
    return port

def get_disks():
    """Find all disks on the system."""
    result = subprocess.run(['lsblk', '-dno', 'NAME'], stdout=subprocess.PIPE, text=True)
    return [f"/dev/{line.strip()}" for line in result.stdout.splitlines()]

def measure_disk_speed(disk):
    """Run hdparm -Tt on a disk and parse the output."""
    try:
        # Use sudo to call hdparm as root (sudoers file must allow this command without password)
        result = subprocess.run(
            ['sudo', '-n', '/sbin/hdparm', '-Tt', disk],
            stdout=subprocess.PIPE, text=True, check=True
        )
        output = result.stdout
        cache_speed = float(output.splitlines()[-2].split()[-2])  # MB/s
        read_speed = float(output.splitlines()[-1].split()[-2])  # MB/s
        return cache_speed, read_speed
    except Exception as e:
        print(f"Error measuring {disk}: {e}")
        return None, None

def collect_metrics():
    """Collect metrics for all disks."""
    disks = get_disks()
    for disk in disks:
        cache_speed, read_speed = measure_disk_speed(disk)
        if cache_speed is not None and read_speed is not None:
            # Use the new metric names
            disk_cached_read_speed.labels(disk=disk).set(cache_speed)
            disk_buffered_read_speed.labels(disk=disk).set(read_speed)

if __name__ == "__main__":
    port = get_exporter_port()
    start_http_server(port)  # Expose metrics on configured port
    print(f"Serving metrics on port {port}") # Log the port

    # Run once immediately on startup
    collect_metrics()

    # Then run periodically
    while True:
        time.sleep(300)  # Wait for 5 minutes
        collect_metrics()
