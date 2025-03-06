import cv2

def display_webcam():
    # Initialize the webcam (0 is usually the default camera)
    cap = cv2.VideoCapture(0)
    
    # Check if the webcam is opened correctly
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return
    
    print("Webcam feed started. Press 'q' to quit.")
    
    # Loop to continuously get frames from the webcam
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        
        # Check if frame was successfully captured
        if not ret:
            print("Error: Failed to capture image from webcam.")
            break
        
        # Display the frame in a window called "Webcam Feed"
        cv2.imshow("Webcam Feed", frame)
        
        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release the webcam and close all windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    display_webcam()
