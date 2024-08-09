import json
import pathlib
from typing import Any, List
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import os
from AutoWin.utils.screen import Screen

class GeminiModel:
    def __init__(self, model_name, api_key, context):
        os.environ["API_KEY"] = api_key
        genai.configure(api_key=os.environ["API_KEY"])
        generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
        }

        self.model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
        
        )
        
        self.context = context
        self.chat_session = self.model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        {"text": "Context: " + self.context}
                    ],
                }
            ]
        )
        self.list_of_image_files = []

    def get_instructions_for_objective(self, original_user_request: str, step_num: int = 0) -> dict[str, Any]:
        gemini_screenshot_files = self.upload_screenshots_and_get_files()
        self.list_of_image_files.extend(gemini_screenshot_files)

        formatted_user_request = self.format_user_request_for_llm(original_user_request, step_num, gemini_screenshot_files)
        llm_response = self.send_message_to_llm(formatted_user_request)
        json_instructions: dict[str, Any] = self.convert_llm_response_to_json_instructions(llm_response)

        return json_instructions

    def send_message_to_llm(self, formatted_user_request) -> dict:
        response = self.chat_session.send_message(formatted_user_request)
        return response

    def upload_screenshots_and_get_files(self):
        # Assuming three screenshots are needed; adjust as required
        filepath = Screen().get_screenshot_file()
        screenshot = {
            'mime_type': 'image/png',
            'data': pathlib.Path(filepath).read_bytes()
        }
        return screenshot

    def format_user_request_for_llm(self, original_user_request, step_num, gemini_screenshot_files) -> list[dict[str, Any]]:
        request_data = json.dumps({
            'original_user_request': original_user_request,
            'step_num': step_num
        })

        #content = [{'type': 'text', 'text': request_data}]
        #content.extend([{'type': 'image', 'image': screenshot} for screenshot in gemini_screenshot_files])
        content = [request_data, gemini_screenshot_files]
        return content
    


    def convert_llm_response_to_json_instructions(self, llm_response: dict) -> dict[str, Any]:
        llm_response_data: str = llm_response.text.strip()

        start_index = llm_response_data.find('{')
        end_index = llm_response_data.rfind('}')

        try:
            json_response = json.loads(llm_response_data[start_index:end_index + 1].strip())
        except Exception as e:
            print(f'Error while parsing JSON response - {e}')
            json_response = {}

        return json_response

    def cleanup(self):
        for _ in self.list_of_image_files:
            pass  # Add cleanup code if applicable


