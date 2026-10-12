import json
import random
import threading
import time
import paho.mqtt.client as mqtt

UNIT = "laptop"
BASE = f"EmotionalSongs/Emotion/U/{UNIT}"
INTENT_TOPIC = f"{BASE}/I"

MIN_CONFIDENCE = 60    #en %, en dessous on ignore la detection
STABLE_SECONDS = 2.0   #l'emotion doit durer ce temps avant qu'on change de chanson

with open("songs.json", encoding="utf-8") as f:
    SONGS = json.load(f)

lock = threading.Lock()
input_topic = None     #le topic qu'on ecoute, donne par une Intent
pending = None         #(emotion, heure); emotion vue mais pas encore stable
current_mood = None
last_song = None


def publish(topic, value, retain=False):
    client.publish(topic, json.dumps(value), qos=1, retain=retain)


def on_connect(client, userdata, flags, reason_code, properties):
    client.subscribe(INTENT_TOPIC, qos=1)
    publish(f"{BASE}/S/online", {"value": True}, retain=True)
    print("Emotion en ligne, j'attends une Intent sur", INTENT_TOPIC)


def handle_intent(intent):
    global input_topic
    new_topic = intent.get("subscribe", {}).get("topic")
    if not new_topic:
        print("Intent inconnue :", intent)
        return
    if input_topic:
        client.unsubscribe(input_topic)
    input_topic = new_topic
    client.subscribe(input_topic, qos=1)
    publish(f"{BASE}/S/subscriptions/emotion", {"value": input_topic}, retain=True)
    print("J'ecoute maintenant :", input_topic)


def handle_emotion(event):
    global pending
    emotion = event.get("value")
    confidence = event.get("confidence", 0)
    if emotion not in SONGS:
        print(f"ignore : {emotion} (pas dans songs.json)")
        return
    if confidence < MIN_CONFIDENCE:
        print(f"ignore : {emotion} {confidence:.0f}% (pas assez sur)")
        return
    pending = (emotion, time.time())
    print(f"vu : {emotion} {confidence:.0f}%, j'attends {STABLE_SECONDS}s")


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload)
    except json.JSONDecodeError:
        print("message illisible sur", msg.topic)
        return
    with lock:
        if msg.topic == INTENT_TOPIC:
            handle_intent(data)
        elif msg.topic == input_topic:
            handle_emotion(data)


def pick_song(mood):
    choices = [s for s in SONGS[mood] if s != last_song]
    return random.choice(choices or SONGS[mood])


def check_stable():
    global pending, current_mood, last_song
    with lock:
        if pending is None:
            return
        emotion, since = pending
        if time.time() - since < STABLE_SECONDS:
            return
        pending = None
        if emotion == current_mood:
            return
        current_mood = emotion
        song = pick_song(emotion)
        last_song = song
    publish(f"{BASE}/E/songSelected", {"value": song, "mood": emotion, "time": time.time()})
    print(f">>> humeur stable : {emotion} -> {song}")


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"emotion-{UNIT}")
client.will_set(f"{BASE}/S/online", json.dumps({"value": False}), qos=1, retain=True)
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883)
client.loop_start()

try:
    while True:
        check_stable()
        time.sleep(0.1)
except KeyboardInterrupt:
    client.publish(f"{BASE}/S/online", json.dumps({"value": False}), qos=1, retain=True).wait_for_publish()
    client.disconnect()