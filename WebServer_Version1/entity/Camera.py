import cv2
last_plate = "Chưa Nhận Diện"
class Camera:
    def __init__(self,id,role):
        self.id = id
        self.role = role

def gen_frames(cap,ocr_plate):
    global last_plate
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            # Nhận diện biển số
            ocr_plate.set_data(frame)
            plate_number = ocr_plate.digit_out
            print(plate_number)
            if plate_number != "unknow":
                last_plate = plate_number
            else:
                last_plate = "Không nhận dạng được"

            # Encode frame để stream
            ret, buffer = cv2.imencode('.jpg', ocr_plate.image_output)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')