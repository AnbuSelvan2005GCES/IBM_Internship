import platform as plt

def run_network_diagnostics():
    try:
        count_flag = "-n" if plt.system().lower() == "windows" else "-c"
        result = subprocess.run(
            ["ping", count_flag, "3", "8.8.8.8"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout
    except Exception as e:
        return str(e)