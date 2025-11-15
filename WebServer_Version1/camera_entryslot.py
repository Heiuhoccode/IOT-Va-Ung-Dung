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

# ==================== MODEL & CAMERA CONFIG ====================
# --- Entry camera (cổng vào) ---
ocr_entry = OcrPlate("model/best_plate.pt", "model/best_ocr.pt")
cap_entry = cv2.VideoCapture(1, cv2.CAP_DSHOW)
if not cap_entry.isOpened():
    print("[ERROR] Cannot open entry camera (index 1)")

entry_last_plate = None
entry_last_publish_time = 0
entry_current_plate_display = None  # để API /entry_status trả về

# --- Slot camera (bãi xe) ---
ocr_slot = OcrPlate("model/best_plate.pt", "model/best_ocr.pt")
cap_slot = cv2.VideoCapture(0)
if not cap_slot.isOpened():
    print("[ERROR] Cannot open slot camera (index 0)")

# ===== Đọc file cấu hình vùng bãi (dùng path tương đối cho tiện) =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
labels_path = os.path.join(BASE_DIR, "smart_parking", "parking_labels.txt")
coords_path = os.path.join(BASE_DIR, "smart_parking", "parking_area_coordinates.txt")

with open(labels_path, encoding="utf-8") as f:
    labels = f.read().splitlines()

with open(coords_path, encoding="utf-8") as f:
    coords_lines = f.read().splitlines()
parking_lot_coords = [list(map(int, line.split())) for line in coords_lines]

# Lưu trạng thái slot
last_status = {}   # trạng thái hiện tại (cho API /parking_status)
last_sent = {}     # lần cuối publish (để tránh spam)


# =======================================================
# ROUTE MENU CHUNG
# =======================================================
@app.route("/")
def home():
    # Trang đơn giản có 2 link: Entry & Slot
    return """
    <h2>Parking System Web</h2>
    <ul>
      <li><a href="/entry">📷 Entry Camera (cổng vào)</a></li>
      <li><a href="/slot">🅿 Slot Camera (bãi đỗ)</a></li>
    </ul>
    """


# =======================================================
# ENTRY CAMERA
# =======================================================
@app.route("/entry")
def entry_page():
    return """
    <h2>Entry Camera</h2>
    <img src="/entry_video_feed" width="640">
    <p>Biển số mới nhất: <span id='plate'></span></p>

    <script>
    setInterval(async () => {
        const res = await fetch("/entry_status");
        const data = await res.json();
        document.getElementById("plate").innerText = data.plate || "None";
    }, 1000);
    </script>
    """


@app.route("/entry_status")
def entry_status():
    return jsonify({"plate": entry_current_plate_display})


@app.route("/entry_video_feed")
def entry_video_feed():

    def gen_frames_entry():
        global entry_last_plate, entry_last_publish_time, entry_current_plate_display

        while True:
            ret, frame = cap_entry.read()
            if not ret:
                continue

            # OCR biển số
            ocr_entry.set_data(frame)
            plate = ocr_entry.digit_out

            # Cập nhật để hiển thị web
            if plate != "unknow":
                entry_current_plate_display = plate

            # Publish MQTT giống logic cũ: nếu biển số thay đổi và cách lần gửi trước > 5s
            if plate != "unknow":
                now = time.time()
                if plate != entry_last_plate and now - entry_last_publish_time > 5:
                    payload = {
                        "plate": plate,
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%S")
                    }
                    mqtt_client.publish("camera/entry", json.dumps(payload))
                    print("[MQTT] Entry published:", payload)

                    entry_last_plate = plate
                    entry_last_publish_time = now

            # Vẽ biển số lên frame
            cv2.putText(frame, f"Plate: {plate}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Stream ra browser
            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                continue

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    return Response(gen_frames_entry(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# =======================================================
# SLOT CAMERA
# =======================================================
@app.route("/slot")
def slot_page():
    return """
    <h2>Slot Camera (bãi đỗ)</h2>
    <img src="/slot_video_feed" width="640">
    <p>Xem API trạng thái bãi: <a href="/parking_status" target="_blank">/parking_status</a></p>
    """


@app.route("/slot_video_feed")
def slot_video_feed():

    def gen_frames_slot():
        global last_status, last_sent

        # Bộ nhớ ổn định trạng thái slot
        slot_memory = {}  # lưu trạng thái & thời gian phát hiện cuối

        def stable_status(slot_name, current_status, stable_time=5.0):
            now = time.time()
            prev = slot_memory.get(slot_name, {"status": None, "time": now})

            if current_status != prev["status"]:
                # Nếu mới thay đổi -> reset thời gian
                slot_memory[slot_name] = {"status": current_status, "time": now}
                return prev["status"]  # vẫn giữ trạng thái cũ cho đến khi đủ ổn định

            # Nếu cùng trạng thái quá stable_time giây -> chấp nhận
            if now - prev["time"] >= stable_time:
                return current_status
            return prev["status"]

        changed = False
        last_publish_time = time.time()
        last_published_payload = None  # để so sánh payload lần trước

        while True:
            ret, frame = cap_slot.read()
            if not ret:
                continue

            status = {}
            for i, coords in enumerate(parking_lot_coords):
                slot_name = labels[i]
                x1, y1, x2, y2 = coords
                slot_img = frame[y1:y2, x1:x2]

                lot_status = parking_lot_status(slot_img)
                lot_status = stable_status(slot_name, lot_status, stable_time=5.0)

                plate_number = None

                if lot_status == "available":
                    color = (0, 255, 0)
                    text = slot_name
                    status[slot_name] = {"status": "available", "plate": None}
                else:
                    color = (0, 0, 255)
                    ocr_slot.set_data(slot_img)
                    plate_number = (
                        ocr_slot.digit_out if ocr_slot.digit_out != "unknow" else "???"
                    )
                    text = f"{slot_name}: {plate_number}"
                    status[slot_name] = {"status": "occupied", "plate": plate_number}

                    # Nếu OCR lỗi ("???") thì lấy lại biển số cũ trong last_status nếu có
                    if plate_number == "???" and slot_name in last_status:
                        prev_plate = last_status[slot_name].get("plate")
                        if prev_plate:
                            plate_number = prev_plate
                            status[slot_name]["plate"] = prev_plate
                            text = f"{slot_name}: {prev_plate}"

                current = {"status": lot_status, "plate": plate_number}
                if last_sent.get(slot_name) != current:
                    last_sent[slot_name] = current
                    changed = True

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, text, (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            last_status = status

            # ===== Publish MQTT mỗi 2.5 giây nếu có thay đổi và payload khác =====
            current_time = time.time()
            if current_time - last_publish_time >= 2.5:
                payload = last_sent

                if not last_published_payload or last_published_payload != payload:
                    mqtt_client.publish("camera/slots", json.dumps(payload))
                    print("[MQTT] Slots updated:", json.dumps(payload, indent=2))
                    # copy nông để tránh sửa chung reference
                    last_published_payload = payload.copy()
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

    return Response(gen_frames_slot(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


# =======================================================
# API TRẠNG THÁI BÃI
# =======================================================
@app.route('/parking_status')
def parking_status_api():
    return jsonify(last_status)


# =======================================================
# MAIN
# =======================================================
if __name__ == '__main__':
    # Chạy 1 web duy nhất cho cả Entry + Slot
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
