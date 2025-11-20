import os

import numpy as np
from flask import Flask, render_template, Response, jsonify
import cv2
from OcrPlate_cu import OcrPlate
from smart_parking.parking_lot_status import parking_lot_status

app = Flask(__name__)

ocr_plate = OcrPlate("model/best_plate.pt", "model/best_ocr.pt")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)# CAP_DSHOW giúp ổn định hơn trên Windows
# cap1 = cv2.VideoCapture(1, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("[ERROR] Cannot open camera")

# Đọc file label
with open("smart_parking/parking_labels.txt") as f:
    labels = f.read().splitlines()

# Đọc file tọa độ
with open("smart_parking/parking_area_coordinates.txt") as f:
    coords_lines = f.read().splitlines()
parking_lot_coords = [list(map(int, line.split())) for line in coords_lines]

# Biến lưu trạng thái mới nhất của bãi
last_status = {}

# ===== Route hiển thị giao diện =====
@app.route('/')
def index():
    return render_template('index.html')

# ===== API Video stream =====
@app.route('/video_feed')
def video_feed():
    def gen_frames():
        global last_status
        while True:
            ret, frame = cap.read()
            # ret2, frame2 = cap1.read()
            if not ret:
                continue

            status = {}

            for i, coords in enumerate(parking_lot_coords):
                slot_img = frame[coords[1]:coords[3], coords[0]:coords[2]]
                lot_status = parking_lot_status(slot_img)

                if lot_status == "available":
                    color = (0, 255, 0)  # xanh
                    text = labels[i]
                    status[labels[i]] = {"status": "available", "plate": None}
                else:
                    color = (0, 0, 255)  # đỏ
                    ocr_plate.set_data(slot_img)
                    plate_number = ocr_plate.digit_out if ocr_plate.digit_out != "unknow" else "???"
                    text = f"{labels[i]}: {plate_number}"
                    status[labels[i]] = {"status": "unavailable", "plate": plate_number}

                cv2.rectangle(frame, (coords[0], coords[1]), (coords[2], coords[3]), color, 2)
                cv2.putText(frame, text, (coords[0], coords[1] - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            # Cập nhật last_status
            last_status = status

            # Encode frame để stream
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# ===== API trạng thái bãi =====
@app.route('/parking_status')
def parking_status():
    global last_status
    return jsonify(last_status)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
