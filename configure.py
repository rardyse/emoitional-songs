import json
import sys
import paho.mqtt.client as mqtt

#   python configure.py keyboard  -> clavier -> Emotion -> DJ
#   python configure.py camera    -> camera  -> Emotion -> DJ
EMOTION_EVENT = "EmotionalSongs/Emotion/U/laptop/E/songSelected"

WIRINGS = {
    "keyboard": {
        "EmotionalSongs/Emotion/U/laptop/I": "EmotionalSongs/KeyboardCamera/U/laptop/E/emotion",
        "EmotionalSongs/DJ/U/laptop/I": EMOTION_EVENT,
    },
    "camera": {
        "EmotionalSongs/Emotion/U/laptop/I": "EmotionalSongs/Camera/U/laptop/E/emotion",
        "EmotionalSongs/DJ/U/laptop/I": EMOTION_EVENT,
    },
}

mode = sys.argv[1] if len(sys.argv) > 1 else "keyboard"
if mode not in WIRINGS:
    print("usage : python configure.py keyboard | camera")
    raise SystemExit

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="configure")
client.connect("localhost", 1883)
client.loop_start()

for intent_topic, listen_to in WIRINGS[mode].items():
    intent = {"subscribe": {"topic": listen_to}}
    client.publish(intent_topic, json.dumps(intent), qos=1, retain=False).wait_for_publish()
    print(f"{intent_topic}  <-  ecoute {listen_to}")

client.disconnect()
