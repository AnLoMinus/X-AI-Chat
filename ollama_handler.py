from PyQt5.QtCore import QThread, pyqtSignal
import subprocess
import json

class OllamaThread(QThread):
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, model, prompt):
        super().__init__()
        self.model = model
        self.prompt = prompt

    def run(self):
        try:
            result = subprocess.run(['ollama', 'run', self.model, self.prompt], 
                                    capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                self.error_occurred.emit(f"Ollama returned non-zero exit status {result.returncode}")
            else:
                self.response_received.emit(result.stdout.strip())
        except subprocess.TimeoutExpired:
            self.error_occurred.emit("Error: Ollama response time exceeded the limit.")
        except Exception as e:
            self.error_occurred.emit(f"Error getting response from Ollama: {str(e)}")

def get_available_models():
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        models = result.stdout.strip().split('\n')[1:]  # Skip the header
        return [model.split()[0] for model in models]
    except Exception as e:
        print(f"Error fetching Ollama models: {e}")
        return ["Default Model"]
