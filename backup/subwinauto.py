import google.generativeai as genai
import win32gui
import win32process
import win32con
import win32api
import psutil
import json
import re
import os
import time
import logging
from pywinauto import Application, timings, mouse
from pywinauto import Desktop, findwindows
from pywinauto.keyboard import send_keys
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Initialize Gemini model
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

def process_command(command, max_retries=3):
    if not command.strip():
        return "Empty command. Please provide a valid command."

    prompt = f"""
    Given the user command: "{command}"
    Generate a JSON response with the appropriate UI action and parameters.
    Possible actions are:
    1. close_window: Requires a "window_name" parameter
    2. list_windows: No parameters required
    3. interact_with_control: Requires "window_name", "control_type", "control_name", and "action" parameters
    4. navigate_in_browser: Requires "browser_name" and "url" parameters
    5. file_explorer_operation: Requires "operation" and additional parameters based on the operation
    6. list_processes: No parameters required
    7. get_process_info: Requires a "pid" parameter
    8. no_action: Use this if no UI action is needed

    Example response formats:
    {{"action": "close_window", "params": {{"window_name": "Firefox"}}}}
    {{"action": "list_windows"}}
    {{"action": "interact_with_control", "params": {{"window_name": "Notepad", "control_type": "Edit", "control_name": "Text Editor", "action": "type_keys", "value": "Hello, World!"}}}}
    {{"action": "navigate_in_browser", "params": {{"browser_name": "Chrome", "url": "https://www.example.com"}}}}
    {{"action": "file_explorer_operation", "params": {{"operation": "rename_files", "folder_path": "C:/Users/YourName/Documents", "file_pattern": "*.txt", "new_name": "renamed_{{index}}.txt"}}}}
    {{"action": "list_processes"}}
    {{"action": "get_process_info", "params": {{"pid": 1234}}}}
    {{"action": "no_action", "response": "Hello! How can I assist you with UI automation today?"}}
    """

    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)

            json_match = re.search(r'```json\s*(.*?)\s*```', response.text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response.text

            action_data = json.loads(json_str)

            if not isinstance(action_data, dict):
                raise ValueError(f"Invalid response format. Expected a dictionary, got: {type(action_data)}")

            if "action" not in action_data:
                raise ValueError(f"Invalid response from AI model. Missing 'action' key. Response: {action_data}")

            if action_data["action"] == "no_action":
                return action_data.get("response", "No action needed")

            result = execute_ui_action(action_data["action"], action_data.get("params", {}))
            return result
        except Exception as e:
            logging.error(f"Error in process_command: {str(e)}")
            if attempt < max_retries - 1:
                logging.info(f"Retrying in 5 seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(5)
            else:
                return f"An error occurred after {max_retries} attempts: {str(e)}"

def execute_ui_action(action, params):
    try:
        if action == "close_window":
            return close_window(params.get("window_name"))
        elif action == "list_windows":
            return "\n".join(list_windows())
        elif action == "interact_with_control":
            return interact_with_control(params)
        elif action == "navigate_in_browser":
            return navigate_in_browser(params.get("browser_name"), params.get("url"), params.get("search_query"))
        elif action == "file_explorer_operation":
            return file_explorer_operation(params)
        elif action == "list_processes":
            return "\n".join(list_processes())
        elif action == "get_process_info":
            return get_detailed_process_info(params.get("pid"))
        else:
            return f"Unknown action: {action}"
    except Exception as e:
        logging.error(f"Error in execute_ui_action: {str(e)}")
        return f"Error executing UI action: {str(e)}"

def find_window(window_name):
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            if window_name.lower() in win32gui.GetWindowText(hwnd).lower():
                hwnds.append(hwnd)
        return True
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds

def close_window(window_name):
    hwnds = find_window(window_name)
    if not hwnds:
        return f"Window '{window_name}' not found"
    for hwnd in hwnds:
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
    return f"Sent close command to {len(hwnds)} window(s) matching '{window_name}'"

def list_windows():
    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            windows.append(win32gui.GetWindowText(hwnd))
        return True
    windows = []
    win32gui.EnumWindows(callback, windows)
    return [w for w in windows if w]  # Remove empty strings

def interact_with_control(params):
    window_name = params.get("window_name")
    control_type = params.get("control_type")
    control_name = params.get("control_name")
    action = params.get("action")
    value = params.get("value")

    if not all([window_name, control_type, control_name, action]):
        return "Missing required parameters for interact_with_control"

    try:
        app = Application(backend="uia").connect(title=window_name, timeout=10)
        window = app.window(title=window_name)
        control = getattr(window, control_type)(title=control_name)

        if action == "type_keys":
            control.type_keys(value, with_spaces=True)
        elif action == "click":
            control.click_input()
        elif action == "double_click":
            control.double_click_input()
        elif action == "right_click":
            control.right_click_input()
        elif action == "scroll":
            control.scroll(value)
        else:
            return f"Unknown action for control: {action}"

        return f"Successfully performed {action} on {control_type} '{control_name}' in {window_name}"
    except Exception as e:
        logging.error(f"Error in interact_with_control: {str(e)}")
        return f"Error interacting with control: {str(e)}"

def navigate_in_browser(browser_name, url, search_query=None):
    if not browser_name or not url:
        return "Missing browser name or URL"

    try:
        print("Listing all windows for debugging:")
        windows = list_windows()
        for window in windows:
            print(f"Window: {window}")

        retries = 3
        for attempt in range(retries):
            try:
                logging.info(f"Attempt {attempt + 1} to find and interact with {browser_name}")
                app = Application(backend="uia").connect(title_re=f".*{browser_name}.*", found_index=0, timeout=10)
                all_windows = app.windows()

                # Try to find the main browser window
                browser_window = None
                for win in all_windows:
                    win_title = win.window_text().lower()
                    logging.info(f"Checking window: {win.window_text()}")
                    if browser_name.lower() in win_title:
                        browser_window = win
                        break

                if not browser_window:
                    raise Exception("No suitable browser window found")

                logging.info(f"Connected to {browser_name} window: {browser_window.window_text()}")

                # Open a new tab first
                browser_window.set_focus()
                send_keys('^t')  # Ctrl+T to open a new tab
                time.sleep(1)  # Wait for the new tab to open

                # Navigate to Google if the search query is provided
                if search_query:
                    send_keys('^l')  # Ctrl+L to focus on the address bar
                    time.sleep(0.5)
                    send_keys('^a')  # Select all existing text
                    send_keys('{BACKSPACE}')  # Clear the address bar
                    send_keys('https://www.google.com{ENTER}')
                    time.sleep(2)  # Wait for Google to load

                    # Simulate typing the search query and pressing Enter
                    send_keys(search_query + '{ENTER}')
                else:
                    # If no search query is provided, just navigate to the URL
                    send_keys('^l')  # Ctrl+L to focus on the address bar
                    time.sleep(0.5)
                    send_keys('^a')  # Select all existing text
                    send_keys('{BACKSPACE}')  # Clear the address bar
                    send_keys(url + '{ENTER}')
                    time.sleep(2)  # Wait for the page to load

                return f"Opened a new tab and navigated to {url} in {browser_name}"
            except Exception as e:
                logging.error(f"Error in navigate_in_browser attempt {attempt + 1}: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(2)  # Wait before retrying

        return f"Error navigating in browser: No windows for {browser_name} could be found after {retries} attempts"
    except Exception as e:
        logging.error(f"Error in navigate_in_browser: {str(e)}")
        return f"Error navigating in browser: {str(e)}"

def get_current_file_explorer_path():
    try:
        hwnds = find_window("File Explorer")
        if not hwnds:
            return None

        for hwnd in hwnds:
            app = Application(backend="uia").connect(handle=hwnd)
            explorer_window = app.top_window()
            address_bar = explorer_window.child_window(auto_id="Address Band Root", control_type="ToolBar")
            address_edit = address_bar.child_window(control_type="Edit")
            path = address_edit.get_value()
            if path:
                return path

        return None
    except Exception as e:
        logging.error(f"Error getting current File Explorer path: {str(e)}")
        return None

def file_explorer_operation(params):
    operation = params.get("operation")
    folder_path = params.get("folder_path")

    if not operation:
        return "Missing operation"

    try:
        if not folder_path:
            folder_path = get_current_file_explorer_path()
            if not folder_path:
                folder_path = input("Folder path not found. Please enter the folder path: ")
            if not os.path.exists(folder_path):
                return f"Folder not found: {folder_path}"

        os.startfile(folder_path)
        time.sleep(1)

        app = Application(backend="uia").connect(title_re=".*File Explorer.*", timeout=10)
        explorer_window = app.top_window()

        if operation == "rename_files":
            return rename_files(explorer_window, params)
        elif operation == "select_files":
            return select_files(explorer_window, params)
        elif operation == "navigate_to_folder":
            return navigate_to_folder(explorer_window, params)
        else:
            return f"Unknown file explorer operation: {operation}"
    except Exception as e:
        logging.error(f"Error in file_explorer_operation: {str(e)}")
        return f"Error in file explorer operation: {str(e)}"

def rename_files(explorer_window, params):
    file_pattern = params.get("file_pattern")
    new_name = params.get("new_name")

    if not file_pattern or not new_name:
        return "Missing file pattern or new name"

    try:
        folder_path = get_current_file_explorer_path()
        if not folder_path:
            return "Could not retrieve the current File Explorer path"

        files = [f for f in os.listdir(folder_path) if re.match(file_pattern, f)]
        if not files:
            return f"No files matching the pattern '{file_pattern}' found in '{folder_path}'"

        for index, file in enumerate(files, start=1):
            new_file_name = new_name.replace("{index}", str(index))
            os.rename(os.path.join(folder_path, file), os.path.join(folder_path, new_file_name))

        return f"Renamed files matching '{file_pattern}' to '{new_name}' in '{folder_path}'"
    except Exception as e:
        logging.error(f"Error in rename_files: {str(e)}")
        return f"Error renaming files: {str(e)}"

def select_files(explorer_window, params):
    file_pattern = params.get("file_pattern")

    if not file_pattern:
        return "Missing file pattern"

    try:
        explorer_window.set_focus()
        send_keys(f'{file_pattern}')
        time.sleep(0.5)
        send_keys('^a')

        return f"Selected files matching '{file_pattern}'"
    except Exception as e:
        logging.error(f"Error in select_files: {str(e)}")
        return f"Error selecting files: {str(e)}"

def navigate_to_folder(explorer_window, params):
    target_folder = params.get("target_folder")

    if not target_folder:
        return "Missing target folder"

    try:
        explorer_window.set_focus()
        send_keys('^l')  # Ctrl+L to focus on the address bar
        time.sleep(0.5)
        send_keys('^a')  # Select all existing text
        send_keys('{BACKSPACE}')  # Clear the address bar
        send_keys(target_folder + '{ENTER}')
        time.sleep(2)  # Wait for the folder to load

        return f"Navigated to folder: {target_folder}"
    except Exception as e:
        logging.error(f"Error in navigate_to_folder: {str(e)}")
        return f"Error navigating to folder: {str(e)}"

def list_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'status']):
        try:
            processes.append(f"PID: {proc.info['pid']}, Name: {proc.info['name']}, Status: {proc.info['status']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return processes

def get_process_info(pid):
    try:
        handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid)
        exe = win32process.GetModuleFileNameEx(handle, 0)
        return exe
    except:
        return None

def get_detailed_process_info(pid):
    try:
        pid = int(pid)
        process = psutil.Process(pid)
        exe_path = get_process_info(pid)
        return f"PID: {pid}, Name: {process.name()}, Exe: {exe_path}, Status: {process.status()}"
    except Exception as e:
        logging.error(f"Error in get_detailed_process_info: {str(e)}")
        return f"Error getting process info for PID {pid}: {str(e)}"

def main():
    print("Welcome to the UI Automation Assistant!")
    print("Enter 'exit' to quit the program.")

    while True:
        try:
            user_input = input("Enter a command: ").strip()
            if user_input.lower() == 'exit':
                print("Exiting the program. Goodbye!")
                break
            result = process_command(user_input)
            print(result)
        except KeyboardInterrupt:
            print("\nProgram interrupted. Exiting...")
            break
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()
