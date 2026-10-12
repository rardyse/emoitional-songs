# emotional songs

a webcam recognises the emotion on your face and plays a matching song
three services communicate only through an MQTT broker (event-driven architecture)

| Service | Role | Publishes |
|---|---|---|
| `camera.py` | sensor (webcam + DeepFace) | `Camera/U/laptop/E/emotion` |
| `keyboard_camera.py` | backup sensor (type the emotion) | `KeyboardCamera/U/laptop/E/emotion` |
| `emotion.py` | processor (confidence, 2 s stability, song choice) | `Emotion/U/laptop/E/songSelected` |
| `dj.py` | actuator (plays the mp3) | `DJ/U/laptop/E/playing` |
| `configure.py` | topology: tells each service what to listen to | Intents on `.../I` |

all topics start with `EmotionalSongs/`

## architecture

the project is **event-driven**, that means that each service publishes what happened on its own topic, without knowing who listens

- **Camera** says "the emotion changed to happy"
- **Emotion** listens, waits until the emotion is stable (2 s), then says "a song was selected"
- **DJ** listens and plays the song

nobody gives orders to anybody, and no service knows the others
who listens to what (so basically the topology) is decided outside the services, in `configure.py`, with Intents

## why not command-driven ?

in a command-driven design, Emotion would tell the DJ directly: "DJ, play this!!!"
--> Emotion would need to know the DJ exists, where it is and how to call it
--> replacing the DJ or adding a second listener would mean changing Emotion's code

here, Emotion only announces an event
that's why the camera can be swapped for the keyboard (`demo.bat keyboard`) without touching Emotion or the DJ: only the wiring in `configure.py` changes

## topics (also called DUISE)

topics follow the DUISE structure from the course: `EmotionalSongs/<Service>/U/<unit>/{I, S, E}`

- `E` (Event): what happened --> `E/emotion`, `E/songSelected`
- `S` (Status): what is true now --> `S/online` (retained, with a Last Will if the service crashes)
- `I` (Intent): what is requested --> "subscribe to this topic"

AND --> MQTT is only the transport, the architecture would stay the same with another one (for example shared folders, like in the course tutorial regarding ROT13)

## installation

1. Python 3.12, then:
   ```
   python -m pip install -r requirements.txt
   ```
2. Mosquitto broker: https://mosquitto.org/download/ (Windows installer, default options)
   Check that it is running:
   ```
   sc query mosquitto
   ```
   The state must be `RUNNING`. Otherwise: `net start mosquitto` (as administrator)
3. Put the mp3 files (user's choice) in `songs/` with the names listed in `songs.json`

## run

open a terminal in the project folder, the command depends on the terminal:

| Terminal | Prompt starts with | Command |
|---|---|---|
| Command Prompt (cmd) | `C:\...>` | `demo.bat` |
| PowerShell | `PS C:\...>` | `.\demo.bat` |

this will open three windows:
- **Emotion**
- **DJ**
- **Camera** (takes a few seconds to load DeepFace)

choose then "a face expression" (for instance, smiling --> happy) and hold it for 2 seconds: the music starts
press `q` in the camera window to quit!

## so... what's actually demo.bat ?

`demo.bat` is a Windows batch script that starts everything in the right order:

1. reads the mode given after the command (precise after demo.bat whether we want `camera` or `keyboard`)
2. checks that the MQTT broker is running on port 1883 (`netstat`); if not, it stops
3. opens two new windows: **Emotion** and **DJ** (`start ... cmd /k python ...`)
4. waits 5 seconds so both services are connected to the broker
5. runs `configure.py <mode>`, which sends the Intents: Emotion listens to the sensor, DJ listens to Emotion
6. opens the sensor window: **Camera** or **KeyboardCamera**

AND --> the order matters: Intents are not retained by the broker, so Emotion and DJ must be running before `configure.py` sends them

## backup (no webcam)

in case there is no camera, the use of keyboard is also possible

```
demo.bat keyboard        (PowerShell: .\demo.bat keyboard)
```

a **KeyboardCamera** window replaces the camera, so the user types an emotion:
(`happy`, `sad`, `fear`, `surprise`, `angry`, `neutral`, `disgust`) and press Enter

## run manually

instead of demo.bat, it is also possible to run the whole project in separate terminals, in this order:
```
python emotion.py
python dj.py
python configure.py camera      (or: keyboard)
python camera.py                (or: keyboard_camera.py)
```
`configure.py` must run after `emotion.py` and `dj.py` are started
