import os
import google.generativeai as genai
import sys
from flask import Flask, request, jsonify
import speech_recognition as sr
import pyttsx3
import json
import subprocess
from pywinauto import Application
import winreg
import os
from sentence_transformers import SentenceTransformer
import re
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import win32gui
import win32process
import win32con
import psutil
from installer.app_install import AppInstaller

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

def start_application(app_name):
    app_path = get_app_path(app_name)
    if app_path:
        try:
            app = Application().start(app_path)
            return f"{app_name} started successfully."
        except Exception as e:
            return f"Failed to start {app_name}. Error: {e}"
    else:
        return f"{app_name} not found."

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

def close_window_function(partial_name):
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
        audio = recognizer.listen(source)
    
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

def process_command(command):
    result = "Did not work"
    response = command  # Simulating the Gemini response
    function_name, similarity_score = find_most_similar_function(response)
    
    if "give code" in command.lower() or "generate code" in command.lower():
        generated_file = generate_and_save_code(command, g_model)
        if generated_file:
            result = f"\nCode has been generated, saved to {generated_file}, and executed (if Python)."
            print(result)
    elif similarity_score >= 0.30:
        if function_name == "open_website_in_chrome":
            extracted_url = extract_url(command)
            if extracted_url:
                result = open_website_in_chrome(extracted_url)
            else:
                result = "No valid URL found in the input."
        elif function_name == "start_application":
            app_name = extract_app_name(command)
            if app_name:
                most_similar_app, most_similar_exe = find_most_similar_app(app_name)
                result = start_application(most_similar_exe)
            else:
                result = "Could not extract application name from input."
        elif function_name == "install_application":
            app_name = extract_app_name(command)
            if app_name:
                result = installer.install_app(app_name)
            else:
                result = "Could not extract application name from input."
        elif function_name == "close_window_function":
            app_name = extract_app_name(command)
            if app_name:
                result = close_window_function(app_name)
            else:
                result = "Could not extract application name from input."
    else:
        result = f"Could not find a function to execute with sufficient similarity (Score: {similarity_score})."

    return jsonify({'result': result})

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
    app.run(port=5000, debug=True)