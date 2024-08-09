import sys
import threading
from multiprocessing import freeze_support
from typing import Optional
from AutoWin.core import Core

class automater:
    def __init__(self):
        self.core = Core()

    def process_request(self, user_request: str) -> Optional[str]:
        print(f'Processing user request: {user_request}')

        if user_request.lower() == 'stop':
            self.core.stop_previous_request()
            return "Request stopped"
        else:
            # Execute the request and wait for the result
            result = self.core.execute_user_request(user_request)
            return result

    def cleanup(self):
        self.core.cleanup()

def auto(user_request):
    freeze_support()  # As required by pyinstaller
    app = automater()
        
    result = app.process_request(user_request)
    if result:
        print(f"Result: {result}")

    app.cleanup()
    sys.exit(0)
