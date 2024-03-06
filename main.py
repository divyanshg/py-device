import subprocess
import cv2
from Synth import Synth
import threading
import time
import random
import threading

room_id = "65c79dbd9863ec99529bd7c0"
key = "mr_8884f292683f3f9ad57b66c092d560568a7d39d46cadac293e2f450e893a3fa3"

path = 0
cap = cv2.VideoCapture(path)

synth = Synth(cap, room_id, key)

def publish_data_to_server():
    while True:
        occupants = random.randint(20, 60)

        synth.publish_data("occupants", occupants)
        time.sleep(10)

data_thread = threading.Thread(target=publish_data_to_server)
data_thread.daemon = True 
data_thread.start()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("frame read failed")
        break

    # YOUR CODE FOR PROCESSING FRAME HERE
    try:
        synth.publish_frame(frame)
    except Exception as e:
        print(f"Error publishing frame to RTMP server: {e}")

    if not synth.is_connected():
        time.sleep(10)
        print("Connection to RTMP server lost. Reattempting connection...")
        try:
            synth.reconnect()
            print("Reconnection successful.")
        except Exception as e:
            print(f"Reconnection failed: {e}")

cap.release()
synth.close()
