import platform
import socket
import subprocess


def get_system_information():

    return {
        "operating_system": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }


def check_internet():

    try:

        socket.create_connection(
            ("8.8.8.8", 53),
            timeout=3
        )

        return {
            "status": "connected",
            "message": "Internet connection is available."
        }

    except OSError:

        return {
            "status": "disconnected",
            "message": "Internet connection is unavailable."
        }


def get_ip_address():

    try:

        hostname = socket.gethostname()

        ip = socket.gethostbyname(hostname)

        return {
            "hostname": hostname,
            "ip_address": ip
        }

    except Exception as e:

        return {
            "error": str(e)
        }


def run_network_diagnostics():

    try:

        result = subprocess.run(
            ["ping", "-n", "3", "8.8.8.8"],
            capture_output=True,
            text=True,
            timeout=10
        )

        return result.stdout

    except Exception as e:

        return str(e)