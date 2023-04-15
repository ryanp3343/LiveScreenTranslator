# LiveScreenTranslator

  
## Description

LiveScreenTranslator is an application that helps users translate text on their screen in real-time. It uses advanced OCR (Optical Character Recognition) and machine translation technologies to provide accurate and quick translations. This tool is useful for people who interact with content in multiple languages and need a seamless translation experience.

Key features include:
- Real-time translation on the screen. 
-  Support for multiple monitors. 
- Option to save translated text to a file. 
- Text-to-speech functionality for an enhanced user experience.

  

## Table of Contents

  

- [Prerequisites](#prerequisites)

- [Installation](#installation)

- [Usage](#usage)

- [Troubleshooting](#troubleshooting)

- [Contributing](#contributing)

- [License](#license)

- [Contact](#contact)

  

## Prerequisites

  

Before installing LiveScreenTranslator, make sure to download and install the following prerequisite:

1. [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) - Tesseract OCR is an Optical Character Recognition engine that LiveScreenTranslator relies on for text recognition. Follow the instructions on the linked page to download and install the appropriate version for your operating system.

**Note:** When installing make sure to click additional script data and additional language data

![installation ](https://user-images.githubusercontent.com/72015041/232171999-2f084e48-8d52-4002-911f-0084bfa8d87e.png)

**Note:** When installing Tesseract OCR, please ensure it is installed to the following path: 'C:\Program Files\Tesseract-OCR'

![installation2](https://user-images.githubusercontent.com/72015041/232172279-4d493deb-95be-4d96-ba80-d2c7f1892f39.png)

## Installation

There are two ways to install and run LiveScreenTranslator:

### Method 1: Download the Release

1. Download the latest release of LiveScreenTranslator from the [Releases page](https://github.com/ryanp3343/LiveScreenTranslator/releases). You can choose between the `.zip` and `.tar.gz` formats.
2. Extract the downloaded archive to a location of your choice.
3. Navigate to the extracted folder and run the `main.exe` file to start the application.

### Method 2: Clone the Repository

1. Clone the LiveScreenTranslator repository to your local machine using the following command:

    ```
    https://github.com/ryanp3343/LiveScreenTranslator.git`	
    ```

2. Navigate to the cloned repository folder:

    ```
    cd LiveScreenTranslator
    ```

3. Install the required dependencies using the `requirements.txt` file:

    ```
    pip install -r requirements.txt
    ```

4. Run the `main.py` file to start the application:

    ```
    python main.py
    ```

  

## Usage

To use LiveScreenTranslator, follow these steps:

1. Launch the LiveScreenTranslator application.

![usage](https://user-images.githubusercontent.com/72015041/232173678-54159626-7522-4513-8456-3a7a8f7174e0.png)

2. Choose the source (translate from) and target (translate to) languages using the provided dropdown boxes.

3. If applicable, select the monitor you want to run the application on from the monitor selection dropdown box. The application will show a preview image of each of your monitors.

4. Enable Text-to-Speech (TTS) or the "Save text to file" option as desired:
   - If you enable the "Save text to file" option, you'll be prompted to choose a file name and location to save the translated text.
 
5. Click the "Select Area" button. A transparent screen will appear over the selected monitor.

6. Click and drag to define the area on the screen you want to capture for translation.

<img width="1214" alt="usage2" src="https://user-images.githubusercontent.com/72015041/232173877-2790a8ba-da68-4561-85f1-4150e0b4723a.png">

7. Click the "Start Capturing Screen" button to begin real-time translation.

The translated text will appear on your screen over the selected area. You can adjust the source and target languages or change the capture area as needed while using the application.



  

## Troubleshooting

If you encounter any issues while installing or using LiveScreenTranslator, please check the following common solutions:

1. **Tesseract OCR not found or not working**: Make sure Tesseract OCR is installed at the correct path: `C:\Program Files\Tesseract-OCR\tesseract.exe`. If you've installed it to a different location, update your application settings to point to the correct path.

2. **Application not capturing the selected area**: Ensure that the selected monitor and capture area are correctly set. You can adjust the capture area by clicking the "Select Area" button and redefining the region you want to capture.

3. **Text-to-Speech not working**: Check your system's audio settings and ensure that your speakers or headphones are properly connected and functioning. Make sure the Text-to-Speech option is enabled in the application settings.

4. **Translation not accurate**: Translation quality may vary depending on the clarity and formatting of the text being captured. Try adjusting the capture area or improving the visibility of the text on your screen.

5. **"Save text to file" not working**: Ensure that you have provided a valid file name and location when prompted. Check if the application has the necessary permissions to write files to the selected location.

If you still experience issues or need additional assistance, please [create an issue](https://github.com/ryanp3343/LiveScreenTranslator/issues) on the GitHub repository.


## License

  

LiveScreenTranslator is released under the [MIT License](LICENSE). For more information, please refer to the [LICENSE](LICENSE) file in the repository.

  

## Contact

  

For any questions or inquiries, please feel free to reach out:


- [Your Name](mailto:ryan_puertas@yahoo.com)

- [GitHub Profile](https://github.com/ryanp3343)
