# Gembot

Gembot is your ultimate productivity companion, designed to revolutionize the way you interact with your computer. With cutting-edge voice command automation and a user-friendly interface, Gembot takes the hassle out of everyday tasks, empowering you to focus on what truly matters.

## Video

https://github.com/user-attachments/assets/738d42c1-931c-41a5-b37a-3dd5e748e630


## Introduction

Gembot was meticulously crafted over a span of two months for Windows users who demand efficiency and speed in their daily workflows. Whether you're a developer, a business professional, or a casual user, Gembot has something to offer, making it an indispensable tool on your desktop

## Key Features

- **Opening Applications**: Seamlessly launch any application on your system with a single command.
- **Installing Applications**: Automate the entire installation process for new software.
- **Generating Code**: Create clean, efficient code snippets in various programming languages.
- **Document Creation**: Instantly generate polished Word documents and PowerPoint presentations.
- **File Management**: Effortlessly manage your files through voice commands.
- **Voice Command Control**: Control your computer with voice commands.
- **Python Code Execution**: Run Python scripts directly from Gembot.
- **Voice-Based Activation**: Activate Gembot by saying "Gemini".
- **Browser Navigation**: Control your web browser with voice commands.
- **Blind Mode**: Enables visually impaired users to interact with the application effortlessly.
- **Screen Reader**: Enables User's to Understand what Apps and Data is opened on the Screen.

## Installation

Follow these steps to install and set up Gembot:

1. **Install Requirements**:
```bash
pip install -r requirements.txt
```

2. **Install torch**:
```bash
pip install torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cpu 
```
Install this version of torch as newer version is incompatible with newer python version.

3. **Setup Dart**:
- Download and install the Dart SDK from the [official Dart website](https://dart.dev/get-dart).
- Add Dart to your system's PATH.
- Verify the installation:
```
dart --version
```

4. **Create .env**:
- Create .env file in root directory of Project.
- Set your Gemini Api Key as API_KEY="your api key".
- Save .env.
```
API_KEY="your api key"
```

5. **Run the Flutter App**:
```bash
flutter pub get
flutter run
```
## Useful Prompts

Here are some practical examples of how you can use Gembot:

- **Open Applications**: 
  - "Open Chrome."
  - "Start Visual Studio Code."
  - "Open PowerPoint."

- **What's on my Screen**: 
  - "What is the Content of Chrome on my Screen?"
  - "What's on my Screen?"
  - "Which App can Perform Code Editing on my Screen"

- **Browsing the Web**: 
  - "Open YouTube in Chrome."
  - "Open Amazon.in in Chrome"

- **File Management**: 
  - "Create a new folder in Documents named 'Gembot Projects'."

- **Document Creation**:
  - "Generate a Word document with an essay on wildlife."
  - "Create a PowerPoint presentation on climate change."

- **Code Generation**:
  - "Generate a Python code for prime numbers from 1 to 100."
  - "Write a Java code snippet to calculate the factorial of a number."

- **Software Installation**:
  - "Install Zoom."
  - "Install Notepad++"

- **Voice Interaction**:
  - "I am Blind" (to interact with TTS).
  - "Gemini" (Keyword to Start Listening)

## Technology Stack

Gembot leverages the power of **Gemini** for interpreting commands and **pywinauto** for executing actions, creating a powerful synergy that makes Gembot both powerful and intuitive.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any problems or have any questions, please open an issue in this repository.

---

Gembot isn't just another tool; it's the next big thing in desktop automation, designed to make your digital life smoother, faster, and more enjoyable. With features like Blind Mode and powerful voice command capabilities, Gembot is committed to being inclusive, making technology accessible to everyone
