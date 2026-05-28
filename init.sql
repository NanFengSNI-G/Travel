-- ============================================================
-- 携程Agent 数据库初始化脚本 (MySQL)
-- 用法: mysql -u root -p Travel < init.sql
-- ============================================================

-- 航班信息表
CREATE TABLE IF NOT EXISTS flights (
    flight_id      INTEGER PRIMARY KEY,
    flight_no      VARCHAR(20)  NOT NULL,
    departure_airport  VARCHAR(10) NOT NULL,
    arrival_airport    VARCHAR(10) NOT NULL,
    scheduled_departure VARCHAR(50) NOT NULL,
    scheduled_arrival   VARCHAR(50) NOT NULL
);

-- 机票表
CREATE TABLE IF NOT EXISTS tickets (
    ticket_no     VARCHAR(50) PRIMARY KEY,
    book_ref      VARCHAR(20) NOT NULL,
    passenger_id  VARCHAR(30) NOT NULL,
    passenger_name VARCHAR(50)
);

-- 机票-航班关联表 (多对多)
CREATE TABLE IF NOT EXISTS ticket_flights (
    ticket_no       VARCHAR(50) NOT NULL,
    flight_id       INTEGER NOT NULL,
    fare_conditions VARCHAR(20),
    PRIMARY KEY (ticket_no, flight_id),
    FOREIGN KEY (ticket_no) REFERENCES tickets(ticket_no),
    FOREIGN KEY (flight_id) REFERENCES flights(flight_id)
);

-- 登机牌表
CREATE TABLE IF NOT EXISTS boarding_passes (
    ticket_no   VARCHAR(50) NOT NULL,
    flight_id   INTEGER NOT NULL,
    boarding_no INTEGER,
    seat_no     VARCHAR(10),
    PRIMARY KEY (ticket_no, flight_id),
    FOREIGN KEY (ticket_no) REFERENCES tickets(ticket_no),
    FOREIGN KEY (flight_id) REFERENCES flights(flight_id)
);

-- 酒店表
CREATE TABLE IF NOT EXISTS hotels (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    location      TEXT NOT NULL,
    price_tier    TEXT,
    checkin_date  TEXT,
    checkout_date TEXT,
    booked        INTEGER DEFAULT 0
);

-- 租车表
CREATE TABLE IF NOT EXISTS car_rentals (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    location   TEXT NOT NULL,
    price_tier TEXT,
    start_date TEXT,
    end_date   TEXT,
    booked     INTEGER DEFAULT 0
);

-- 旅行推荐表
CREATE TABLE IF NOT EXISTS trip_recommendations (
    id        INTEGER PRIMARY KEY,
    name      TEXT NOT NULL,
    location  TEXT NOT NULL,
    keywords  TEXT,
    details   TEXT,
    booked    INTEGER DEFAULT 0
);


-- ============================================================
-- 示例数据（可重复执行：先清空再插入）
-- ============================================================

DELETE FROM boarding_passes;
DELETE FROM ticket_flights;
DELETE FROM tickets;
DELETE FROM flights;
DELETE FROM hotels;
DELETE FROM car_rentals;
DELETE FROM trip_recommendations;

-- 航班
INSERT INTO flights VALUES (1,  'LX011', 'ZRH', 'PEK', '2026-06-15 13:30:00.000+08:00', '2026-06-16 05:45:00.000+08:00');
INSERT INTO flights VALUES (2,  'LX012', 'PEK', 'ZRH', '2026-06-16 07:15:00.000+08:00', '2026-06-16 12:30:00.000+08:00');
INSERT INTO flights VALUES (3,  'LX023', 'ZRH', 'PVG', '2026-06-20 09:00:00.000+08:00', '2026-06-21 01:30:00.000+08:00');
INSERT INTO flights VALUES (4,  'LX024', 'PVG', 'ZRH', '2026-06-21 10:30:00.000+08:00', '2026-06-21 17:00:00.000+08:00');
INSERT INTO flights VALUES (5,  'CA123', 'PEK', 'SHA', '2026-06-10 08:00:00.000+08:00', '2026-06-10 10:15:00.000+08:00');
INSERT INTO flights VALUES (6,  'CA456', 'SHA', 'PEK', '2026-06-10 14:00:00.000+08:00', '2026-06-10 16:15:00.000+08:00');
INSERT INTO flights VALUES (7,  'LX035', 'ZRH', 'CDG', '2026-06-18 07:00:00.000+08:00', '2026-06-18 08:30:00.000+08:00');
INSERT INTO flights VALUES (8,  'LX036', 'CDG', 'ZRH', '2026-06-25 18:00:00.000+08:00', '2026-06-25 19:30:00.000+08:00');
INSERT INTO flights VALUES (9,  'MU567', 'PVG', 'PEK', '2026-06-22 11:00:00.000+08:00', '2026-06-22 13:20:00.000+08:00');
INSERT INTO flights VALUES (10, 'MU890', 'PEK', 'PVG', '2026-06-24 16:00:00.000+08:00', '2026-06-24 18:15:00.000+08:00');

-- 机票
INSERT INTO tickets VALUES ('TKT-001', 'BK-001', '3442 587242', '张伟');
INSERT INTO tickets VALUES ('TKT-002', 'BK-001', '3442 587242', '张伟');
INSERT INTO tickets VALUES ('TKT-003', 'BK-002', '3442 587242', '张伟');
INSERT INTO tickets VALUES ('TKT-004', 'BK-003', '3442 587242', '张伟');

-- 机票-航班关联
INSERT INTO ticket_flights VALUES ('TKT-001', 1, 'Economy');
INSERT INTO ticket_flights VALUES ('TKT-002', 7, 'Business');
INSERT INTO ticket_flights VALUES ('TKT-003', 3, 'Economy');
INSERT INTO ticket_flights VALUES ('TKT-004', 8, 'Economy');

-- 登机牌
INSERT INTO boarding_passes VALUES ('TKT-001', 1, 1, '23A');
INSERT INTO boarding_passes VALUES ('TKT-002', 7, 2, '12B');
INSERT INTO boarding_passes VALUES ('TKT-003', 3, 1, '15C');
INSERT INTO boarding_passes VALUES ('TKT-004', 8, 3, '08D');

-- 酒店
INSERT INTO hotels (id, name, location, price_tier, checkin_date, checkout_date, booked) VALUES
(1, '北京王府井希尔顿酒店',   '北京', 'luxury',    '2026-06-16', '2026-06-20', 0),
(2, '上海外滩茂悦大酒店',     '上海', 'luxury',    '2026-06-21', '2026-06-24', 0),
(3, '北京如家快捷酒店',       '北京', 'budget',    NULL,         NULL,         0),
(4, '上海锦江之星',           '上海', 'budget',    NULL,         NULL,         0),
(5, '巴黎四季酒店',           '巴黎', 'luxury',    NULL,         NULL,         0),
(6, '苏黎世万豪酒店',         '苏黎世','mid-range', NULL,        NULL,         0),
(7, '日内瓦青年旅舍',         '日内瓦','budget',   NULL,         NULL,         0),
(8, '北京诺金酒店',           '北京', 'mid-range', NULL,         NULL,         0);

-- 租车
INSERT INTO car_rentals (id, name, location, price_tier, start_date, end_date, booked) VALUES
(1, '神州租车-大众朗逸',  '北京', 'budget',    NULL, NULL, 0),
(2, '一嗨租车-别克GL8',   '上海', 'mid-range', NULL, NULL, 0),
(3, 'Enterprise-BMW 5系', '苏黎世','luxury',   NULL, NULL, 0),
(4, 'Avis-丰田卡罗拉',    '巴黎', 'budget',    NULL, NULL, 0),
(5, '赫兹租车-奔驰C级',   '日内瓦','luxury',   NULL, NULL, 0),
(6, '神州租车-本田雅阁',  '北京', 'mid-range', NULL, NULL, 0);

-- 旅行推荐
INSERT INTO trip_recommendations (id, name, location, keywords, details, booked) VALUES
(1,  '长城一日游',           '北京',   '长城,历史,文化',    '早上8点出发，含午餐和导游', 0),
(2,  '故宫深度游',           '北京',   '故宫,历史,文化',    '专业导游讲解，约4小时', 0),
(3,  '外滩夜景观光',         '上海',   '夜景,拍照,浪漫',   '晚上7点出发，含游船', 0),
(4,  '瑞士阿尔卑斯山徒步',   '苏黎世', '自然,徒步,冒险',   '全天行程，含向导和午餐', 0),
(5,  '卢浮宫艺术之旅',       '巴黎',   '艺术,文化,博物馆',  '含门票和语音导览', 0),
(6,  '日内瓦湖畔骑行',       '日内瓦', '骑行,自然,休闲',   '提供自行车租赁，约3小时', 0),
(7,  '豫园+城隍庙半日游',    '上海',   '园林,小吃,文化',   '下午1点出发，含小吃品尝', 0),
(8,  '颐和园泛舟体验',       '北京',   '园林,划船,休闲',   '含划船费用，约2小时', 0);
