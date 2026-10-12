import json
import time
import cv2
import paho.mqtt.client as mqtt
from deepface import DeepFace

UNIT = "laptop"
BASE = f"EmotionalSongs/Camera/U/{UNIT}"
ANALYZE_EVERY = 10   # on analyse une image sur 10, sinon c'est trop lent

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"camera-{UNIT}")
client.will_set(f"{BASE}/S/online", json.dumps({"value": False}), qos=1, retain=True)
client.connect("localhost", 1883)
client.loop_start()
client.publish(f"{BASE}/S/online", json.dumps({"value": True}), qos=1, retain=True)

cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cam.isOpened():
    print("Camera introuvable")
    raise SystemExit

label = "..."
last = None
frame_count = 0

try:
    while True:
        ok, frame = cam.read()
        if not ok:
            print("Impossible de lire la camera")
            break

        if frame_count % ANALYZE_EVERY == 0:
            result = DeepFace.analyze(frame, actions=["emotion"],
                                      enforce_detection=False, silent=True)[0]
            emotion = result["dominant_emotion"]
            confidence = float(result["emotion"][emotion])
            label = f"{emotion} {confidence:.0f}%"

            # On n'annonce que les changements : c'est ca, un Event
            if emotion != last:
                last = emotion
                event = {"value": emotion, "confidence": confidence, "time": time.time()}
                client.publish(f"{BASE}/E/emotion", json.dumps(event), qos=1, retain=False)
                print("publie :", label)
        frame_count += 1

        cv2.putText(frame, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
        cv2.imshow("Camera (q pour quitter)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
except KeyboardInterrupt:
    pass

cam.release()
cv2.destroyAllWindows()
client.publish(f"{BASE}/S/online", json.dumps({"value": False}), qos=1, retain=True).wait_for_publish()
client.disconnect()
