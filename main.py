from utils import *
from classes import *
from settings import *

# Konfiguracja
mp_pose = mp.solutions.pose

pose_local = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
pose_ip = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

cap_local = cv2.VideoCapture(local_idx)
cam_ip = IPStream(ip_url)  # nie laguje, prawie zerowy delay


matches = None
exercise_type = None
print("Wybierz cwiczenie glosowo: biceps lub barki")

while True:
    while exercise_type is None:
        exercise_type = select_exercise_via_voice()
    matches = difflib.get_close_matches(exercise_type, exercises, n=1, cutoff=0.5)
    if matches is not None and matches[0] in exercises:
        exercise_type = matches[0]
        print(f"Wybrano: {exercise_type}")
        break


voice_control = VoiceThread()

while True:
    ret1, frame1 = cap_local.read()
    ret2, frame2 = cam_ip.read()

    if not ret1:
        frame1 = np.zeros((h, w, 3), np.uint8)

    # Skalowanie
    frame1 = cv2.resize(frame1, (w, h))
    frame2 = cv2.resize(frame2, (w, h))

    frame1, results1 = detect_and_draw(frame1, pose_local)
    frame2, results2 = detect_and_draw(frame2, pose_ip)

    # Compute 3D angles from stereo views (assumes cameras at +/-45deg)
    angles = compute_angles_3d(results1, results2, focal=1.0, baseline=0.6)
    draw_angles_on_frames(frame1, frame2, results1, results2, angles)
    cv2.putText(frame1, "Mic ON... (start/stop)", (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.7, WHITE, 1)

    if voice_control.started:
        # tu potem trzeba wrzucic cale liczenie itp itd
        status_color = GREEN
        status_text = f"SERIA TRWA - {exercise_type}"
    else:
        status_color = RED
        status_text = "POWIEDZ 'START'"

    cv2.putText(frame1, status_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.9, status_color, 2)
    cv2.imshow(f"Dual Camera - {exercise_type}", np.hstack((frame1, frame2)))

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
voice_control.stop()
cap_local.release()
cam_ip.release()
cv2.destroyAllWindows()
