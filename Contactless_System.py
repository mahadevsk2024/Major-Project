import RPi.GPIO as GPIO
import time
import cv2
import face_recognition
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# Gmail credentials
EMAIL_ADDRESS = "raspberrypi3b20@gmail.com"
EMAIL_PASSWORD = "dzbhipoqcgwhuwxp"

# Function to send email
def send_email(subject, body):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = "mahadevsk110@gmail.com"
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server.sendmail(EMAIL_ADDRESS, "mahadevsk110@gmail.com", msg.as_string())
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print("Error sending email:", e)

# Function to log recognized face name with date and time
def log_recognized_face(name):
    with open("/home/pi/Desktop/recognized_faces_log.txt", "a") as log_file:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"{current_time} - {name}\n")
        print(f"Logged recognized face: {name} at {current_time}")

# GPIO setup
IR_PIN = 17
RELAY_PIN = 23
BUZZER_PIN = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(IR_PIN, GPIO.IN)
GPIO.setup(RELAY_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# Load the known faces and their encodings (replace with your data)
known_face_images = [
    "/home/pi/Desktop/Test_Images/Mahadev.jpg",
    "/home/pi/Desktop/Test_Images/Megha.jpg",
    "/home/pi/Desktop/Test_Images/Punit.jpg",
    "/home/pi/Desktop/Test_Images/Sandeep.jpg",
    # Add more known faces here...
]

known_face_encodings = []
for image_path in known_face_images:
    try:
        known_image = cv2.imread(image_path)
        if known_image is None:
            print(f"Error: Could not read image {image_path}")
            continue  # Skip to next iteration if image not loaded
        rgb_image = cv2.cvtColor(known_image, cv2.COLOR_BGR2RGB)  # Convert to RGB
        encoding = face_recognition.face_encodings(rgb_image)[0]  # Get encoding for each face
        known_face_encodings.append(encoding)
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")

# Initialize video capture object
cap = cv2.VideoCapture(0)  # 0 for default camera

# Check if webcam opened successfully
if not cap.isOpened():
    print("Error opening webcam!")
    exit()

try:
    while True:
        # Check if IR sensor detects an object
        if GPIO.input(IR_PIN) == 0:  # IR sensor detects an object (active low)
            print("Object detected")
            
            # Capture frame-by-frame
            ret, frame = cap.read()

            # Check if frame capture was successful
            if not ret:
                print("Failed to capture frame!")
                break

            # Convert frame to RGB format
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Find all faces and their encodings in the current frame
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            face_recognized = False

            # Loop through each face in the current frame
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Match the face encoding with known faces
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"

                # If a match is found, identify the person
                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_face_images[first_match_index].split("/")[-1].split(".")[0]  # Extract name from path
                    face_recognized = True

                # Draw a rectangle around the face and label it with the name
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

                # Log the recognized face with date and time
                if name != "Unknown":
                    log_recognized_face(name)

            # If a known face is recognized, turn on the relay for 10 seconds
            if face_recognized:
                GPIO.output(RELAY_PIN, GPIO.LOW)
                print("Relay turned ON")
                time.sleep(10)  # Keep the relay on for 10 seconds
                GPIO.output(RELAY_PIN, GPIO.HIGH)
                print("Relay turned OFF")
            else:
                # If no known face is recognized, turn on the buzzer for 5 seconds
                GPIO.output(BUZZER_PIN, GPIO.HIGH)
                print("Buzzer turned ON")
                time.sleep(5)  # Keep the buzzer on for 5 seconds
                GPIO.output(BUZZER_PIN, GPIO.LOW)
                print("Buzzer turned OFF")
                
                # Send alert email to the bank manager
                subject = "Unknown person detected!"
                body = "An unknown person has been detected by the face recognition system."
                send_email(subject, body)

            # Display the resulting frame
            cv2.imshow('Face Recognition', frame)

        # Quit if 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Release the capture and clean up the GPIO settings
    cap.release()
    cv2.destroyAllWindows()
    GPIO.cleanup()
