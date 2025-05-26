import os
import subprocess
import time
from prometheus_client import start_http_server, Gauge
import socket

CONFIG_PATH = "/etc/prometheus_hdparm_exporter/hdparm_exporter.conf"

# Prometheus metrics
# Changed metric names to match hdparm output
disk_buffered_read_speed = Gauge('disk_buffered_read_speed', 'Disk buffered read speed in MB/s', ['disk', 'hostname'])
disk_cached_read_speed = Gauge('disk_cached_read_speed', 'Disk cached read speed in MB/s', ['disk', 'hostname'])

def get_exporter_config():
    """Read exporter configuration from file."""
    port = 9101  # default port
    listen_ip = "0.0.0.0" # default listen IP (all interfaces)
    interval_minutes = 5 # default interval in minutes

    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            for line in f:
                line = line.strip()
                if line.startswith("PORT="):
                    try:
                        port = int(line.split("=", 1)[1])
                    except ValueError:
                        print(f"Warning: Invalid PORT value in {CONFIG_PATH}")
                elif line.startswith("LISTEN_IP="):
                    listen_ip = line.split("=", 1)[1]
                elif line.startswith("INTERVAL_MINUTES="): # Changed config key
                    try:
                        interval_minutes = int(line.split("=", 1)[1])
                    except ValueError:
                        print(f"Warning: Invalid INTERVAL_MINUTES value in {CONFIG_PATH}")

    scrape_interval_seconds = interval_minutes * 60 # Convert minutes to seconds
    return listen_ip, port, scrape_interval_seconds

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
    hostname = socket.gethostname()  # Get the VM hostname
    disks = get_disks()
    for disk in disks:
        cache_speed, read_speed = measure_disk_speed(disk)
        if cache_speed is not None and read_speed is not None:
            disk_cached_read_speed.labels(disk=disk, hostname=hostname).set(cache_speed)
            disk_buffered_read_speed.labels(disk=disk, hostname=hostname).set(read_speed)

if __name__ == "__main__":
    listen_ip, port, scrape_interval = get_exporter_config()
    start_http_server(port, addr=listen_ip)  # Expose metrics on configured IP and port
    print(f"Serving metrics on {listen_ip}:{port}") # Log the IP and port
    print(f"Scraping disks every {scrape_interval} seconds ({scrape_interval // 60} minutes)") # Log interval

    # Run once immediately on startup
    collect_metrics()

    # Then run periodically
    while True:
        time.sleep(scrape_interval)  # Use configured scrape interval (in seconds)
        collect_metrics()
