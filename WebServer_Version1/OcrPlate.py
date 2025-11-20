from ultralytics import YOLO
import cv2
import numpy as np

class OcrPlate:
    def __init__(self, path_detect_model, path_ocr_model):
        """
        path_detect_model: model YOLO detect biển số
        path_ocr_model: model YOLO OCR ký tự
        """
        self.model_plate = YOLO(path_detect_model)
        self.model_ocr = YOLO(path_ocr_model)

        # Kết quả trả về
        self.image_input = None
        self.image_output = None
        self.digit_out = "unknow"
        self.confidence = 0.0
        self.box_xyxy = None

    # ============================
    # ==== HÀM XỬ LÝ CHÍNH  ======
    # ============================

    def set_data(self, image_input):
        """ Nhận ảnh gốc và bắt đầu quá trình detect + OCR """
        self.image_input = image_input.copy()
        self.image_output = image_input.copy()
        self.digit_out = "unknow"
        self.confidence = 0.0

        self.detect_and_ocr()

    # ============================
    # ==== 1. TIỀN XỬ LÝ ẢNH =====
    # ============================

    def preprocess_plate(self, img):
        """
        Tăng chất lượng biển số trước khi OCR.
        """
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        except:
            gray = img

        # Khử nhiễu
        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        # Tăng tương phản
        gray = cv2.equalizeHist(gray)

        # Resize về kích thước chuẩn cho OCR
        gray = cv2.resize(gray, (320, 80))

        # Đổi lại về 3 kênh cho YOLO OCR
        processed = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        return processed

    # ============================
    # ==== 2. PHÁT HIỆN BIỂN =====
    # ============================

    def detect_and_ocr(self):
        lbs = self.model_ocr.names

        # YOLO detect biển số
        results = self.model_plate.predict(
            source=self.image_input,
            conf=0.55,          # giảm từ 0.8 → 0.55
            iou=0.65,
            verbose=False
        )

        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return

        xyxy = boxes.xyxy
        conf = boxes.conf
        cls = boxes.cls

        self.box_xyxy = xyxy

        # Lặp qua từng biển số phát hiện
        for (x1, y1, x2, y2), cf in zip(xyxy, conf):
            x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

            # Loại bỏ biển quá nhỏ
            if (x2 - x1) < 80 or (y2 - y1) < 30:
                continue

            self.confidence = float(cf)

            # Crop biển số
            plate_img = self.image_input[y1:y2, x1:x2]

            # Tiền xử lý ảnh
            plate_img = self.preprocess_plate(plate_img)

            # OCR
            ocr_result = self.model_ocr.predict(
                source=plate_img,
                conf=0.15,      # giảm conf OCR
                iou=0.6,
                verbose=False
            )[0]

            if len(ocr_result.boxes) == 0:
                continue

            # Lấy thông tin ký tự
            chars = self.extract_plate_chars(ocr_result, lbs)

            # Gán kết quả
            self.digit_out = chars

            # Vẽ lên ảnh
            cv2.rectangle(self.image_output, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(self.image_output, chars, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)

    # ==================================
    # ==== 3. XỬ LÝ KÝ TỰ BIỂN SỐ ======
    # ==================================

    def extract_plate_chars(self, ocr_result, labels_encoder):

        boxes = ocr_result.boxes
        xywh = boxes.xywh[:, :2].cpu().numpy()
        cls = boxes.cls.cpu().numpy()
        conf = boxes.conf.cpu().numpy()

        # Điều kiện nhận dạng
        if len(cls) < 5:
            return "unknow"

        # Gộp dữ liệu: x_center, y_center, label
        data = np.hstack([xywh, cls.reshape(-1, 1)])

        return self.sort_and_format_plate(data, labels_encoder)

    # ============================================
    # ==== 4. TÁCH 1 DÒNG / 2 DÒNG + SẮP XẾP ======
    # ============================================

    def sort_and_format_plate(self, data, labels_encoder):
        """
        Nhận diện biển số 1 hoặc 2 dòng.
        Sắp xếp ký tự theo x hoặc theo cả y.
        """
        delta_y = np.max(data[:, 1]) - np.min(data[:, 1])

        # Biển số 2 dòng (delta_y lớn)
        if delta_y > 22:
            y_mean = np.mean(data[:, 1])

            line1 = data[data[:, 1] < y_mean]
            line2 = data[data[:, 1] >= y_mean]

            line1 = line1[line1[:, 0].argsort()]
            line2 = line2[line2[:, 0].argsort()]

            plate = "".join([labels_encoder[int(c)] for c in line1[:, -1]])
            plate += "-" + "".join([labels_encoder[int(c)] for c in line2[:, -1]])

            return plate

        # Biển số 1 dòng
        data = data[data[:, 0].argsort()]
        raw = "".join([labels_encoder[int(c)] for c in data[:, -1]])

        # Chèn dấu "-" sau 3 ký tự (ví dụ: 59A-12345)
        if len(raw) > 3:
            raw = raw[:3] + "-" + raw[3:]

        return raw
