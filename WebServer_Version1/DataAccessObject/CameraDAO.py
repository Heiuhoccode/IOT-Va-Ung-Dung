import pymysql

from WebServer_Version1.DataAccessObject.DAO import DB_CONFIG


class CameraDAO:
    @staticmethod
    def check_plate_in_db(plate):
        print("checkDB")
        try:
            conn = pymysql.connect(**DB_CONFIG, ssl={"ssl": {}})
        except Exception as e:
            print("Lỗi kết nối DB:", e)
            return False

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM Vehicle WHERE license_plate = %s LIMIT 1", (plate,))
            result = cursor.fetchone()
            print(result)
            return result is not None
        finally:
            conn.close()
