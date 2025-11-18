import cv2, json, time, paho.mqtt.client as mqtt
from OcrPlate import OcrPlate

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
ocr = OcrPlate("model/best_plate.pt", "model/best_ocr.pt")
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("[ERROR] Cannot open camera 3")

# ==================== LOGIC ====================
last_plate = None          # Biển số lần trước đã publish
last_publish_time = 0      # Thời gian publish gần nhất (để thêm giới hạn tốc độ nhẹ)

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    ocr.set_data(frame)
    plate = ocr.digit_out

    if plate != "unknow":
        current_time = time.time()
        # Publish nếu biển số thay đổi HOẶC đã hơn 3 giây kể từ lần gửi gần nhất
        if current_time-last_publish_time > 10:
        # if plate != last_plate :
            payload = {
                "plate": plate,
                "status": "out",
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
            mqtt_client.publish("camera/entry", json.dumps(payload))
            print("[MQTT] Published:", payload)

            # Cập nhật lại trạng thái
            last_plate = plate
            last_publish_time = current_time

    # Hiển thị khung hình (nếu cần)
    cv2.imshow("Entry Camera", frame)
    if cv2.waitKey(1) & 0xFF == 27:  # Nhấn ESC để thoát
        break

cap.release()
cv2.destroyAllWindows()
