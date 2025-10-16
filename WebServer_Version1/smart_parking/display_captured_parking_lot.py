import cv2

img = cv2.imread("G:/Nam4_Ki1/IOTvaUngDung/Code/WebServer_Version1/smart_parking/parking_lot.png")

cv2.imshow("Parking lot", img)

print("[INFO] Display parking lot image. Press any key to exit.")

cv2.waitKey(0)

cv2.destroyAllWindows()