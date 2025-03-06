import cv2
import numpy as np

def display_webcam():
    # Initialize the webcam (0 is usually the default camera)
    cap = cv2.VideoCapture(0)
    
    # Check if the webcam is opened correctly
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return
    
    print("Webcam feed started. Press 'q' to quit.")
    
    # Capture the first frame to compare against
    ret, prev_frame = cap.read()
    if not ret:
        print("Error: Failed to capture initial image from webcam.")
        return
    
    # Convert to grayscale for easier comparison
    prev_frame_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    
    # Loop to continuously get frames from the webcam
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        
        # Check if frame was successfully captured
        if not ret:
            print("Error: Failed to capture image from webcam.")
            break
        
        # Convert current frame to grayscale
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate absolute difference between current and previous frame
        frame_diff = cv2.absdiff(frame_gray, prev_frame_gray)
        
        # Apply threshold to highlight significant differences
        _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
        
        # Create a 3-channel image from the thresholded difference
        diff_display = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        
        # Display the difference frame in a window
        cv2.imshow("Motion Detection", diff_display)
        
        # Update previous frame for next iteration
        prev_frame_gray = frame_gray.copy()
        
        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release the webcam and close all windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    display_webcam()
