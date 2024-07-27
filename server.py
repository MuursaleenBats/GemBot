import os
import google.generativeai as genai
import sys
from flask import Flask, request, jsonify
import speech_recognition as sr
import pyttsx3
import json
import subprocess
from pywinauto import Application, timings, mouse
from pywinauto import Desktop, findwindows
from pywinauto.keyboard import send_keys
import winreg
import os
from sentence_transformers import SentenceTransformer
import re
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import win32gui
import win32process
import win32con
import win32api
import psutil
import time
import logging
from installer.app_install import AppInstaller
import threading
import time
#sab changa si

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

os.environ["API_KEY"] = "AIzaSyDsTNYvMqYM-LAGUd8fB12rWzVixDsU914"
genai.configure(api_key=os.environ["API_KEY"])
g_model = genai.GenerativeModel('gemini-1.5-pro')

app = Flask(__name__)
installer = AppInstaller()
# Load datasets
with open('app_name.json', 'r') as file:
    apps_to_check = json.load(file)

with open('installation_list.json', 'r') as file:
    install_list = json.load(file)

# Function dataset
functions = {
    "Open website in chrome": "open_website_in_chrome",
    "Start application": "start_application",
    "Install app": "install_application",
    "Close window": "close_window_function",
    "Generate code": "generate_and_save_code"
}

model = SentenceTransformer('all-MiniLM-L6-v2')  # Load the model once

def get_app_path(app_name):
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths")
        for i in range(winreg.QueryInfoKey(key)[0]):
            try:
                subkey_name = winreg.EnumKey(key, i)
                if subkey_name.lower() == app_name.lower() or subkey_name.lower() == app_name.lower() + '.exe':
                    subkey = winreg.OpenKey(key, subkey_name)
                    path, _ = winreg.QueryValueEx(subkey, "")
                    return os.path.normpath(path)
            except WindowsError:
                continue

        if app_name.lower() == "explorer" or app_name.lower() == "explorer.exe":
            key_2 = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon")
            explorer_path, _ = winreg.QueryValueEx(key_2, "Shell")
            return os.path.normpath(explorer_path)
        
    except WindowsError as e:
        print(f"Failed to get {app_name} path. Error: {e}")
    return None

def listen_for_keyword():
    recognizer = sr.Recognizer()
    while True:
        with sr.Microphone() as source:
            print("Listening for 'Gemini'...")
            audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio).lower()
            print(f"Heard: {text}")
            if "gemini" in text:
                print("Keyword 'Gemini' detected! Listening for command...")
                command = listen_for_command()
                if command:
                    result = process_command(command)
                    print(f"Command result: {result}")
                    # You might want to add text-to-speech here to speak the result
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")

def start_application(app_name):
    app_path = get_app_path(app_name)
    if app_path:
        try:
            app = Application().start(app_path)
            return f"{app_name} started successfully."
        except Exception as e:
            return f"Failed to start {app_name}. Error: {e}"       
    else:
        try:
            app = Application().start(f"{app_name}")
            return f"{app_name} started successfully."
        except Exception as e:
            return f"Failed to start {app_name}."

def install_application(code):
    try:
        result = subprocess.run(f'powershell -Command "{code}"', shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode()
    except subprocess.CalledProcessError as e:
        return f"Failed to install application. Error: {e.stderr.decode()}"

def compute_similarity(user_input, items):
    user_input_embedding = model.encode([user_input])
    items_embeddings = model.encode(items)
    similarities = cosine_similarity(user_input_embedding, items_embeddings)[0]
    most_similar_index = similarities.argmax()
    return items[most_similar_index], similarities[most_similar_index]

def find_most_similar_app(user_input):
    app_names = list(apps_to_check.keys())
    most_similar_app, similarity_score = compute_similarity(user_input, app_names)
    most_similar_exe = apps_to_check[most_similar_app]
    return most_similar_app, most_similar_exe

def find_installation(user_input):
    install_names = list(install_list.keys())
    most_similar_key, similarity_score = compute_similarity(user_input, install_names)
    code = install_list[most_similar_key]
    return code

def find_most_similar_function(user_input):
    function_descriptions = list(functions.keys())
    most_similar_function, similarity_score = compute_similarity(user_input, function_descriptions)
    function_name = functions[most_similar_function]
    return function_name, similarity_score

def open_website_in_chrome(url):
    chrome_path = get_app_path("chrome")
    if chrome_path:
        try:
            app = Application().start(f'"{chrome_path}" {url}')
            return f"Opened {url} in Google Chrome."
        except Exception as e:
            return f"Failed to open website in Chrome. Error: {e}"
    else:
        return "Google Chrome not found."
    
def send_to_gemini(command, model):
    try:
        response = model.generate_content(command)
        if hasattr(response, 'text'):
            return response.text
        elif isinstance(response, str):
            return response
        else:
            print(f"Unexpected response type from Gemini: {type(response)}")
            return str(response)
    except Exception as e:
        print(f"Error sending command to Gemini: {e}")
        return None
def list_windows():
    def winEnumHandler(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process = psutil.Process(pid)
                    ctx.append(f"{title} (Process: {process.name()})")
                except:
                    ctx.append(title)
    windows = []
    win32gui.EnumWindows(winEnumHandler, windows)
    return windows

def find_window(partial_name):
    partial_name = partial_name.lower()
    matching_windows = []
    for window in list_windows():
        if partial_name in window.lower():
            matching_windows.append(window)
    return matching_windows

def close_window_function(partial_name):
    matching_windows = find_window(partial_name)
    if matching_windows:
        if len(matching_windows) == 1:
            full_name = matching_windows[0]
            title = full_name.split(" (Process: ")[0]
            process_name = full_name.split("(Process: ")[1][:-1]  # Remove the last ')'
            
            def enum_windows_callback(hwnd, result):
                if win32gui.IsWindowVisible(hwnd) and title.lower() in win32gui.GetWindowText(hwnd).lower():
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    if psutil.Process(pid).name().lower() == process_name.lower():
                        result.append(hwnd)
                return True

            result = []
            win32gui.EnumWindows(enum_windows_callback, result)
            
            if result:
                hwnd = result[0]
                try:
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                    return f"Sent close command to window: {full_name}"
                except Exception as e:
                    return f"Error while trying to close window {full_name}: {str(e)}"
            else:
                return f"Found window in list, but couldn't interact with it: {full_name}"
        else:
            return f"Multiple matching windows found: {', '.join(matching_windows)}. Please be more specific."
    else:
        return f"No windows found matching: {partial_name}. Available windows: {', '.join(list_windows())}"

def generate_and_save_code(user_input, model):
    language = extract_language(user_input)
    
    prompt = f"Generate {language} code for: {user_input}. Provide only the code, without explanations."
    generated_code = send_to_gemini(prompt, model)
    
    if generated_code:
        extension = get_file_extension(language)
        filename = f"generated_code{extension}"
        
        # Remove any potential markdown code block syntax
        generated_code = generated_code.strip('`')
        if generated_code.startswith(language):
            generated_code = generated_code[len(language):].strip()
        
        with open(filename, 'w') as file:
            file.write(generated_code)
        
        print(f"Generated code saved to {filename}")
        
        # Execute the code if it's Python
        if language.lower() == 'python':
            print("\nExecuting the generated Python code:")
            try:
                # Use subprocess to run the Python script
                result = subprocess.run([sys.executable, filename], capture_output=True, text=True, timeout=10)
                print("Output:")
                print(result.stdout)
                if result.stderr:
                    print("Errors:")
                    print(result.stderr)
            except subprocess.TimeoutExpired:
                print("Execution timed out after 10 seconds.")
            except Exception as e:
                print(f"An error occurred while executing the code: {e}")
        else:
            print(f"\nNote: Automatic execution is only supported for Python. The {language} code has been saved but not executed.")
        
        return filename
    else:
        print("Failed to generate code.")
        return None

def extract_language(text):
    languages = ['python', 'java', 'javascript', 'c++', 'c#', 'ruby']
    for lang in languages:
        if lang in text.lower():
            return lang
    return 'python'  # Default to Python if no language is specified

def get_file_extension(language):
    extensions = {
        'python': '.py',
        'java': '.java',
        'javascript': '.js',
        'c++': '.cpp',
        'c#': '.cs',
        'ruby': '.rb'
    }
    return extensions.get(language, '.txt')

def listen_for_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for command...")
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
    
    try:
        command = recognizer.recognize_google(audio)
        print(f"Recognized command: {command}")
        return command
    except sr.UnknownValueError:
        print("Could not understand audio")
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return None


@app.route('/command', methods=['POST'])
def handle_command():
    data = request.json
    user_input = data.get('command')
    print(user_input)

    if user_input.lower() == "mic":
        # Activate speech recognition
        spoken_command = listen_for_command()
        if spoken_command:
            # Process the spoken command
            return process_command(spoken_command)
        else:
            return jsonify({'result': "Failed to recognize speech command."})
    else:
        # Process the text command as before
        return process_command(user_input)

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
    8. open_website_in_chrome: Requires a "url" parameter
    9. start_application: Requires an "app_name" parameter
    10. install_application: Requires an "app_name" parameter
    11. generate_and_save_code: Requires a "language" and "code_description" parameter
    12. no_action: Use this if no UI action is needed

    Example response formats:
    {{"action": "close_window", "params": {{"window_name": "Firefox"}}}}
    {{"action": "list_windows"}}
    {{"action": "interact_with_control", "params": {{"window_name": "Notepad", "control_type": "Edit", "control_name": "Text Editor", "action": "type_keys", "value": "Hello, World!"}}}}
    {{"action": "navigate_in_browser", "params": {{"browser_name": "Chrome", "url": "https://www.example.com"}}}}
    {{"action": "file_explorer_operation", "params": {{"operation": "rename_files", "folder_path": "C:/Users/YourName/Documents", "file_pattern": "*.txt", "new_name": "renamed_{{index}}.txt"}}}}
    {{"action": "list_processes"}}
    {{"action": "get_process_info", "params": {{"pid": 1234}}}}
    {{"action": "open_website_in_chrome", "params": {{"url": "https://www.example.com"}}}}
    {{"action": "start_application", "params": {{"app_name": "winword.exe"}}}}
    {{"action": "install_application", "params": {{"app_name": "Chrome"}}}}
    {{"action": "generate_and_save_code", "params": {{"language": "python", "code_description": "A function to calculate fibonacci numbers"}}}}
    {{"action": "no_action", "response": "Hello! How can I assist you with UI automation today?"}}
    """

    for attempt in range(max_retries):
        try:
            response = g_model.generate_content(prompt)
            print(response)
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
    

def execute_ui_action(action, params):
    try:
        if action == "close_window":
            return close_window_function(params.get("window_name"))
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
        elif action == "open_website_in_chrome":
            return open_website_in_chrome(params.get("url"))
        elif action == "start_application":
            return start_application(params.get("app_name"))
        elif action == "install_application":
            return installer.install_app(params.get("app_name"))
        elif action == "generate_and_save_code":
            return generate_and_save_code(params.get("language") + params.get("code_description"), g_model)
        else:
            return f"Unknown action: {action}"
    except Exception as e:
        logging.error(f"Error in execute_ui_action: {str(e)}")

def extract_url(text):
    url_pattern = re.compile(r"[a-zA-Z0-9.-]+\.(com|org|net|edu|gov)")
    match = url_pattern.search(text)
    if match:
        return match.group(0)
    return None

def extract_app_name(text):
    start_match = re.search(r'\bstart\b\s+(\w+)', text)
    install_match = re.search(r'\binstall\b\s+(\w+)', text)
    close_match = re.search(r'\bclose\b\s+(\w+)', text)
    if start_match:
        return start_match.group(1)
    elif install_match:
        return install_match.group(1)
    elif close_match:
        return close_match.group(1)
    return None

if __name__ == "__main__":
    voice_thread = threading.Thread(target=listen_for_keyword, daemon=True)
    voice_thread.start()
    app.run(port=5000, debug=True)