import os

from flask import Flask, render_template, request
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException

app = Flask(__name__)

ROUTER = {
    "device_type": "cisco_ios_telnet",
    "ip": "192.168.10.82",
    "port": 32770,
    # Prefer environment variables over hardcoded credentials:
    #   export NET_USER=admin NET_PASS=... NET_SECRET=...
    "username": os.getenv("NET_USER", "admin"),
    "password": os.getenv("NET_PASS", "eve123"),
    "secret": os.getenv("NET_SECRET", "eve123"),
}

COMMANDS = [
    "show version",
    "show ip interface brief",
    "show running-config",
]


@app.route("/", methods=["GET", "POST"])
def index():
    results, error = {}, None

    if request.method == "POST":
        try:
            # The context manager closes the session even if a command fails.
            with ConnectHandler(**ROUTER, conn_timeout=10) as conn:
                conn.enable()
                for cmd in COMMANDS:
                    results[cmd] = conn.send_command(cmd)
        except NetmikoAuthenticationException:
            error = "Login failed. Check the username, password and enable secret."
        except NetmikoTimeoutException:
            error = (f"No response from {ROUTER['ip']}:{ROUTER['port']}. "
                     "Check that the lab node is running and reachable.")
        except Exception as exc:
            error = f"Unexpected error: {exc}"

    return render_template("index.html", results=results, error=error)


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1", host="127.0.0.1", port=5000)