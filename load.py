import subprocess
import time
import random
import string
import cv2

class VideoStreamer:
    def __init__(self, room_id, fps, width, height):
        self.room_id = room_id
        self.rtmp_url = f"rtmp://192.168.1.9:1935/live/{room_id}"
        self.fps = fps
        self.width = width
        self.height = height
        self.stream_pipe = None

    def generate_random_string(self, length):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def init_stream(self):
        key = self.generate_random_string(10)
        command = [
            'ffmpeg',
            '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', '1920x1080',
            '-r', str(self.fps),
            '-i', '-',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'veryfast',
            '-tune', 'film',         # Adjust tune for film-like quality
            '-crf', '18',            # Constant Rate Factor (CRF) for quality control
            '-maxrate', '8M',        # Maximum bitrate for the stream
            '-bufsize', '16M',       # Buffer size for rate control
            '-g', '60',              # GOP size (keyframe interval)
            '-profile:v', 'high',    # Profile for H.264 codec
            '-level', '4.2',         # Level for H.264 codec
            '-f', 'flv',
            f'{self.rtmp_url}_{key}'
        ]
        self.stream_pipe = subprocess.Popen(command, stdin=subprocess.PIPE)

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

def main():
    num_connections = 300
    fps = 30
    width = 640
    height = 480

    streamers = []

    # Capture from camera
    cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    for i in range(num_connections):
        room_id = f"room_{i}"
        streamer = VideoStreamer(room_id, fps, width, height)
        streamer.init_stream()
        streamers.append(streamer)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            for streamer in streamers:
                streamer.publish_frame(frame)

    except KeyboardInterrupt:
        for streamer in streamers:
            streamer.close()

    cap.release()

if __name__ == "__main__":
    main()
