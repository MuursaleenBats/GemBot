import google.generativeai as genai
from flask import Flask, request, jsonify
import subprocess
import sys
import os

app = Flask(__name__)

os.environ["API_KEY"] = "AIzaSyDsTNYvMqYM-LAGUd8fB12rWzVixDsU914"
genai.configure(api_key=os.environ["API_KEY"])
model = genai.GenerativeModel('gemini-1.5-pro')

@app.route('/generate_and_save_code', methods=['POST'])
def generate_and_save_code_route():
    try:
        data = request.json
        user_input = data.get('user_input')

        if not user_input:
            return jsonify({"error": "No user input provided."}), 400

        print(f"Received user_input: {user_input}")

        language = extract_language(user_input)
        prompt = f"Generate {language} code for: {user_input}. Provide only the code, without explanations."
        print(f"Generated prompt: {prompt}")

        generated_code = send_to_gemini(prompt, model)
        if not generated_code:
            return jsonify({"error": "Failed to generate code."}), 500

        print(f"Generated code (raw): {generated_code}")
        generated_code = generated_code.strip('`')
        if generated_code.startswith(language):
            generated_code = generated_code[len(language):].strip()

        filename = f"generated_code{get_file_extension(language)}"
        try:
            with open(filename, 'w') as file:
                file.write(generated_code)
        except IOError as e:
            print(f"File write error: {e}")
            return jsonify({"error": f"File write error: {e}"}), 500

        print(f"Generated code saved to {filename}")

        # Execute the code if it's Python
        if language.lower() == 'python':
            try:
                result = subprocess.run([sys.executable, filename], capture_output=True, text=True, timeout=10)
                return jsonify({
                    "message": f"Generated code saved to {filename} and executed.",
                    "output": result.stdout,
                    "errors": result.stderr
                })
            except subprocess.TimeoutExpired:
                return jsonify({"error": "Execution timed out after 10 seconds."}), 500
            except Exception as e:
                return jsonify({"error": f"An error occurred while executing the code: {e}"}), 500
        else:
            return jsonify({"message": f"Generated code saved to {filename}. Note: Automatic execution is only supported for Python."})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": f"An error occurred: {e}"}), 500

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

def send_to_gemini(prompt, model):
    retry_attempts = 3
    for attempt in range(retry_attempts):
        try:
            response = model.generate_content(prompt)
            print(f"Raw response from Gemini: {response}")
            if hasattr(response, 'text'):
                return response.text
            elif isinstance(response, str):
                return response
            else:
                print(f"Unexpected response type from Gemini: {type(response)}")
                return str(response)
        except Exception as e:
            print(f"Error sending command to Gemini (attempt {attempt + 1}): {e}")
            time.sleep(2)  # Wait before retrying
    return None

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
