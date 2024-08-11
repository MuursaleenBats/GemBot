from AppOpener import open as app_open
import winapps
import subprocess
from fuzzywuzzy import process

def get_installed_apps():
    """
    Get a list of installed applications using winapps.
    
    Returns:
        list: A list of installed application names.
    """
    apps = list(winapps.list_installed())
    app_names = [app.name for app in apps]
    return app_names

def suggest_apps(app_name, app_names, threshold=70):
    """
    Suggest similar application names based on fuzzy matching.
    
    Args:
        app_name (str): The name of the application to match.
        app_names (list): A list of installed application names.
        threshold (int): The matching threshold (default is 70).
    
    Returns:
        list: A list of suggested application names.
    """
    suggestions = process.extract(app_name, app_names, limit=5)
    return [suggestion for suggestion, score in suggestions if score >= threshold]

def open_app(app_names):
    """
    Attempts to open multiple applications using the appopener library.
    Falls back to winapps if appopener fails, with suggestions for misspelled names.
    
    Args:
        app_names (list): The names of the applications to open.

    Returns:
        None
    """
    installed_apps = get_installed_apps()
    
    for app_name in app_names:
        try:
            # Attempt to open the app using appopener with match_closest=True
            app_open(app_name, match_closest=True)
            print(f"Opening {app_name}...")
        except Exception as e:
            print(f"appopener failed to open {app_name}: {e}")
            # Suggest similar applications if the name is misspelled
            suggestions = suggest_apps(app_name, installed_apps)
            
            if suggestions:
                print(f"Application '{app_name}' not found. Did you mean one of these?")
                for suggestion in suggestions:
                    print(f" - {suggestion}")
                suggested_name = suggestions[0]
                user_confirmation = input(f"Do you want to open '{suggested_name}' instead? (yes/no): ").strip().lower()
                if user_confirmation == 'yes':
                    open_app([suggested_name])
            else:
                # Fallback to using winapps if no suggestions are found
                print("Attempting to open the app using winapps...")
                app = list(winapps.search_installed(app_name))

                if app:
                    # Use the first match if multiple apps have similar names
                    app_info = app[0]
                    uninstall_string = app_info.uninstall_string

                    # Try to open the app using uninstall string
                    try:
                        subprocess.Popen(uninstall_string)
                        print(f"Opening {app_info.name} using uninstall string...")
                    except Exception as e:
                        print(f"Error opening {app_info.name} using uninstall string: {e}")
                else:
                    print(f"Application '{app_name}' not found. Please make sure the name is correct.")

def install_app_with_choco(app_name):
    """
    Installs an application using Chocolatey package manager.
    
    Args:
        app_name (str): The name of the application to install.

    Returns:
        bool: True if the installation was successful, False otherwise.
    """
    try:
        # Use subprocess to run the Chocolatey installation command
        result = subprocess.run(["choco", "install", app_name, "-y"], check=True)
        if result.returncode == 0:
            print(f"Successfully installed {app_name} with Chocolatey.")
            return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing {app_name} with Chocolatey: {e}")
    except FileNotFoundError:
        print("Chocolatey is not installed. Please install Chocolatey first.")
    
    return False

def install_app_with_winget(app_name):
    """
    Installs an application using winget package manager from the Microsoft Store.
    
    Args:
        app_name (str): The name of the application to install.

    Returns:
        bool: True if the installation was successful, False otherwise.
    """
    try:
        # Use subprocess to run the winget installation command
        result = subprocess.run(["winget", "install", "--name", app_name, "--silent", "--accept-package-agreements", "--accept-source-agreements"], check=True)
        if result.returncode == 0:
            print(f"Successfully installed {app_name} with winget.")
            return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing {app_name} with winget: {e}")
    except FileNotFoundError:
        print("winget is not installed. Please install winget first.")
    
    return False

def install_app(app_name):
    """
    Attempts to install an application using winget first and falls back to Chocolatey if winget fails.
    
    Args:
        app_name (str): The name of the application to install.

    Returns:
        None
    """
    if not install_app_with_winget(app_name):
        print(f"Trying to install {app_name} with Chocolatey...")
        install_app_with_choco(app_name)

if __name__ == "__main__":
    action = input("Do you want to open or install an app? (open/install): ").strip().lower()
    app_names = input("Enter the names of the apps (comma separated): ").strip().split(',')
    app_names = [app_name.strip() for app_name in app_names]
    
    if action == "open":
        open_app(app_names)
    elif action == "install":
        for app_name in app_names:
            install_app(app_name)
    else:
        print("Invalid action. Please choose 'open' or 'install'.")
