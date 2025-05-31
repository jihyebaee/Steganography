# Steganography

Computer Vision assignment for COM31006 that uses the SIFT algorithm and Least Significant Bit(LSB) embedding to imperceptibly hide a watermark inside an image

## Features
1. Watermark Embedder: Hides a watermark image inside a carrier image
2. Authenticity Verifier: Check whether the expected watermark is present
3. Tampering Detector: Identifies whether an image has been modified (e.g. cropped, rotated)

## Installation
1. Clone the repository
   ```
   git clone https://github.com/jihyebaee/Steganography.git
   cd Steganography
   ```
3. Create virtual environment
   ```
   python3 -m venv .venv
   . .venv/bin/activate (macOS)
   ```
5. Install packages
   ```
   pip install opencv-python
   pip install flask
   pip install --upgrade pip
   pip install numpy
   pip install matplotlib
   ```

## Running the App
This assignment uses Flask to serve a simple web interface
1. Start the Flask server
   ```
   flask run
   ```
3. Open your browser and visit
   ```
   http://127.0.0.1:5000/
   ```

## How to Use
### 1. Watermark Embedder
- Upload a carrier image
- Upload a small watermark image
- The embedded image will be displayed and can be downloaded

### 2. Authenticity Verifier / Tampering Detector
- Upload the image you want to test
- Click **Submit** to view the verification or tampering detection result
   
## Sample images
Sample carrier and watermark images are provided in the `/static` folder

### Demonstration Video
https://youtu.be/g64twzKrMCM
