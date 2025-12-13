import cv2
import numpy as np
import threading
import mediapipe as mp

class IPStream:
    def __init__(self, url):
        self.cap = cv2.VideoCapture(url)
        self.frame = np.zeros((480, 640, 3), np.uint8)
        self.running = True
        threading.Thread(target=self.update, daemon=True).start()
    def update(self):
        while self.running:
            ret, img = self.cap.read()
            if ret: self.frame = img
    def read(self):
        return True, self.frame
    def release(self):
        self.running = False
        self.cap.release()

def detect_and_draw(frame, model):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_rgb.flags.writeable = False
    
    results = model.process(frame_rgb)
    
    if results.pose_landmarks:
        mp.solutions.drawing_utils.draw_landmarks(
            frame, 
            results.pose_landmarks, 
            mp.solutions.pose.POSE_CONNECTIONS
        )
    
    return frame, results


def _landmark_dict(results):
    """Return dict of landmark index -> (x_norm, y_norm)."""
    if not results or not results.pose_landmarks:
        return {}
    lm = results.pose_landmarks.landmark
    return {i: (lm[i].x, lm[i].y) for i in range(len(lm))}


def _triangulate_point(x1, y1, x2, y2, focal=1.0, baseline=0.6):
    """Approximate 3D point from two normalized image coords.

    Assumptions:
    - both images are normalized coords from 0..1
    - cameras are symmetric around Z axis at +/-45 degrees yaw
    - focal length is arbitrary scale (focal=1 gives reasonable relative distances)
    - baseline is distance between cameras along X axis
    Returns 3D np.array (x, y, z) in arbitrary units.
    """
    # image plane coords centered at 0
    x_im1 = x1 - 0.5
    y_im1 = 0.5 - y1
    x_im2 = x2 - 0.5
    y_im2 = 0.5 - y2

    d1 = np.array([x_im1, y_im1, focal], dtype=float)
    d2 = np.array([x_im2, y_im2, focal], dtype=float)
    d1 = d1 / np.linalg.norm(d1)
    d2 = d2 / np.linalg.norm(d2)

    # Camera positions: left (-b/2,0,0), right (+b/2,0,0)
    o1 = np.array([-baseline/2.0, 0.0, 0.0])
    o2 = np.array([ baseline/2.0, 0.0, 0.0])

    # Rotate directions by yaw: left camera looks +45deg, right camera -45deg
    th = np.deg2rad(45.0)
    R_left = np.array([[ np.cos(th), 0.0, np.sin(th)],
                       [ 0.0,        1.0, 0.0      ],
                       [-np.sin(th), 0.0, np.cos(th)]])
    R_right = np.array([[ np.cos(-th), 0.0, np.sin(-th)],
                        [ 0.0,         1.0, 0.0       ],
                        [-np.sin(-th), 0.0, np.cos(-th)]])

    v1 = R_left.dot(d1)
    v2 = R_right.dot(d2)

    # Triangulate by finding closest points on two rays o1+s*v1 and o2+t*v2
    a = np.dot(v1, v1)
    b = np.dot(v1, v2)
    c = np.dot(v2, v2)
    w0 = o1 - o2
    e = np.dot(v1, w0)
    f = np.dot(v2, w0)
    denom = a*c - b*b
    if abs(denom) < 1e-6:
        s = 0.0
        t = 0.0
    else:
        s = (b*f - c*e) / denom
        t = (a*f - b*e) / denom

    p1 = o1 + s * v1
    p2 = o2 + t * v2
    return (p1 + p2) / 2.0


def reconstruct_3d(results_left, results_right, focal=1.0, baseline=0.6):
    """Reconstruct 3D points for landmarks present in both results.
    Returns dict index -> (x,y,z)
    """
    left = _landmark_dict(results_left)
    right = _landmark_dict(results_right)
    common = set(left.keys()) & set(right.keys())
    pts3d = {}
    for i in common:
        x1, y1 = left[i]
        x2, y2 = right[i]
        pts3d[i] = _triangulate_point(x1, y1, x2, y2, focal=focal, baseline=baseline)
    return pts3d


def angle_between_3d(a, b, c):
    """Return angle at point b formed by points a-b-c in degrees."""
    ba = a - b
    bc = c - b
    na = np.linalg.norm(ba)
    nb = np.linalg.norm(bc)
    if na < 1e-6 or nb < 1e-6:
        return None
    cosang = np.dot(ba, bc) / (na * nb)
    cosang = np.clip(cosang, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosang)))


def compute_angles_3d(results_left, results_right, focal=1.0, baseline=0.6):
    """Compute common joint angles (elbows) from stereo pose results.
    Returns dict with keys like 'left_elbow', 'right_elbow' with angles in degrees.
    """
    pts3d = reconstruct_3d(results_left, results_right, focal=focal, baseline=baseline)
    angles = {}
    # Use MediaPipe landmark indices
    L_SHOULDER = mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value
    L_ELBOW = mp.solutions.pose.PoseLandmark.LEFT_ELBOW.value
    L_WRIST = mp.solutions.pose.PoseLandmark.LEFT_WRIST.value
    R_SHOULDER = mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER.value
    R_ELBOW = mp.solutions.pose.PoseLandmark.RIGHT_ELBOW.value
    R_WRIST = mp.solutions.pose.PoseLandmark.RIGHT_WRIST.value

    # Elbow angles (shoulder - elbow - wrist)
    if L_SHOULDER in pts3d and L_ELBOW in pts3d and L_WRIST in pts3d:
        angles['left_elbow'] = angle_between_3d(pts3d[L_SHOULDER], pts3d[L_ELBOW], pts3d[L_WRIST])
    else:
        angles['left_elbow'] = None

    if R_SHOULDER in pts3d and R_ELBOW in pts3d and R_WRIST in pts3d:
        angles['right_elbow'] = angle_between_3d(pts3d[R_SHOULDER], pts3d[R_ELBOW], pts3d[R_WRIST])
    else:
        angles['right_elbow'] = None

    # Shoulder angles: measure angle at shoulder between torso-up vector and upper-arm (neck/torso - shoulder - elbow)
    angles['left_shoulder'] = None
    angles['right_shoulder'] = None

    # Need a torso-up reference point: prefer midpoint between shoulders (neck proxy), fallback to hip
    L_HIP = mp.solutions.pose.PoseLandmark.LEFT_HIP.value
    R_HIP = mp.solutions.pose.PoseLandmark.RIGHT_HIP.value

    neck = None
    if L_SHOULDER in pts3d and R_SHOULDER in pts3d:
        neck = (pts3d[L_SHOULDER] + pts3d[R_SHOULDER]) / 2.0

    # Left shoulder angle: neck(or left hip) - left_shoulder - left_elbow
    if L_SHOULDER in pts3d and L_ELBOW in pts3d:
        ref = None
        if neck is not None:
            ref = neck
        elif L_HIP in pts3d:
            ref = pts3d[L_HIP]
        if ref is not None:
            angles['left_shoulder'] = angle_between_3d(ref, pts3d[L_SHOULDER], pts3d[L_ELBOW])

    # Right shoulder angle: neck(or right hip) - right_shoulder - right_elbow
    if R_SHOULDER in pts3d and R_ELBOW in pts3d:
        ref = None
        if neck is not None:
            ref = neck
        elif R_HIP in pts3d:
            ref = pts3d[R_HIP]
        if ref is not None:
            angles['right_shoulder'] = angle_between_3d(ref, pts3d[R_SHOULDER], pts3d[R_ELBOW])

    return angles


def draw_angles_on_frames(frame_left, frame_right, results_left, results_right, angles):
    """Draw angle text near elbow landmarks on both frames."""
    # Draw both left and right angles on both frames using each frame's landmark positions
    h1, w1 = frame_left.shape[:2]
    h2, w2 = frame_right.shape[:2]

    # helper to draw a value near a landmark on a frame
    def _draw_if(frame, lm_list, landmark_idx, x_scale, y_scale, val, prefix):
        if lm_list is None:
            return
        if landmark_idx is None or landmark_idx >= len(lm_list):
            return
        x = int(lm_list[landmark_idx].x * x_scale)
        y = int(lm_list[landmark_idx].y * y_scale)
        if val is not None:
            # Use ASCII 'deg' because OpenCV Hershey fonts don't render the Unicode degree symbol (°)
            cv2.putText(frame, f"{prefix}:{int(val)} deg", (x-25, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

    # Left frame: use results_left landmarks to place texts
    if results_left and results_left.pose_landmarks:
        lm_l = results_left.pose_landmarks.landmark
        # left elbow
        _draw_if(frame_left, lm_l, mp.solutions.pose.PoseLandmark.LEFT_ELBOW.value, w1, h1, angles.get('left_elbow'), 'Lel')
        # right elbow
        _draw_if(frame_left, lm_l, mp.solutions.pose.PoseLandmark.RIGHT_ELBOW.value, w1, h1, angles.get('right_elbow'), 'Rel')
        # left shoulder
        _draw_if(frame_left, lm_l, mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value, w1, h1, angles.get('left_shoulder'), 'Lsh')
        # right shoulder
        _draw_if(frame_left, lm_l, mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER.value, w1, h1, angles.get('right_shoulder'), 'Rsh')

    # Right frame: use results_right landmarks to place texts
    if results_right and results_right.pose_landmarks:
        lm_r = results_right.pose_landmarks.landmark
        _draw_if(frame_right, lm_r, mp.solutions.pose.PoseLandmark.LEFT_ELBOW.value, w2, h2, angles.get('left_elbow'), 'Lel')
        _draw_if(frame_right, lm_r, mp.solutions.pose.PoseLandmark.RIGHT_ELBOW.value, w2, h2, angles.get('right_elbow'), 'Rel')
        _draw_if(frame_right, lm_r, mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value, w2, h2, angles.get('left_shoulder'), 'Lsh')
        _draw_if(frame_right, lm_r, mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER.value, w2, h2, angles.get('right_shoulder'), 'Rsh')