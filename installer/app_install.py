import subprocess
import sys
import os
import json
import winreg
import argparse
from fuzzywuzzy import fuzz

def get_powershell_path():
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

def run_powershell_script_as_admin(script_path, app_name):
    if sys.platform != 'win32':
        raise OSError("This function is only supported on Windows.")

    powershell_path = get_powershell_path()
    
    args = f'-ExecutionPolicy Bypass -File "{script_path}" -app "{app_name}"'
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
            return False
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the PowerShell script: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False

def get_application_list():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, 'package_list.json')
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        return [app['Name'] for app in data]
    except FileNotFoundError:
        print(f"Error: package_list.json not found at {json_path}")
        return []
    except json.JSONDecodeError:
        print(f"Error: package_list.json is not a valid JSON file")
        return []

def find_closest_match(user_input, app_list):
    best_match = None
    best_ratio = 0
    for app in app_list:
        ratio = fuzz.partial_ratio(user_input.lower(), app.lower())
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = app
    return best_match if best_ratio >= 70 else None

def main():
    parser = argparse.ArgumentParser(description='Install an application using PowerShell script.')
    parser.add_argument('--app', help='Name of the application to install')
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, 'install_programs.ps1')
    
    if not os.path.exists(script_path):
        print(f"Error: install_programs.ps1 not found at {script_path}")
        return

    app_list = get_application_list()
    if not app_list:
        return

    if args.app:
        user_input = args.app
    else:
        print("Available applications:")
        for app in app_list:
            print(f"- {app}")
        user_input = input("\nEnter the name of the application you want to install: ")

    closest_match = find_closest_match(user_input, app_list)
    
    if closest_match:
        print(f"Closest match found: {closest_match}")
        confirm = input(f"Do you want to install {closest_match}? (y/n): ")
        
        if confirm.lower() == 'y':
            print(f"Starting installation of {closest_match}...")
            success = run_powershell_script_as_admin(script_path, closest_match)
            if success==0:
                print(f"{closest_match} installation process completed.")
            else:
                print(f"Failed to install {closest_match}. Please check the PowerShell script and try again.")
        else:
            print("Installation cancelled.")
    else:
        print(f"No close match found for '{user_input}'. Please check the application name and try again.")

if __name__ == "__main__":
    main()
