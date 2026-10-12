import json
import os
import queue
import time
import paho.mqtt.client as mqtt
import pygame

UNIT = "laptop"
BASE = f"EmotionalSongs/DJ/U/{UNIT}"
INTENT_TOPIC = f"{BASE}/I"
SONGS_DIR = "songs"

input_topic = None          # le topic qu'on ecoute, donne par une Intent
to_play = queue.Queue()     # pygame doit jouer depuis le programme principal

pygame.mixer.init()


def publish(topic, value, retain=False):
    client.publish(topic, json.dumps(value), qos=1, retain=retain)


def on_connect(client, userdata, flags, reason_code, properties):
    client.subscribe(INTENT_TOPIC, qos=1)
    publish(f"{BASE}/S/online", {"value": True}, retain=True)
    print("DJ en ligne, attente d'une Intent sur", INTENT_TOPIC)


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
    publish(f"{BASE}/S/subscriptions/song", {"value": input_topic}, retain=True)
    print("DJ écoute maintenant :", input_topic)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload)
    except json.JSONDecodeError:
        print("message illisible sur", msg.topic)
        return
    if msg.topic == INTENT_TOPIC:
        handle_intent(data)
    elif msg.topic == input_topic:
        to_play.put(data.get("value"))


def play(song):
    path = os.path.join(SONGS_DIR, song)
    if not os.path.exists(path):
        print("fichier introuvable :", path)
        return
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
    except pygame.error as e:
        print("impossible de lire", path, ":", e)
        return
    publish(f"{BASE}/E/playing", {"value": song, "time": time.time()})
    print("♪ Dj joue :", song)


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"dj-{UNIT}")
client.will_set(f"{BASE}/S/online", json.dumps({"value": False}), qos=1, retain=True)
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883)
client.loop_start()

try:
    while True:
        try:
            play(to_play.get(timeout=0.2))
        except queue.Empty:
            pass
except KeyboardInterrupt:
    pygame.mixer.music.stop()
    client.publish(f"{BASE}/S/online", json.dumps({"value": False}), qos=1, retain=True).wait_for_publish()
    client.disconnect()
