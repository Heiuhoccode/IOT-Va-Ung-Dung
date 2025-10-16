import os, json, cv2, time
import numpy as np
import paho.mqtt.client as mqtt
from flask import Flask, render_template, Response, jsonify
from OcrPlate import OcrPlate
from smart_parking.parking_lot_status import parking_lot_status

app = Flask(__name__)

# ==================== MQTT CONFIG ====================
MQTT_BROKER = "4e01ee67ec4e475ca4c3b68e2703f19e.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "Nhom3iot"
MQTT_PASS = "Nhom3iot"

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
mqtt_client.tls_set()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

# ==================== CAMERA CONFIG ====================
ocr_plate = OcrPlate("model/best_plate.pt", "model/best_ocr.pt")
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("[ERROR] Cannot open camera")

# ===== Đọc file cấu hình vùng bãi =====
with open("G:/Nam4_Ki1/IOTvaUngDung/Code/WebServer_Version1/smart_parking/parking_labels.txt") as f:
    labels = f.read().splitlines()

with open("G:/Nam4_Ki1/IOTvaUngDung/Code/WebServer_Version1/smart_parking/parking_area_coordinates.txt") as f:
    coords_lines = f.read().splitlines()
parking_lot_coords = [list(map(int, line.split())) for line in coords_lines]

# Lưu trạng thái
last_status = {}   # trạng thái hiện tại (cho API)
last_sent = {}     # lần cuối publish (để tránh spam)

# =======================================================
@app.route('/')
def index():
    return render_template('index.html')

# =======================================================
@app.route('/video_feed')
def video_feed():
    # def gen_frames():
    #     global last_status, last_sent
    #
    #     while True:
    #         ret, frame = cap.read()
    #         if not ret:
    #             continue
    #
    #         status = {}
    #         for i, coords in enumerate(parking_lot_coords):
    #             slot_name = labels[i]
    #             slot_img = frame[coords[1]:coords[3], coords[0]:coords[2]]
    #             lot_status = parking_lot_status(slot_img)
    #             plate_number = None
    #
    #             if lot_status == "available":
    #                 color = (0, 255, 0)
    #                 text = slot_name
    #                 status[slot_name] = {"status": "available", "plate": None}
    #             else:
    #                 color = (0, 0, 255)
    #                 ocr_plate.set_data(slot_img)
    #                 plate_number = (
    #                     ocr_plate.digit_out if ocr_plate.digit_out != "unknow" else "???"
    #                 )
    #                 text = f"{slot_name}: {plate_number}"
    #                 status[slot_name] = {"status": "occupied", "plate": plate_number}
    #
    #             # ===== Publish MQTT nếu thay đổi =====
    #             current = {"status": lot_status, "plate": plate_number}
    #             if last_sent.get(slot_name) != current:
    #                 payload = {
    #                     "slot": slot_name,
    #                     "status": lot_status,
    #                     "plate": plate_number,
    #                     "ts": time.strftime("%Y-%m-%dT%H:%M:%S")
    #                 }
    #                 mqtt_client.publish("camera/slot", json.dumps(payload))
    #                 last_sent[slot_name] = current
    #                 print("[MQTT] Updated:", payload)
    #
    #             # ===== Vẽ khung =====
    #             cv2.rectangle(frame, (coords[0], coords[1]), (coords[2], coords[3]), color, 2)
    #             cv2.putText(frame, text, (coords[0], coords[1] - 5),
    #                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    #
    #         last_status = status
    #
    #         # Stream frame (không delay)
    #         ret, buffer = cv2.imencode('.jpg', frame)
    #         if not ret:
    #             continue
    #
    #         yield (b'--frame\r\n'
    #                b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    def gen_frames():
        global last_status, last_sent
        changed = False
        last_publish_time = time.time()
        last_published_payload = None  # <--- thêm dòng này

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            status = {}
            for i, coords in enumerate(parking_lot_coords):
                slot_name = labels[i]
                slot_img = frame[coords[1]:coords[3], coords[0]:coords[2]]
                lot_status = parking_lot_status(slot_img)
                plate_number = None

                if lot_status == "available":
                    color = (0, 255, 0)
                    text = slot_name
                    status[slot_name] = {"status": "available", "plate": None}
                else:
                    color = (0, 0, 255)
                    ocr_plate.set_data(slot_img)
                    plate_number = (
                        ocr_plate.digit_out if ocr_plate.digit_out != "unknow" else "???"
                    )
                    text = f"{slot_name}: {plate_number}"
                    status[slot_name] = {"status": "occupied", "plate": plate_number}

                current = {"status": lot_status, "plate": plate_number}
                if last_sent.get(slot_name) != current:
                    last_sent[slot_name] = current
                    changed = True

                cv2.rectangle(frame, (coords[0], coords[1]), (coords[2], coords[3]), color, 2)
                cv2.putText(frame, text, (coords[0], coords[1] - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            last_status = status

            # ===== Publish MQTT mỗi 2.5 giây nếu có thay đổi và payload khác =====
            current_time = time.time()
            if current_time - last_publish_time >= 2.5:
                payload = {
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "slots": last_sent
                }

                # So sánh payload với lần publish trước
                if not last_published_payload or last_published_payload["slots"] != payload["slots"]:
                    mqtt_client.publish("camera/slots", json.dumps(payload))
                    print("[MQTT] Updated all slots:", json.dumps(payload, indent=2))
                    last_published_payload = {"slots": payload["slots"].copy()}
                else:
                    # Không gửi vì dữ liệu giống hệt
                    pass

                last_publish_time = current_time
                changed = False

            # Stream frame
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# =======================================================
@app.route('/parking_status')
def parking_status():
    return jsonify(last_status)

# =======================================================
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
