from flask import Flask, render_template, Response, jsonify
import cv2
from OcrPlate import OcrPlate

from DataAccessObject.CameraDAO import *
from entity import Camera
app = Flask(__name__)

# Load model
ocr_plate = OcrPlate("model/best_plate.pt", "model/best_ocr.pt")
cap = cv2.VideoCapture(1)  # camera


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(Camera.gen_frames(cap,ocr_plate), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/plate')
def plate():
    print(f'{jsonify({"plate": Camera.last_plate})} 877879')
    return jsonify({"plate": Camera.last_plate})

@app.route("/verify_plate/<plate>")
def verify_plate(plate):
    if CameraDAO.check_plate_in_db(plate):
        # Lệnh mở thanh Bariier
        return jsonify({"plate": plate, "status": "Đã xác thực"})
    else:
        return jsonify({"plate": plate, "status": "Không có dữ liệu"})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
