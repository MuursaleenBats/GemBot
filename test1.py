import requests
import json

def send_post_request(url, data):
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        try:
            response_json = response.json()
            print("Response JSON:")
            print(json.dumps(response_json, indent=4))
        except requests.exceptions.JSONDecodeError:
            print("Response is not valid JSON.")
            print("Response Text:")
            print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

base_url = "http://127.0.0.1:5000"

data_generate_and_save_code = {
    "user_input": "add two numbers using function and call the function",

}

send_post_request(f"{base_url}/generate_and_save_code", data_generate_and_save_code)
