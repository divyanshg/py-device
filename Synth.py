import cv2
import subprocess
import requests
import time

BASE_URL = "172.16.3.76"

class Synth:
    def __init__(self, cameraFeed, roomId, apiKey):
        self.cameraFeed = cameraFeed
        self.roomId = roomId
        
        self.rtmp_url = f"rtmp://{BASE_URL}:1935/live/{roomId}?key={apiKey}"
        self.api_url = f"http://{BASE_URL}:3000/rooms/{roomId}/property/update?key={apiKey}"

        fps = int(self.cameraFeed.get(cv2.CAP_PROP_FPS))
        width = int(self.cameraFeed.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cameraFeed.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.command =  ['ffmpeg',
           '-y',
           '-f', 'rawvideo',
           '-vcodec', 'rawvideo',
           '-pix_fmt', 'bgr24',
           '-s', "{}x{}".format(width, height),
           '-r', str(fps),
           '-i', '-',
           '-c:v', 'libx264',
           '-pix_fmt', 'yuv420p',
           '-preset', 'ultrafast',
           '-tune', 'zerolatency',  # Zero latency encoding
           '-f', 'flv',
           self.rtmp_url]
        
        self.stream_pipe = subprocess.Popen(self.command, stdin=subprocess.PIPE)
    
    def publish_frame(self, frame):
        if self.stream_pipe:
            self.stream_pipe.stdin.write(frame.tobytes())

    def close(self):
        if self.stream_pipe:
            self.stream_pipe.stdin.close()
    
    def is_connected(self):
        return self.stream_pipe.poll() is None if self.stream_pipe else False

    def reconnect(self):
        self.close()
        self.init_stream()

    def wait_until_connected(self, timeout=30):
        start_time = time.time()
        while not self.is_connected():
            if time.time() - start_time > timeout:
                raise TimeoutError("Connection timeout reached")
            time.sleep(1)

    def publish_data(self, property, value):
        try:
            response = requests.get(f"{self.api_url}&name={property}&value={value}")
            print(response.json()["message"])
        except Exception as e:
            print(f"Error publishing data to server: {e}")