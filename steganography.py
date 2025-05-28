# Implement image-to-image steganography to embed a watermark (image)

import cv2
import matplotlib.pyplot as plt
import numpy as np

# Watermark Embedder
# 1. Leveraging key point detection using the SIFT algorithm
# UI: To embed a watermark into an image. Input and output are images

# 1.1 Input images
# Open an image to serve as the carrier for watermark
# The image should have enough complexity to hide the watermark without visual distortion
# Choose a smaller image to be hidden in the cover image
def input_images(carrier_path, watermark_path):
    # Read Image
    carrier_img = cv2.imread(carrier_path)
    watermark_img = cv2.imread(watermark_path)

    if carrier_img is None:
        raise FileNotFoundError(f"Carrier image is not found")
    if watermark_img is None:
        raise FileNotFoundError(f"Watermark image is not found")
    
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
def keypoint_detection(carrier_img_gray):
    sift = cv2.SIFT_create()
    kp, des = sift.detectAndCompute(carrier_img_gray, None)

    print(f"There are {len(kp)} keypoints")

    # N keypoints (Top 3 big points)
    n_kp = sorted(kp, key=lambda x: -x.size)
    top20_kp = n_kp[:20]
    top20_des = des[:20]

    # Draw keypoints on the grayscale image
    sift_image = cv2.drawKeypoints(carrier_img_gray, top20_kp, None, flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    cv2.imwrite("Top20 key point detection.png", sift_image)
    print("Top 20 Key points detected")

    # Extract the coordinates of keypoints
    coordinates = cv2.KeyPoint_convert(top20_kp)
    print(coordinates)

    # Extract feature descriptors of N keypoints
    print(top20_des)

    return top20_kp, top20_des


# 1.4. Watermark Encoding and Embedding
# Prepare the watermark image for embedding
## Depending on its size and the number of keypoints, adjust the watermark accordingly
# Embed the watermark by subtly modifying the pixel values at the detected keypoints in the cover image using LSB
# Ensure the watermark remains imperceptible to the human eye but retrievable with the correct method
def watermark_encoding(watermark_img_gray, pixel_size=3):
    # Resize if watermark is too big
    height, width = watermark_img_gray.shape

    if height > pixel_size or width > pixel_size:
        print("Resize watermark because it is too big")
        watermark_img_gray = cv2.resize(watermark_img_gray, (pixel_size, pixel_size), interpolation=cv2.INTER_AREA)

    data_watermark = np.array(watermark_img_gray)
    print(data_watermark)

    # Convert to binary format
    _, binary = cv2.threshold(data_watermark, 127, 1, cv2.THRESH_BINARY)

    # To 1D
    watermark_bits = binary.flatten().tolist()
    print("watermark encoded")
    
    return watermark_bits

def watermark_embedding(carrier_img, top20_kp, watermark_bits, watermark_height, watermark_width):
    embedded_img = carrier_img.copy()
    embedded_img_height, embedded_img_width, _ = embedded_img.shape

    x = watermark_width // 2
    y = watermark_height // 2

    for kp in top20_kp:
        center_x = int(kp.pt[0])
        center_y = int(kp.pt[1])
        bit_index = 0

        for dy in range(-y, -y + watermark_height):
            for dx in range(-x, -x + watermark_width):
                coordinates_x = center_x + dx
                coordinates_y = center_y + dy

                if 0 <= coordinates_x < embedded_img_width and 0 <= coordinates_y < embedded_img_height and bit_index < len(watermark_bits):
                    # Get Blue channel
                    blue = int(embedded_img[coordinates_y, coordinates_x, 0])

                    lsb = blue & 1
                    bit = watermark_bits[bit_index]

                    if lsb != bit:
                        lsb_reset = blue & 0xFE

                        # Put watermark bit
                        embedded_img[coordinates_y, coordinates_x, 0] = lsb_reset | bit
                    
                    bit_index += 1

    return embedded_img


# Watermark Recovery
def watermark_recovery(embedded_img, top20_kp, watermark_width, watermark_height):
    # 2.1 Reapply the SIFT algorithm to the modified image(with the watermark embedded)
    embedded_img_gray = cv2.cvtColor(embedded_img, cv2.COLOR_BGR2GRAY)
    print("Convert the embedded image to grayscale")

    sift = cv2.SIFT_create()
    kp, des = sift.detectAndCompute(embedded_img_gray, None)
    top_kp = sorted(kp, key=lambda x: -x.size)[:len(top20_kp)]

    # 2.2 Detect the same set of keypoints from the modified image
    embedded_img_height, embedded_img_width, _ = embedded_img.shape
    recover = []

    x = watermark_width // 2
    y = watermark_height // 2

    for index, kp in enumerate(top_kp):
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

        recover.append(recovery_bits)        
                    
    return recover


# Tampering Detector
# Build a tool to upload an image and determine if it has been tampered with by comparing the watermark's consistency
# This tool should test for common tampering techniques(cropping, resizing, or rotating)
# And flag any discrepancies in the wateramrk extraction process
def tampering_detector(tampered_img, watermark_bits, top20_kp, watermark_height, watermark_width, threshold=0.9):
    watermark_recovery_list = watermark_recovery(tampered_img, top20_kp, watermark_width, watermark_height)

    if not watermark_recovery_list or len(watermark_recovery_list[0]) == 0:
        return "Tampering is detected"
    
    recovered_bits = watermark_recovery_list[0]
    compare = min(len(watermark_bits), len(recovered_bits))

    matching_num = sum(1 for i in range(compare) if watermark_bits[i] == recovered_bits[i])
    matching = matching_num / compare

    if matching >= threshold:
        print("Image is authentic")
        return "Authentic"
    else:
        print("Image is tampered")
        return "Tampered"
