import subprocess
import os
import json
import time
import Jetson.GPIO as GPIO
import cv2
import sys



# Variablen
output_directory = "/home/yusuf/Dokumente/YK-AE/"
output_file = os.path.join(output_directory, "output_0.mkv")
isRecording = False
recordingLock = False
video_count = 0
system_count = 0
process = None  # Initialisierung des Prozesses
jetlog_IsSleeping = False
jetlog_GlanceTest = "/"  # Signalisiert ob die Kameras funktionieren: Wertebereich = { "/", "FAIL", "Success" }
jetlog_ErrorLogs = "/"
handylog_startRec = False
handylog_stopRec = False
handylog_goSleep = False
handylog_pullLog = False



# Responsible for Recording, der Parameter ist ein Bool welcher angibt ob er recorden soll oder nicht
def recorder(record):
    global isRecording, recordingLock, process, output_file, system_count, video_count, jetlog_ErrorLogs
    if recordingLock:
        return
    recordingLock = True
    try:
        if not record and isRecording and process:
            process.terminate()
            process.wait()
            time.sleep(1)  # Warte, um sicherzustellen, dass Datei geschlossen ist
            isRecording = False
            video_count += 1
            variables["video_count"] = video_count
            with open('variables.json', 'w') as file:
                json.dump(variables, file, indent=4)
            if os.path.isfile(output_file):
                log("Recording erfolgreich beendet!")
            else:
                log("ERROR! VIDEO-FILE COULD NOT BE CREATED!")
        elif record:
            output_file = os.path.join(output_directory, f"output_{video_count}.mkv")
            command = [
                'gst-launch-1.0', 'nvarguscamerasrc', '!',
                'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1',
                '!', 'nvvidconv', '!', 'omxh264enc', '!',
                'h264parse', '!', 'matroskamux', '!', 'filesink',
                f'location={output_file}', '-e'
            ]
            process = subprocess.Popen(command)
            isRecording = True
            log(f"Recording gestartet mit Datei: {output_file}")
        else:
            log("WARNING! KONNTE WEDER RECORDEN NOCH RECORDING BEENDEN -> {process} | {record} | {isRecording}")
    except Exception as e:
        log("ERROR! {e}")
        jetlog_ErrorLogs = e
    finally:
        recordingLock = False


# Log-System
def log(message):
    global system_count
    try:
        with open('/proc/uptime', 'r') as f:
            TIME = float(f.readline().split()[0])
    except Exception as e:
        with open('log.txt', 'a') as file:
            file.write(f"{system_count} <<MAIN>> ERROR! CANT ACCESS SYSTEM-TIME!\n")
        TIME = 0
    TIME = round(TIME / 60, 1)
    with open('log.txt', 'a') as file:
        file.write(f"{system_count} <<MAIN>> {message}  *** {TIME} min\n")


# Main
def main():
    global jetlog_IsSleeping, jetlog_GlanceTest, jetlog_ErrorLogs
    with open('HandyLog.json', 'r') as file:
        handyLog = json.load(file)
    handylog_startRec = handyLog['StartRecording']
    handylog_stopRec = handyLog['StopRecording']
    handylog_goSleep = handyLog['GoSleep']
    handylog_pullLog = handyLog['Pull_Log']
    handylog_snapshot = handyLog['Snapshot']
    # ermittle ob Benutzer was will, falls eine der Flags in HandyLog wahr ist werden wir es am Ende resetten
    if handylog_startRec or handylog_stopRec or handylog_goSleep or handylog_pullLog or handylog_snapshot:
        if handylog_startRec:
            recorder(True)
            handyLog['StartRecording'] = False
        if handylog_stopRec:
            recorder(False)
            handyLog['StopRecording'] = False
        if handylog_goSleep:
            jetlog_IsSleeping = True
            handyLog['GoSleep'] = False
        if handylog_pullLog:
            handyLog['Pull_Log'] = False
        if handylog_snapshot:
            snapshot_file = os.path.join(output_directory, "snapshot.mkv")
            command = [
                      'gst-launch-1.0', 'nvarguscamerasrc', '!',
                      'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1',
                      '!', 'nvvidconv', '!', 'omxh264enc', '!',
                      'h264parse', '!', 'matroskamux', '!', 'filesink',
                      f'location={snapshot_file}', '-e'
            ]
            log("Starting snapshot recording...")
            handyLog['Snapshot'] = False
            snapshot_process = subprocess.Popen(command)
            time.sleep(4)  # Record for 4 seconds
            snapshot_process.terminate()
            snapshot_process.wait()
            log(f"Snapshot recording completed: {snapshot_file}")
        with open('HandyLog.json', 'w') as file:
            json.dump(handyLog, file, indent=4)
        jetLog = {
                "Is_Recording": isRecording,
                "Is_Sleeping": jetlog_IsSleeping,
                "Glance_Test": jetlog_GlanceTest,
                "Error_Log": jetlog_ErrorLogs
            }
        with open('JetLog.json', 'w') as file:  # übermittle den Benutzer JetLog
            json.dump(jetLog, file, indent=4)
        
        # Sleep-Mode falls Benutzer es angefordert hat
        if jetlog_IsSleeping:
            jetlog_IsSleeping = False
            try:
                log("Go to Sleep..........")
            except Exception as e:
                log("ERROR! CANT SLEEP! {e}")



if __name__ == '__main__':
    # Lese die Werte aus variables.json
    with open('variables.json', 'r') as file:
        variables = json.load(file)
    system_count = variables["system_count"]
    video_count = variables["video_count"]
    log("YK-AE gestartet...")

    # Starte den YKAE_Sensor Prozess welcher Sensordaten dokumentiert
    try:
        subprocess.Popen(['python3', '/home/yusuf/Dokumente/YK-AE/YKAE_Sensor.py'])
        log("Sensor aktiviert")
    except subprocess.CalledProcessError as e:
        log("ERROR! SENSOR KONNTE NICHT AKTIVIERT WERDEN!")
        jetlog_ErrorLogs = e

    # Glance-Test um zu überprüfen ob die Kameras funktionieren
    glance_file = "glance.mkv"
    command = [
                'gst-launch-1.0', 'nvarguscamerasrc', '!',
                'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=10/1',
                '!', 'nvvidconv', '!', 'omxh264enc', '!',
                'h264parse', '!', 'matroskamux', '!', 'filesink',
                f'location={glance_file}', '-e'
            ]
    log("Starte Glance-Test...")
    glance_process = subprocess.Popen(command)
    log(f"Glance-Recording gestartet...")
    time.sleep(2.5)
    glance_process.terminate()
    glance_process.wait()
    if os.path.isfile(glance_file):
        log("Glance-Test erfolgreich beendet!")
        try:
            os.remove(glance_file)
        except Exception as e:
            log("ERROR! COULD NOT REMOVE GLANCE-FILE!")
        jetlog_GlanceTest = "Success"
        log("YK-AE ist betriebsbereit!")
    else:
        log("ERROR! GLANCE-TEST FAIL!")
        jetlog_GlanceTest = "FAIL"

    # Starte Netcat Listener welcher auf HandyLog.json vom Handy geschickt listenet
    try:
        subprocess.Popen(["bash", "-c", "while true; do nc -lv -p 5000 > temp.json && [ -s temp.json ] && mv temp.json HandyLog.json; done"], 
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log("Netcat Listener gestartet...")
    except subprocess.CalledProcessError as e:
        log("ERROR! Netcat KONNTE NICHT AKTIVIERT WERDEN!")
        jetlog_ErrorLogs = e

    # Server Script starten
    try:
        subprocess.Popen(['python3', '/home/yusuf/Dokumente/YK-AE/YKAE_Server.py'])
        log("Versuche Server zu starten...")
    except subprocess.CalledProcessError as e:
        log("ERROR! Server KONNTE NICHT AKTIVIERT WERDEN!")
        jetlog_ErrorLogs = e

    # MAIN
    try:
        while True:
            main()
            time.sleep(10)
    finally:
        # Aktualisiere die variablen
        variables["video_count"] = video_count
        with open('variables.json', 'w') as file:
            json.dump(variables, file, indent=4)
        log("Terminiere...")
    
    





