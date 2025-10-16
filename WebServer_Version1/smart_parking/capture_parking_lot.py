import cv2

camera = cv2.VideoCapture(0)

print("[INFO] Initializing camera.")

cv2.namedWindow("Camera")

while True:

    ret, frame = camera.read()

    if not ret:

        print("[ERROR] Failed to initialize camera.")

        break

    h, w = frame.shape[:2]
    cv2.resizeWindow("Camera", w, h)

    cv2.imshow("Camera", frame)

    key = cv2.waitKey(1)

    if key%256 == 27:

        # ESC

        print("[INFO] Camera terminated.")

        break

    elif key%256 == 32:

        # SPACE

        img_name = "G:/Nam4_Ki1/IOTvaUngDung/Code/WebServer_Version1/smart_parking/parking_lot.png"

        print("[INFO] Saving '{}' ...".format(img_name))

        cv2.imwrite(img_name, frame)

        print("[INFO] '{}' saved successfully!".format(img_name))

        camera.release()

        cv2.destroyAllWindows()

        break
# import cv2
# import numpy as np
#
# camera = cv2.VideoCapture(0)
# cv2.namedWindow("Camera", cv2.WINDOW_NORMAL)
#
# target_w, target_h = 800, 600
#
# while True:
#     ret, frame = camera.read()
#     if not ret:
#         break
#
#     h, w = frame.shape[:2]
#     ratio = min(target_w / w, target_h / h)
#     new_w, new_h = int(w * ratio), int(h * ratio)
#     resized = cv2.resize(frame, (new_w, new_h))
#
#     # Tạo khung đen để căn giữa
#     result = np.zeros((target_h, target_w, 3), dtype=np.uint8)
#     x = (target_w - new_w) // 2
#     y = (target_h - new_h) // 2
#     result[y:y+new_h, x:x+new_w] = resized
#
#     cv2.imshow("Camera", result)
#
#     if cv2.waitKey(1) & 0xFF == 27:
#         break
#
# camera.release()
# cv2.destroyAllWindows()

