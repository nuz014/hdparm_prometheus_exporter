# hdparm-prometheus-exporter

This package provides a Prometheus exporter that periodically benchmarks all disks on the system using `hdparm -Tt` and exposes the results as Prometheus metrics.

## Features

- Finds all block devices and measures their read and cache speeds every 5 minutes.
- Exposes metrics via HTTP for Prometheus scraping.
- Runs as a dedicated system user (`hdparm_exporter`) for security.
- Installs a systemd service for automatic startup.
- Allows configuration of the exporter port via `/etc/prometheus_hdparm_exporter/hdparm_exporter.conf`.
- Handles proper permissions for running `hdparm` via a sudoers rule.

## Installation

Install the RPM or DEB package on your system. The installer will:
- Create the `hdparm_exporter` user.
- Install the exporter script to `/opt/hdparm_prometheus_exporter/`.
- Install and enable the `hdparm_exporter` systemd service.
- Install a sudoers file to allow the exporter to run `hdparm` without a password.
- Place a default config file at `/etc/prometheus_hdparm_exporter/hdparm_exporter.conf`.

## Configuration

Edit `/etc/prometheus_hdparm_exporter/hdparm_exporter.conf` to change the port or listen IP:

```
# Port for Prometheus exporter to listen on
PORT=9100

# IP address for Prometheus exporter to listen on (0.0.0.0 for all interfaces)
LISTEN_IP=0.0.0.0
```

Restart the service after changing the configuration:

```
sudo systemctl restart hdparm_exporter
```

## Metrics

The exporter exposes the following metrics for each disk:

- `disk_read_speed{disk="/dev/sdX"}`: Disk read speed in MB/s
- `disk_cache_speed{disk="/dev/sdX"}`: Disk cache speed in MB/s

## Removal

When the package is removed, the service, user, sudoers file, and all installed files are cleaned up automatically.

## Security

- The exporter runs as a non-privileged user.
- Only the `hdparm` command can be run as root via sudo, as specified in `/etc/sudoers.d/hdparm_exporter`.