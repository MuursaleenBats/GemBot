import requests
import json

# URL of the Flask application
base_url = "http://127.0.0.1:5000"

# Sample data to be sent in POST requests
data_start_application = {
    "app_name": "word"
}


data_open_website_in_chrome = {
    "url": "http://example.com"
}

# Helper function to send POST request and print response
def send_post_request(url, data):
    response = requests.post(url, json=data)
    print(f"URL: {url}")
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(json.dumps(response.json(), indent=4))
    print("\n" + "="*50 + "\n")

# Sending POST requests to each endpoint
send_post_request(f"{base_url}/start_application", data_start_application)
#send_post_request(f"{base_url}/generate_and_save_code", data_generate_and_save_code)
#send_post_request(f"{base_url}/open_website_in_chrome", data_open_website_in_chrome)
