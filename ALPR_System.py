import cv2
import streamlit as st
import numpy as np
import torchvision.transforms as T
import easyocr
from datetime import datetime
import database as db

st.set_page_config(page_title="ALPR System", page_icon="🚗")

st.sidebar.success("Select a page above")

# Load YOLOv4 weights and configuration
net = cv2.dnn.readNetFromDarknet('yolov4-obj.cfg', 'yolov4-obj_6000.weights')

# Get the output layer names
layer_names = net.getLayerNames()
output_layers = [layer_names[i[0] - 1] for i in [net.getUnconnectedOutLayers()]]

# Define the class labels
class_labels = ['license_plate']  # Add your class labels here

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])  # Specify the language(s) for license plate recognition

# Function to perform object detection
def perform_object_detection(image):
    # Convert image to blob
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416), swapRB=True, crop=False)

    # Set the input to the network
    net.setInput(blob)

    # Run the forward pass
    outputs = net.forward(output_layers)

    # Get bounding box coordinates, confidence scores, and class labels
    boxes = []
    confidences = []
    class_ids = []

    for output in outputs:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            if confidence > 0.3:  # Adjust the confidence threshold as needed
                # Scale the bounding box coordinates to the original image size
                height, width, _ = image.shape
                box = detection[0:4] * np.array([width, height, width, height])
                (center_x, center_y, box_width, box_height) = box.astype('int')

                # Calculate the top-left corner of the bounding box
                x = int(center_x - (box_width / 2))
                y = int(center_y - (box_height / 2))

                boxes.append([x, y, int(box_width), int(box_height)])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    # Apply non-maximum suppression to remove redundant overlapping boxes
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

    # Draw bounding boxes on the image
    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]
            label = class_labels[class_ids[i]]
            confidence = confidences[i]

            # Draw bounding box and label
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(image, f'{label}: {confidence:.2f}', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return image

# Function to extract license plate number using EasyOCR
def extract_license_plate_number(image):
    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Perform thresholding to enhance the license plate region
    _, threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Find contours in the thresholded image
    contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Iterate over the contours and find the contour with the largest area
    largest_contour = max(contours, key=cv2.contourArea)

    # Get the bounding rectangle coordinates of the license plate contour
    x, y, w, h = cv2.boundingRect(largest_contour)

    # Crop the license plate region from the image
    plate_image = image[y:y + h, x:x + w]

    # Perform license plate recognition using EasyOCR
    results = reader.readtext(plate_image)

    # Extract license plate number from OCR results
    if results:
        license_plate_number = results[0][1]
    else:
        license_plate_number = 'No license plate number found'

    # Draw bounding box and label on the original image
    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.putText(image, license_plate_number, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return image, license_plate_number

st.title("License Plate Recognition System")

col1, col2, col3, col4, col5 = st.columns([1,1,1,1,3])

with col1:
    start_button = st.button('Open Camera')
with col2:
    close_button = st.button('Close Camera')
with col3:
    capture_button = st.button("Capture")
with col4:
    next_button = st.button('Next')

license_plate_number = ""
captured_image = None
current_time = datetime.now().strftime('%H:%M:%S')
FRAME_WINDOW = st.image([])
camera = cv2.VideoCapture(0)
run = False

if start_button:
    run = True

if next_button:
    run = True

if close_button:
    run = False
    camera.release()

if capture_button:
    #camera = cv2.VideoCapture(0)
    run = False
    while True:
        _, frame = camera.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        captured_image = frame.copy()
        break

    camera.release()

if captured_image is not None:
    # Perform object detection and license plate recognition on the captured image
    output_frame = perform_object_detection(captured_image)
    output_frame, license_plate_number = extract_license_plate_number(captured_image)

    st.image(output_frame)
    st.write("License Plate Number: " + license_plate_number)
    st.write("Time: " + current_time)

    captured_image = None

    if license_plate_number != "No license plate number found":
        formatted_lp = license_plate_number.replace(" ", "").upper()
        db.insert_lpn(formatted_lp, current_time)
    

while run:
    _, frame = camera.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    FRAME_WINDOW.image(frame)
else:
    st.write('')