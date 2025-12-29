import argparse
import os
import sys
import cv2
from ultralytics import YOLO

def main():
    # 1. Argparse Setup
    parser = argparse.ArgumentParser(description="YOLO Video Stream Detection")
    parser.add_argument('--input', type=str, required=True, help="Pfad zur .mp4 Videodatei")
    parser.add_argument('--model', type=str, default='yolov8n.pt', help="YOLO Modell (default: yolov8n.pt)")
    
    args = parser.parse_args()

    # 2. Validierung: Ist es eine .mp4 Datei?
    if not args.input.lower().endswith('.mp4'):
        print(f"ERROR: Die Datei '{args.input}' ist kein MP4-Format!")
        sys.exit(1)

    if not os.path.exists(args.input):
        print(f"ERROR: Die Datei '{args.input}' wurde nicht gefunden!")
        sys.exit(1)

    # 3. YOLO Modell laden
    print(f"Lade Modell {args.model}...")
    model = YOLO(args.model)

    # 4. Videoquelle öffnen
    cap = cv2.VideoCapture(args.input)
    
    if not cap.isOpened():
        print("ERROR: Konnte Videostream nicht öffnen.")
        sys.exit(1)

    print("Starte Livestream... Drücke 'q' zum Beenden.")

    # 5. Iteration über die Video-Frames
    while cap.isOpened():
        success, frame = cap.read()
        
        if not success:
            print("Video-Ende erreicht oder Fehler beim Lesen.")
            break

        # YOLO Inference (Objekterkennung)
        # stream=True nutzt einen Generator für bessere Performance
        results = model(frame, stream=True)

        for result in results:
            # Annotated Frame zeichnen (BBoxes und Labels)
            annotated_frame = result.plot()

            # Fenster anzeigen
            cv2.imshow("YOLOv8 Livestream - YK-AE System", annotated_frame)

        # Abbrechen mit Taste 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Ressourcen freigeben
    cap.release()
    cv2.destroyAllWindows()
    print("Stream beendet.")

if __name__ == "__main__":
    main()
