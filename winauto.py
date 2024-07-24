from flask import Flask, request, jsonify
import speech_recognition as sr
import pyttsx3
import json
import subprocess
from pywinauto import Application
import winreg
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
import sys
import google.generativeai as genai

app = Flask(__name__)

os.environ["API_KEY"] = "AIzaSyDsTNYvMqYM-LAGUd8fB12rWzVixDsU914"
genai.configure(api_key=os.environ["API_KEY"])
model = genai.GenerativeModel('gemini-1.5-pro')
# Load datasets
with open('app_name.json', 'r') as file:
    apps_to_check = json.load(file)

with open('installation_list.json', 'r') as file:
    install_list = json.load(file)

# Function dataset
functions = {
    "Open Google Chrome with a URL": "open_website_in_chrome",
    "Start an application using pywinauto": "start_application",
    "Install application": "install_application",
    "Generate code": "generate_and_save_code"
}

def get_app_path(app_name):
    try:
        # Check in App Paths
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

        # Special check for explorer.exe
        if app_name.lower() == "explorer" or app_name.lower() == "explorer.exe":
            key_2 = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon")
            explorer_path, _ = winreg.QueryValueEx(key_2, "Shell")
            return os.path.normpath(explorer_path)

    except WindowsError as e:
        print(f"Failed to get {app_name} path. Error: {e}")

    return None

@app.route('/')
def home():
    return "Hello, Flask!"

@app.route('/start_application', methods=['POST'])
def start_application_route():
    data = request.json
    app_name = data.get('app_name')
    app_path = get_app_path(app_name)
    if app_path:
        print(f"Found {app_name} at: {app_path}")
        try:
            app = Application().start(app_path)
            print(f"{app_name} started successfully.")
            return jsonify({"message": f"{app_name} started successfully."})
        except Exception as e:
            print(f"Failed to start {app_name}. Error: {e}")
            return jsonify({"error": f"Failed to start {app_name}. Error: {e}"})
    else:
        print(f"{app_name} not found.")
        return jsonify({"error": f"{app_name} not found."})

@app.route('/install_application', methods=['POST'])
def install_application_route():
    data = request.json
    code = data.get('code')
    try:
        result = subprocess.run(f'powershell -Command "{code}"', shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result.stdout.decode())
        print(f"Application installed successfully.")
        return jsonify({"message": "Application installed successfully.", "output": result.stdout.decode()})
    except subprocess.CalledProcessError as e:
        print(f"Failed to install application. Error: {e.stderr.decode()}")
        return jsonify({"error": f"Failed to install application. Error: {e.stderr.decode()}"})

def compute_similarity(user_input, items):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(items)
    user_input_vec = vectorizer.transform([user_input])
    cosine_similarities = cosine_similarity(user_input_vec, tfidf_matrix).flatten()
    most_similar_index = np.argmax(cosine_similarities)
    return items[most_similar_index], cosine_similarities[most_similar_index]

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

@app.route('/open_website_in_chrome', methods=['POST'])
def open_website_in_chrome_route():
    data = request.json
    url = data.get('url')
    chrome_path = get_app_path("chrome")
    if (chrome_path):
        print(f"Google Chrome found at: {chrome_path}")
        try:
            app = Application().start(f'"{chrome_path}" {url}')
            print(f"Opened {url} in Google Chrome.")
            return jsonify({"message": f"Opened {url} in Google Chrome."})
        except Exception as e:
            print(f"Failed to open website in Chrome. Error: {e}")
            return jsonify({"error": f"Failed to open website in Chrome. Error: {e}"})
    else:
        return jsonify({"error": "Google Chrome not found."})

@app.route('/generate_and_save_code', methods=['POST'])
def generate_and_save_code_route():
    data = request.json
    user_input = data.get('user_input')

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
        
        return jsonify({"message": f"Generated code saved to {filename}", "filename": filename})
    else:
        return jsonify({"error": "Failed to generate code."})

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

@app.route('/send_to_gemini', methods=['POST'])
def send_to_gemini_route():
    data = request.json
    command = data.get('command')
    model = data.get('model')  # Assuming you are passing the model object in the request
    try:
        response = model.generate_content(command)
        if hasattr(response, 'text'):
            return jsonify({"response": response.text})
        elif isinstance(response, str):
            return jsonify({"response": response})
        else:
            print(f"Unexpected response type from Gemini: {type(response)}")
            return jsonify({"response": str(response)})
    except Exception as e:
        print(f"Error sending command to Gemini: {e}")
        return jsonify({"error": f"Error sending command to Gemini: {e}"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)