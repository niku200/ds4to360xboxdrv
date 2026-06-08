import subprocess
import os
import signal
import logging

logger = logging.getLogger(__name__)

class ProcessRunner:
    def __init__(self, name, command, env=None):
        self.name = name
        self.command = command
        self.env = env or os.environ.copy()
        self.process = None

    def start(self):
        if self.process and self.process.poll() is None:
            logger.warning(f"Process {self.name} is already running.")
            return

        try:
            logger.info(f"Starting {self.name}: {' '.join(self.command)}")
            self.process = subprocess.Popen(
                self.command,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
        except Exception as e:
            logger.error(f"Failed to start {self.name}: {e}")

    def stop(self):
        if not self.process:
            return

        logger.info(f"Stopping {self.name} (PID: {self.process.pid})")
        try:
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning(f"{self.name} did not stop gracefully, killing...")
            os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
        except Exception as e:
            logger.error(f"Error stopping {self.name}: {e}")
        finally:
            self.process = None

    def is_running(self):
        return self.process is not None and self.process.poll() is None
