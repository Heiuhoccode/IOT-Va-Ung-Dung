Use binzkjb5rditypwr6b8r;

DELETE FROM SensorData WHERE 1=1;
DELETE FROM EnvironmentData WHERE  1=1;
DELETE FROM ParkingHistory WHERE 1=1;
DELETE FROM Slot WHERE 1=1;
DELETE FROM Vehicle WHERE 1=1;
DELETE FROM ParkingLot WHERE 1=1;

alter table SensorData auto_increment=1;
alter table EnvironmentData auto_increment=1;
alter table ParkingHistory auto_increment=1;
alter table Slot auto_increment=1;
alter table Vehicle auto_increment=1;
alter table ParkingLot auto_increment=1;

INSERT INTO ParkingLot (lot_name, location, total_slot) VALUES
('Bãi xe A', '96A Đ. Trần Phú, P. Mộ Lao, Hà Đông, Hà Nội', 5),
('Bãi xe B', 'Số 310/3, Ngọc Đại, Xã Đại Mỗ, Huyện Từ Liêm, Đai Mễ, Nam Từ Liêm, Hà Nội', 10);
INSERT INTO Vehicle (license_plate, vehicle_type) VALUES
('59A1-12345', 'motorbike'),
('59B2-67890', 'motorbike'),
('51F-11111', 'car'),
('51G-22222', 'car'),
('60C1-33333', 'car'),
('99E1-22268','car');


