Use binzkjb5rditypwr6b8r;

DROP TABLE IF EXISTS SensorData;
DROP TABLE IF EXISTS EnvironmentData;
DROP TABLE IF EXISTS ParkingHistory;
DROP TABLE IF EXISTS Slot;
DROP TABLE IF EXISTS Camera;
DROP TABLE IF EXISTS ParkingLot;
DROP TABLE IF EXISTS Vehicle;


CREATE TABLE ParkingLot (
    lot_id INT AUTO_INCREMENT PRIMARY KEY,
    lot_name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    total_slot INT NOT NULL
);
CREATE TABLE Camera (
	cam_id INT auto_increment primary key,
    role varchar(255) NOT NULL,
    lot_id INT,
    foreign key(lot_id) references ParkingLot(lot_id)
);
CREATE TABLE Slot (
    slot_id INT AUTO_INCREMENT PRIMARY KEY,
    lot_id INT,
    slot_number VARCHAR(20) NOT NULL,
    status ENUM('empty','occupied') DEFAULT 'empty',
    sensor_id VARCHAR(50) UNIQUE,
    led_status ENUM('red','green') DEFAULT 'green',
    FOREIGN KEY (lot_id) REFERENCES ParkingLot(lot_id)
);
CREATE TABLE Vehicle (
    vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
    license_plate VARCHAR(20) UNIQUE NOT NULL,
    vehicle_type ENUM('car','motorbike') DEFAULT 'car'
);
CREATE TABLE ParkingHistory (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    slot_id INT,
    vehicle_id INT,
    time_in DATETIME NOT NULL,
    time_out DATETIME,
    gate_action ENUM('in','out'),
    FOREIGN KEY (slot_id) REFERENCES Slot(slot_id),
    FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id)
);
CREATE TABLE SensorData (
    data_id INT AUTO_INCREMENT PRIMARY KEY,
    sensor_id VARCHAR(50),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    distance FLOAT,  -- dữ liệu từ sonar
    status ENUM('empty','occupied'),
    FOREIGN KEY (sensor_id) REFERENCES Slot(sensor_id)
);
CREATE TABLE EnvironmentData (
    env_id INT AUTO_INCREMENT PRIMARY KEY,
    lot_id INT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    temperature FLOAT,  -- °C
    humidity FLOAT,     -- %
    FOREIGN KEY (lot_id) REFERENCES ParkingLot(lot_id)
);


