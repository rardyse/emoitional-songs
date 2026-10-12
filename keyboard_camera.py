import json
import time
import paho.mqtt.client as mqtt

UNIT = "laptop"
BASE = f"EmotionalSongs/KeyboardCamera/U/{UNIT}"
EMOTIONS = ["happy", "fear", "surprise", "sad", "angry", "neutral", "disgust"]

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"keyboard-camera-{UNIT}")

# Si le programme plante, le broker publie "online = false" a notre place
client.will_set(f"{BASE}/S/online", json.dumps({"value": False}), qos=1, retain=True)

client.connect("localhost", 1883)
client.loop_start()
client.publish(f"{BASE}/S/online", json.dumps({"value": True}), qos=1, retain=True)

print("Tape une emotion :", ", ".join(EMOTIONS))
last = None

try:
    while True:
        emotion = input("> ").strip().lower()
        if emotion not in EMOTIONS:
            print("inconnue")
            continue
        if emotion == last:
            continue
        last = emotion
        event = {"value": emotion, "confidence": 100, "time": time.time()}
        client.publish(f"{BASE}/E/emotion", json.dumps(event), qos=1, retain=False)
        print("publie :", event)
except (KeyboardInterrupt, EOFError):
    client.publish(f"{BASE}/S/online", json.dumps({"value": False}), qos=1, retain=True).wait_for_publish()
    client.disconnect()