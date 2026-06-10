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
            return

        try:
            logger.debug(f"Starting {self.name}: {' '.join(self.command)}")
            # Use PIPE for stderr so we can report errors if it fails to start or dies
            self.process = subprocess.Popen(
                self.command,
                env=self.env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True
            )
        except Exception as e:
            logger.error(f"Failed to start {self.name}: {e}")

    def get_stderr(self):
        if self.process and self.process.stderr:
            # Non-blocking read would be better, but for now we just try to read what's there
            try:
                import fcntl
                fd = self.process.stderr.fileno()
                fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
                return self.process.stderr.read()
            except:
                return None
        return None

    def stop(self):
        if not self.process:
            return

        pid = self.process.pid
        logger.debug(f"Stopping {self.name} (PID: {pid})")
        try:
            os.killpg(pid, signal.SIGTERM)
            self.process.wait(timeout=5)
        except (ProcessLookupError, PermissionError):
            pass
        except subprocess.TimeoutExpired:
            logger.warning(f"{self.name} did not stop gracefully, killing...")
            try:
                os.killpg(pid, signal.SIGKILL)
                self.process.wait(timeout=2)
            except (ProcessLookupError, PermissionError):
                pass
            except Exception as e:
                logger.error(f"Error killing {self.name}: {e}")
        except Exception as e:
            logger.error(f"Error stopping {self.name}: {e}")
        finally:
            self.process = None

    def is_running(self):
        return self.process is not None and self.process.poll() is None
