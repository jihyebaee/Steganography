import os
import cv2

from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename

# Importing my function
from steganography import input_images, preprocessing, keypoint_detection, watermark_encoding, watermark_embedding, watermark_recovery, tampering_detector

UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Generate flask application
app = Flask(__name__)
app.secret_key = "super secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Checks if an extension is valid
def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    result = ''
    carrier_imgfile = None
    watermark_imgfile = None
    embedded_img = None

    if request.method == 'POST':
        option = request.form.get('option')

        # Watermark Embedder: to embed a watermark into an image 
        # Input and output are images
        if option == 'watermarkEmbedder':
            # Check if the post request has the file part
            if 'carrier' not in request.files:
                flash('No carrier file part')
                return redirect(request.url)
            if 'watermark' not in request.files:
                flash('No watermark file part')
                return redirect(request.url)

            carrier = request.files['carrier']
            watermark = request.files['watermark']

            # If the user does not select the file,
            # browser submits an empty file without a filename.
            if carrier.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if watermark.filename == '':
                flash('No selected file')
                return redirect(request.url)
            
            carrier_filename = "carrier.png"
            watermark_filename = "watermark.png"
            carrier_path = os.path.join(app.config['UPLOAD_FOLDER'], carrier_filename)
            watermark_path = os.path.join(app.config['UPLOAD_FOLDER'], watermark_filename)
   
            carrier.save(carrier_path)
            watermark.save(watermark_path)

            carrier_img, watermark_img = input_images(carrier_path, watermark_path)
            flash("Images uploaded")

            carrier_img_gray, watermark_img_gray = preprocessing(carrier_img, watermark_img)
            top20_kp, _ = keypoint_detection(carrier_img_gray)
            watermark_bits = watermark_encoding(watermark_img_gray, pixel_size=3)
            watermark_height, watermark_width = watermark_img_gray.shape
            embedded = watermark_embedding(carrier_img, top20_kp, watermark_bits, watermark_height, watermark_width)
            
            embedded_img = "embedded.png"
            cv2.imwrite(os.path.join('static', embedded_img), embedded)
            result = "Watermark successfully embedded"

            carrier_imgfile = carrier_filename
            watermark_imgfile = watermark_filename

        # Authenticity Verifier: to verify if an image contains the watermark
        # Given an image, it should return “Yes” or “No”
        elif option == 'Verifier':
            # Check if the post request has the file part
            if 'verifier' not in request.files:
                flash('No verifier file part')
                return redirect(request.url)

            verifier = request.files['verifier']

            if verifier.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if watermark.filename == '':
                flash('No selected file')
                return redirect(request.url)

            verifier_filename = "verifier.png"
            watermark_filename = "watermark.png"
            verifier_path = os.path.join(app.config['UPLOAD_FOLDER'], verifier_filename)
            watermark_path = os.path.join(app.config['UPLOAD_FOLDER'], watermark_filename)

            verifier.save(verifier_path)
            watermark.save(watermark_path)

            embedded_img, watermark_img = input_images(verifier_path, watermark_path)
            flash("Images uploaded")

            embedded_img_gray, watermark_img_gray = preprocessing(embedded_img, watermark_img)
            top20_kp, _ = keypoint_detection(embedded_img_gray)
            watermark_bits = watermark_encoding(watermark_img_gray, pixel_size=3)
            watermark_height, watermark_width = watermark_img_gray.shape

            recovery = watermark_recovery(embedded_img, top20_kp, watermark_width, watermark_height)
            recovery_bits = recovery[0] if recovery else []
            matching = sum([a == b for a, b in zip(watermark_bits, recovery_bits)]) / len(watermark_bits) if watermark_bits else 0

            result = "Yes. Watermark detected" if matching > 0.9 else "No. Watermark is not detected"

        # Tampering Detector: to detect whether an image has been altered based on watermark consistency
        # Given an input image, the tool should return "Yes" if tampered is detected and "No" otherwise
        # If tampered is detected, the output shold include the image marked with keypoints
        # that do not match the expected watermark
        # This is particularly useful for identifying specific manipulations or image composites.

        return render_template("index.html", result = result, result_img=embedded_img, 
                               carrier_img=carrier_imgfile, watermark_img=watermark_imgfile)

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(debug=True)

