import cv2

car_cascade = cv2.CascadeClassifier('G:/Nam4_Ki1/IOTvaUngDung/Code/WebServer_Version1/smart_parking/cars.xml')

def parking_lot_status(filename):
    if filename is None or filename.size == 0:
        return "available"  # mặc định coi như trống nếu ảnh không hợp lệ

    gray = cv2.cvtColor(filename, cv2.COLOR_BGR2GRAY)
    # detected_cars = car_cascade.detectMultiScale(gray, 1.1, 1)
    detected_cars = car_cascade.detectMultiScale(gray, 1.01, 4)

    if len(detected_cars) == 0:
    
        return "available"

    elif len(detected_cars) > 0:

        return "occupied"
