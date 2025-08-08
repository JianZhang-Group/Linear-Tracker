import json
from math import sqrt
from datetime import datetime
import uuid
import time

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
        self.has_triggered = False  # ✅ 新增字段：是否已执行操作

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

def load_detections_per_frame(file_path):
    with open(file_path, 'r') as f:
        raw_data = json.load(f)

    all_frames = []
    for frame in raw_data:
        detections = []
        for det in frame['detection']['detections']:
            if det.get('score', 1.0) < CONFIDENCE_THRESHOLD:
                continue
            ts = datetime.strptime(det['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
            detections.append({
                'x': det['x_center'],
                'y': det['y_center'],
                'timestamp': ts
            })
        all_frames.append(detections)
    return all_frames

# ========== 实时轨迹维护 ==========
tracks = []

def update_tracks(detections):
    global tracks
    if not detections:
        return

    current_time = detections[0]['timestamp']

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
            new_track = Track(x, y, ts)
            new_track.has_triggered = True
            tracks.append(new_track)

            print(f"[操作触发] 轨迹ID: {new_track.id} 第一次匹配，位置: ({x:.2f}, {y:.2f}) 时间: {ts}")

    cleanup_tracks(current_time)

def cleanup_tracks(current_time):
    global tracks
    tracks = [t for t in tracks if (current_time - t.last_time).total_seconds() <= TIMEOUT_SECONDS]

def get_active_tracks():
    return tracks

# ========== 模拟实时调用 ==========
def realtime_simulation(all_frames, delay=0.5):
    for i, frame_detections in enumerate(all_frames):
        print(f"\n--- Frame {i+1}, detections: {len(frame_detections)} ---")
        update_tracks(frame_detections)

        active = get_active_tracks()
        print(f"活跃轨迹数: {len(active)}")
        for t in active:
            last_pos = t.last_position()
            print(f"轨迹ID: {t.id}, 最新位置: ({last_pos[0]:.2f}, {last_pos[1]:.2f}), 更新时间: {t.last_time}")

        time.sleep(delay)  # 模拟帧间延迟

if __name__ == "__main__":
    file_path = "log_data\Detections_20250808_134441.json"  # 修改为你的文件路径
    all_frames = load_detections_per_frame(file_path)
    realtime_simulation(all_frames)
