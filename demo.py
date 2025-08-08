import json
from math import sqrt
from datetime import datetime
import uuid

# ========== 参数 ========== 
GIVEN_VX = 0.0              # X 方向速度（像素/秒）
GIVEN_VY = 480.0            # Y 方向速度（像素/秒）
TOLERANCE = 60.0           # 匹配容差（像素）
TIMEOUT_SECONDS = 2.0       # 超时时间（秒）
CONFIDENCE_THRESHOLD = 0.6  # 置信度阈值


# ========== 数据结构 ==========
class Track:
    def __init__(self, x, y, timestamp):
        self.id = str(uuid.uuid4())[:8]
        self.history = [(timestamp, x, y)]
        self.last_time = timestamp

    def predict_position(self, current_time):
        last_time, x, y = self.history[-1]
        dt = (current_time - last_time).total_seconds()
        px = x + GIVEN_VX * dt
        py = y + GIVEN_VY * dt
        return px, py

    def update(self, x, y, timestamp):
        self.history.append((timestamp, x, y))
        self.last_time = timestamp

    def last_position(self):
        return self.history[-1][1], self.history[-1][2]

# ========== 工具函数 ==========
def euclidean(p1, p2):
    return sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def load_detections(file_path):
    with open(file_path, 'r') as f:
        raw_data = json.load(f)

    detections = []
    for frame in raw_data:
        for det in frame['detection']['detections']:
            if det.get('score', 1.0) < CONFIDENCE_THRESHOLD:
                continue  # 丢弃置信度低的检测

            ts = datetime.strptime(det['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
            detections.append({
                'x': det['x_center'],
                'y': det['y_center'],
                'timestamp': ts
            }) 

    detections.sort(key=lambda d: d['timestamp'])
    return detections


# ========== 主逻辑 ==========
def run_tracking():
    detections = load_detections("log_data\Detections_20250808_134441.json")
    tracks = []

    for det in detections:
        x, y, ts = det['x'], det['y'], det['timestamp']

        matched = False
        for track in tracks:
            time_diff = (ts - track.last_time).total_seconds()
            if time_diff > TIMEOUT_SECONDS:
                continue

            pred_x, pred_y = track.predict_position(ts)
            dist = euclidean((x, y), (pred_x, pred_y))
            if dist <= TOLERANCE:
                track.update(x, y, ts)
                matched = True
                break

        if not matched:
            tracks.append(Track(x, y, ts))

    # 打印结果
    print("\n📌 轨迹追踪结果：")
    for idx, track in enumerate(tracks):
        print(f"\nTrack {idx + 1} (ID: {track.id}):")
        for t, x, y in track.history:
            print(f"  Time: {t}, X: {x}, Y: {y}")

if __name__ == "__main__":
    run_tracking()
