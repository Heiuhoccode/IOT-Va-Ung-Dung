import cv2

cap = cv2.VideoCapture(1)  # Thử 0, 1, hoặc 2
if not cap.isOpened():
    print("[ERROR] Không thể mở camera.")
    exit()
while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Không đọc được frame.")
        break
    cv2.imshow("Test Camera", frame)
    if cv2.waitKey(1) & 0xFF == 27:  # Nhấn ESC để thoát
        break
cap.release()
cv2.destroyAllWindows()