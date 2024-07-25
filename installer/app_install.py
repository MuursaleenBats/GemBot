# installer/app_install.py

import subprocess
import sys
import os
import json
import winreg
from fuzzywuzzy import fuzz

class AppInstaller:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.script_path = os.path.join(self.script_dir, 'install_programs.ps1')
        self.json_path = os.path.join(self.script_dir, 'package_list.json')
    
    def get_powershell_path(self):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\PowerShell\1\ShellIds\Microsoft.PowerShell") as key:
                return winreg.QueryValueEx(key, "Path")[0]
        except WindowsError:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\PowerShell\3\ShellIds\Microsoft.PowerShell") as key:
                    return winreg.QueryValueEx(key, "Path")[0]
            except WindowsError:
                print("Warning: Could not find PowerShell path in registry. Using default path.")
                return r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"

    def run_powershell_script_as_admin(self, app_name):
        if sys.platform != 'win32':
            raise OSError("This function is only supported on Windows.")

        powershell_path = self.get_powershell_path()
        
        args = f'-ExecutionPolicy Bypass -File "{self.script_path}" -app "{app_name}"'
        args = args.replace('"', '`"')
        
        command = f'Start-Process "{powershell_path}" -Verb RunAs -ArgumentList "{args}" -Wait'
        
        try:
            print("Attempting to run PowerShell script with elevated privileges...")
            result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True)
            print("PowerShell script execution completed.")
            if result.stderr:
                print(f"stderr: {result.stderr}")
            elif "Microsoft Store transfer" in result.stdout:
                print("Microsoft Store was opened for manual installation.")
                return True
            elif "installed successfully" in result.stdout:
                print(f"{app_name} was installed successfully.")
                return True
            else:
                print(f"Installation of {app_name} may be transferred. Please check the output.")
                return True
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while running the PowerShell script: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            return False

    def get_application_list(self):
        try:
            with open(self.json_path, 'r') as f:
                data = json.load(f)
            return [app['Name'] for app in data]
        except FileNotFoundError:
            print(f"Error: package_list.json not found at {self.json_path}")
            return []
        except json.JSONDecodeError:
            print(f"Error: package_list.json is not a valid JSON file")
            return []

    def find_closest_match(self, user_input):
        app_list = self.get_application_list()
        best_match = None
        best_ratio = 0
        for app in app_list:
            ratio = fuzz.partial_ratio(user_input.lower(), app.lower())
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = app
        return best_match if best_ratio >= 70 else None

    def install_app(self, user_input):
        if not os.path.exists(self.script_path):
            return f"Error: install_programs.ps1 not found at {self.script_path}"

        app_list = self.get_application_list()
        if not app_list:
            return "No applications available for installation."

        closest_match = self.find_closest_match(user_input)
        
        if closest_match:
            success = self.run_powershell_script_as_admin(closest_match)
            if success:
                return f"{closest_match} installation process completed."
            else:
                return f"Failed to install {closest_match}. Please check the PowerShell script and try again."
        else:
            return f"No close match found for '{user_input}'. Please check the application name and try again."
