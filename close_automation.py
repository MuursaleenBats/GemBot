# import google.generativeai as genai
# import win32gui
# import win32process
# import win32con
# import psutil
# import json
# import re
# import os
# import time

# # Configure the Gemini API
# os.environ["API_KEY"] = "AIzaSyDsTNYvMqYM-LAGUd8fB12rWzVixDsU914"
# genai.configure(api_key=os.environ["API_KEY"])
# model = genai.GenerativeModel('gemini-1.5-pro')

# def list_windows():
#     def winEnumHandler(hwnd, ctx):
#         if win32gui.IsWindowVisible(hwnd):
#             title = win32gui.GetWindowText(hwnd)
#             if title:
#                 try:
#                     _, pid = win32process.GetWindowThreadProcessId(hwnd)
#                     process = psutil.Process(pid)
#                     ctx.append(f"{title} (Process: {process.name()})")
#                 except:
#                     ctx.append(title)
#     windows = []
#     win32gui.EnumWindows(winEnumHandler, windows)
#     return windows

# def find_window(partial_name):
#     partial_name = partial_name.lower()
#     matching_windows = []
#     for window in list_windows():
#         if partial_name in window.lower():
#             matching_windows.append(window)
#     return matching_windows

# def close_window(window_name):
#     matching_windows = find_window(window_name)
#     if matching_windows:
#         if len(matching_windows) == 1:
#             full_name = matching_windows[0]
#             # Extract just the window title (everything before " (Process: ")
#             title = full_name.split(" (Process: ")[0]
#             process_name = full_name.split("(Process: ")[1][:-1]  # Remove the last ')'
            
#             def enum_windows_callback(hwnd, result):
#                 if win32gui.IsWindowVisible(hwnd) and title.lower() in win32gui.GetWindowText(hwnd).lower():
#                     _, pid = win32process.GetWindowThreadProcessId(hwnd)
#                     if psutil.Process(pid).name().lower() == process_name.lower():
#                         result.append(hwnd)
#                 return True

#             result = []
#             win32gui.EnumWindows(enum_windows_callback, result)
            
#             if result:
#                 hwnd = result[0]
#                 try:
#                     win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
#                     return f"Sent close command to window: {full_name}"
#                 except Exception as e:
#                     return f"Error while trying to close window {full_name}: {str(e)}"
#             else:
#                 return f"Found window in list, but couldn't interact with it: {full_name}"
#         else:
#             return f"Multiple matching windows found: {', '.join(matching_windows)}. Please be more specific."
#     else:
#         return f"No windows found matching: {window_name}. Available windows: {', '.join(list_windows())}"

# def execute_ui_action(action, params):
#     if action == "close_window":
#         return close_window(params.get("window_name", ""))
#     elif action == "list_windows":
#         windows = list_windows()
#         if windows:
#             return "Open windows:\n" + "\n".join(windows)
#         else:
#             return "No windows found. This might be due to permission issues or system configuration."
#     else:
#         return f"Unknown action: {action}"

# def process_command(command, max_retries=3):
#     prompt = f"""
#     Given the user command: "{command}"
#     Generate a JSON response with the appropriate UI action and parameters.
#     Possible actions are:
#     1. close_window: Requires a "window_name" parameter
#     2. list_windows: No parameters required
#     3. no_action: Use this if no UI action is needed
#     Example response format:
#     {{"action": "close_window", "params": {{"window_name": "Firefox"}}}}
#     For listing windows or when window name is not specified:
#     {{"action": "list_windows"}}
#     For greetings or non-UI commands, use:
#     {{"action": "no_action", "response": "Hello! How can I assist you with UI automation today?"}}
#     """
    
#     for attempt in range(max_retries):
#         try:
#             response = model.generate_content(prompt)
            
#             json_match = re.search(r'```json\s*(.*?)\s*```', response.text, re.DOTALL)
#             if json_match:
#                 json_str = json_match.group(1)
#             else:
#                 json_str = response.text
            
#             action_data = json.loads(json_str)
            
#             if not isinstance(action_data, dict):
#                 return f"Invalid response format. Expected a dictionary, got: {type(action_data)}"
            
#             if "action" not in action_data:
#                 return f"Invalid response from AI model. Missing 'action' key. Response: {action_data}"
            
#             if action_data["action"] == "no_action":
#                 return action_data.get("response", "No action needed")
            
#             result = execute_ui_action(action_data["action"], action_data.get("params", {}))
#             return result
#         except Exception as e:
#             if attempt < max_retries - 1:
#                 print(f"An error occurred: {str(e)}. Retrying in 5 seconds...")
#                 time.sleep(5)
#             else:
#                 return f"An error occurred after {max_retries} attempts: {str(e)}"

# def main():
#     while True:
#         command = input("Enter a command (or 'quit' to exit): ")
#         if command.lower() == 'quit':
#             break
#         result = process_command(command)
#         print(result)

# if __name__ == "__main__":
#     main()


import win32gui
import win32process
import win32con
import psutil

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

# Example usage
if __name__ == "__main__":
    window_name = "notepad"  # Replace this with the partial name of the window you want to close
    result = close_window_function(window_name)
    print(result)