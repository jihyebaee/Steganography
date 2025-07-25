# Implement image-to-image steganography to embed a watermark (image)

import cv2
import os
import matplotlib.pyplot as plt
import numpy as np

# Watermark Embedder
# 1. Leveraging key point detection using the SIFT algorithm
# UI: To embed a watermark into an image. Input and output are images

# 1.1 Input images
# Open an image to serve as the carrier for watermark
# The image should have enough complexity to hide the watermark without visual distortion
# Choose a smaller image to be hidden in the cover image
def input_images(carrier_path, watermark_path, pixel_size=3):
    # Change to png
    def png(image_path):
        image = cv2.imread(image_path)

        if image is None:
            raise FileNotFoundError(f"Image is not found")
        
        base, _ = os.path.splitext(image_path)
        png_path = base + ".png"
        cv2.imwrite(png_path, image)
        return png_path
    
    if not carrier_path.lower().endswith('.png'):
        carrier_path = png(carrier_path)
    if not watermark_path.lower().endswith('.png'):
        watermark_path = png(watermark_path)

    # Read Image
    carrier_img = cv2.imread(carrier_path)
    watermark_img = cv2.imread(watermark_path)

    if carrier_img is None:
        raise FileNotFoundError(f"Carrier image is not found")
    if watermark_img is None:
        raise FileNotFoundError(f"Watermark image is not found")
    
    # Resize the watermark
    if watermark_img.shape != (pixel_size, pixel_size):
        print("Resize watermark because it is too big")
        watermark_img = cv2.resize(watermark_img, (pixel_size, pixel_size), interpolation=cv2.INTER_NEAREST)

    return carrier_img, watermark_img


# 1.2. Preprocessing
# Ensure both images are the same format (preferably .png or .tif)
# Convert the carrier image to grayscale for easier SIFT point detection.
def preprocessing(carrier_img, watermark_img):
    # Converting to grayscale
    carrier_img_gray = cv2.cvtColor(carrier_img, cv2.COLOR_BGR2GRAY)
    print("Convert the carrier image to grayscale")
    watermark_img_gray = cv2.cvtColor(watermark_img, cv2.COLOR_BGR2GRAY)
    print("Convert the watermark image to grayscale")

    return carrier_img_gray, watermark_img_gray


# 1.3. Key point detection with SIFT
# Apply the SIFT algorithm to detect keypoints in the cover image (Carrier image)
# Extract the coordinates and feature descriptors of N keypoints
# to serve as the locations for embedding the watermark.
def keypoint_detection(carrier_img_gray, min_distance=None):
    sift = cv2.SIFT_create()
    kp, _ = sift.detectAndCompute(carrier_img_gray, None)

    print(f"There are {len(kp)} keypoints")

    # Find biggest keypoint size
    kp_size = max([k.size for k in kp]) if kp else 0
    kp_min_distance = int(kp_size * 0.6)

    if min_distance is None:
        min_distance = kp_min_distance

    n_kp_des = sorted(kp, key=lambda x: -x.size)

    top_kp = []

    for current_kp in n_kp_des:
        if all(np.linalg.norm(np.array(current_kp.pt) - np.array(existing_kp.pt)) >= min_distance for existing_kp in top_kp):
            top_kp.append(current_kp)

    # Draw keypoints on the grayscale image
    sift_image = cv2.drawKeypoints(carrier_img_gray, top_kp, None, flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    cv2.imwrite("key point detection.png", sift_image)
    print("Key points detected")

    # Extract the coordinates of keypoints
    coordinates = cv2.KeyPoint_convert(top_kp)
    print(coordinates)

    return top_kp


# 1.4. Watermark Encoding and Embedding
# Prepare the watermark image for embedding
## Depending on its size and the number of keypoints, adjust the watermark accordingly
# Embed the watermark by subtly modifying the pixel values at the detected keypoints in the cover image using LSB
# Ensure the watermark remains imperceptible to the human eye but retrievable with the correct method
def watermark_encoding(watermark_img_gray, pixel_size=3):
    # Convert to binary format
    _, binary = cv2.threshold(watermark_img_gray, 127, 1, cv2.THRESH_BINARY)

    # To 1D
    watermark_bits = binary.flatten().tolist()
    print("watermark encoded")
    
    return watermark_bits

def rotate_watermark(watermark_img_gray, angle, pixel_size=3):
    # Convert to binary format
    _, binary = cv2.threshold(watermark_img_gray, 127, 1, cv2.THRESH_BINARY)

    resize = cv2.resize(binary.astype(np.uint8), (pixel_size, pixel_size), interpolation=cv2.INTER_NEAREST)
    center = (pixel_size // 2.0, pixel_size // 2.0)
    rotate = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(resize, rotate, (pixel_size, pixel_size), flags=cv2.INTER_NEAREST)

    return rotated.flatten().tolist()

def rotate_watermark_from_position(kp, width, height):
    x, y = kp.pt

    # Top left
    if x < width // 2 and y < height // 2:
        return 0
    # Top right
    elif x >= width // 2 and y < height // 2:
        return 45
    # Bottom right
    elif x >= width // 2 and y >= height // 2:
        return 90
    # Button left
    else:
        return 180

def watermark_embedding(carrier_img, top_kp, watermark_bits, watermark_height, watermark_width, watermark_img_gray):
    embedded_img = carrier_img.copy()
    embedded_img_height, embedded_img_width, _ = embedded_img.shape

    x = watermark_width // 2
    y = watermark_height // 2

    for kp in top_kp:
        angle = rotate_watermark_from_position(kp, embedded_img_width, embedded_img_height)
        rotated_watermark_bits = rotate_watermark(watermark_img_gray, angle, pixel_size=watermark_width)

        center_x = int(kp.pt[0])
        center_y = int(kp.pt[1])
        bit_index = 0

        for dy in range(-y, -y + watermark_height):
            for dx in range(-x, -x + watermark_width):
                coordinates_x = center_x + dx
                coordinates_y = center_y + dy

                if (0 <= coordinates_x < embedded_img_width and 
                    0 <= coordinates_y < embedded_img_height and 
                    bit_index < len(rotated_watermark_bits)):

                    # Get Blue channel
                    blue = int(embedded_img[coordinates_y, coordinates_x, 0])

                    lsb = blue & 1
                    bit = rotated_watermark_bits[bit_index]

                    if lsb != bit:
                        lsb_reset = blue & 0xFE

                        # Put watermark bit
                        embedded_img[coordinates_y, coordinates_x, 0] = lsb_reset | bit
                    
                    bit_index += 1

    return embedded_img


# Watermark Recovery
def watermark_recovery(embedded_img, top_kp, watermark_img_gray, watermark_width, watermark_height):
    # 2.1 Reapply the SIFT algorithm to the modified image(with the watermark embedded)
    embedded_img_gray = cv2.cvtColor(embedded_img, cv2.COLOR_BGR2GRAY)
    print("Convert the embedded image to grayscale")

    sift = cv2.SIFT_create()
    kp, _ = sift.detectAndCompute(embedded_img_gray, None)

    # Find biggest keypoint size
    kp_size = max([k.size for k in kp]) if kp else 0
    kp_min_distance = int(kp_size * 0.6)
    min_distance = kp_min_distance

    n_kp_des = sorted(kp, key=lambda x: -x.size)

    top_kp = []

    for current_kp in n_kp_des:
        if all(np.linalg.norm(np.array(current_kp.pt) - np.array(existing_kp.pt)) >= min_distance for existing_kp in top_kp):
            top_kp.append(current_kp)

    # 2.2 Detect the same set of keypoints from the modified image
    embedded_img_height, embedded_img_width, _ = embedded_img.shape
    recover = []

    x = watermark_width // 2
    y = watermark_height // 2

    for kp in top_kp:
        angle = rotate_watermark_from_position(kp, embedded_img_width, embedded_img_height)
        bits = rotate_watermark(watermark_img_gray, angle, pixel_size=watermark_width)

        recovery_bits = []
        center_x = int(kp.pt[0])
        center_y = int(kp.pt[1])

        for dy in range(-y, y + 1):
            for dx in range(-x, x + 1):
                coordinates_x = center_x + dx
                coordinates_y = center_y + dy

                if 0 <= coordinates_x < embedded_img_width and 0 <= coordinates_y < embedded_img_height:
                    # Get Blue channel
                    blue = int(embedded_img[coordinates_y, coordinates_x, 0])

                    lsb = int(blue) & 1
                    recovery_bits.append(lsb)

        compare = min(len(bits), len(recovery_bits))
        matching = sum(bits[i] == recovery_bits[i] for i in range(compare)) / compare if compare > 0 else 0
        recover.append((angle, matching))
                    
    return recover


# Tampering Detector
# Build a tool to upload an image and determine if it has been tampered with by comparing the watermark's consistency
# This tool should test for common tampering techniques(cropping, resizing, or rotating)
# And flag any discrepancies in the wateramrk extraction process
def tampering_detector(tampered_img, watermark_img_gray, watermark_bits, top_kp, watermark_height, watermark_width, threshold=0.9):
    watermark_recovery = watermark_recovery(tampered_img, top_kp, watermark_img_gray, watermark_width, watermark_height)

    for angle, match in watermark_recovery:
        if match < threshold:
            return "Tampered"
    return "Authentic"