-- =============================================
-- УНИВЕРСАЛЬНЫЙ МАГАЗИН - СКРИПТ СОЗДАНИЯ БД
-- =============================================
-- ИНСТРУКЦИЯ:
-- 1. Откройте MySQL / phpMyAdmin / DBeaver / HeidiSQL
-- 2. Выполните этот скрипт целиком (или по частям)
-- 3. База автоматически создастся с именем UniversalStore
--
-- КАК СДЕЛАТЬ ПОД ДРУГУЮ ТЕМУ (книги, одежда, техника и т.д.):
--   - Измените название базы ниже (опционально)
--   - Измените INSERT в таблицы Categories, Manufacturers, Suppliers
--   - Измените примеры товаров в таблице Products
--   - В main.py измените переменную SHOP_NAME
-- =============================================

CREATE DATABASE IF NOT EXISTS UniversalStore 
    DEFAULT CHARACTER SET utf8mb4 
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE UniversalStore;

-- =====================
-- 1. Роли пользователей
-- =====================
DROP TABLE IF EXISTS Roles;
CREATE TABLE Roles (
    role_id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) NOT NULL UNIQUE COMMENT 'Название роли'
) ENGINE=InnoDB;

INSERT INTO Roles (role_name) VALUES 
('Гость'), 
('Клиент'), 
('Менеджер'), 
('Администратор');

-- =====================
-- 2. Пользователи
-- =====================
DROP TABLE IF EXISTS Users;
CREATE TABLE Users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50),
    surname VARCHAR(50),
    patronymic VARCHAR(50),
    username VARCHAR(100) NOT NULL UNIQUE COMMENT 'Логин (email)',
    password_hash VARCHAR(255) NOT NULL COMMENT 'Пароль (в демо хранится открыто)',
    role_id INT,
    FOREIGN KEY (role_id) REFERENCES Roles(role_id)
) ENGINE=InnoDB;

-- Тестовые пользователи (пароли = логин для простоты демо)
INSERT INTO Users (name, surname, patronymic, username, password_hash, role_id) VALUES
('Иван', 'Петров', 'Сергеевич', 'admin@shop.ru', 'admin123', 4),
('Мария', 'Сидорова', 'Алексеевна', 'manager@shop.ru', 'manager123', 3),
('Алексей', 'Козлов', 'Викторович', 'client@shop.ru', 'client123', 2),
('Гость', 'Гостевой', '', 'guest', 'guest', 1);

-- =====================
-- 3. Категории товаров (УНИВЕРСАЛЬНО — меняйте под свою тему)
-- =====================
DROP TABLE IF EXISTS Categories;
CREATE TABLE Categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB;

INSERT INTO Categories (category_name) VALUES 
('Обувь женская'),
('Обувь мужская'),
('Аксессуары'),
('Одежда');

-- =====================
-- 4. Производители (УНИВЕРСАЛЬНО)
-- =====================
DROP TABLE IF EXISTS Manufacturers;
CREATE TABLE Manufacturers (
    manufacturer_id INT PRIMARY KEY AUTO_INCREMENT,
    manufacturer_name VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB;

INSERT INTO Manufacturers (manufacturer_name) VALUES 
('Kari'),
('Marco Tozzi'),
('Rieker'),
('Adidas'),
('Nike');

-- =====================
-- 5. Поставщики (УНИВЕРСАЛЬНО)
-- =====================
DROP TABLE IF EXISTS Suppliers;
CREATE TABLE Suppliers (
    supplier_id INT PRIMARY KEY AUTO_INCREMENT,
    supplier_name VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB;

INSERT INTO Suppliers (supplier_name) VALUES 
('ООО "ОбувьОпт"'),
('ИП Сидоров'),
('Крупный поставщик');

-- =====================
-- 6. Товары (главная таблица — УНИВЕРСАЛЬНАЯ)
-- =====================
DROP TABLE IF EXISTS Products;
CREATE TABLE Products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    article VARCHAR(50) UNIQUE COMMENT 'Артикул товара',
    product_name VARCHAR(150) NOT NULL,
    category_id INT,
    description TEXT,
    manufacturer_id INT,
    supplier_id INT,
    price DECIMAL(10,2) NOT NULL,
    unit VARCHAR(20) DEFAULT 'шт.',
    stock_quantity INT DEFAULT 0,
    discount_percentage DECIMAL(5,2) DEFAULT 0,
    image_path VARCHAR(255) DEFAULT 'images/1.jpg',
    FOREIGN KEY (category_id) REFERENCES Categories(category_id),
    FOREIGN KEY (manufacturer_id) REFERENCES Manufacturers(manufacturer_id),
    FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id)
) ENGINE=InnoDB;

-- Примеры товаров (легко заменить на книги, телефоны и т.д.)
INSERT INTO Products 
(article, product_name, category_id, description, manufacturer_id, supplier_id, price, unit, stock_quantity, discount_percentage, image_path) 
VALUES
('ART-001', 'Ботинки женские демисезонные', 1, 'Комфортные ботинки на каждый день', 1, 1, 4990, 'шт.', 25, 10, 'images/1.jpg'),
('ART-002', 'Кроссовки мужские спортивные', 2, 'Лёгкие кроссовки для активного отдыха', 4, 2, 6490, 'шт.', 18, 5, 'images/1.jpg'),
('ART-003', 'Туфли классические мужские', 2, 'Офисные туфли из натуральной кожи', 2, 1, 8990, 'шт.', 12, 0, 'images/1.jpg'),
('ART-004', 'Сумка женская кожаная', 3, 'Стильная сумка через плечо', 3, 3, 3290, 'шт.', 30, 15, 'images/1.jpg'),
('ART-005', 'Куртка мужская осенняя', 4, 'Демисезонная куртка с капюшоном', 5, 2, 12500, 'шт.', 8, 20, 'images/1.jpg');

-- =====================
-- 7. Пункты выдачи заказов
-- =====================
DROP TABLE IF EXISTS Pickup_points;
CREATE TABLE Pickup_points (
    pickup_point_id INT PRIMARY KEY AUTO_INCREMENT,
    full_address VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

INSERT INTO Pickup_points (full_address) VALUES 
('г. Москва, ул. Ленина, 15'),
('г. Санкт-Петербург, пр. Невский, 42'),
('г. Казань, ул. Баумана, 7');

-- =====================
-- 8. Статусы заказов
-- =====================
DROP TABLE IF EXISTS Order_statuses;
CREATE TABLE Order_statuses (
    status_id INT PRIMARY KEY AUTO_INCREMENT,
    status_name VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB;

INSERT INTO Order_statuses (status_name) VALUES 
('Новый'),
('В обработке'),
('Завершен'),
('Отменен');

-- =====================
-- 9. Заказы
-- =====================
DROP TABLE IF EXISTS Orders;
CREATE TABLE Orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    pickup_point_id INT,
    pickup_code VARCHAR(20),
    status_id INT,
    order_date DATE DEFAULT (CURRENT_DATE),
    delivery_date DATE,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (pickup_point_id) REFERENCES Pickup_points(pickup_point_id),
    FOREIGN KEY (status_id) REFERENCES Order_statuses(status_id)
) ENGINE=InnoDB;

-- =====================
-- 10. Состав заказа
-- =====================
DROP TABLE IF EXISTS OrderItems;
CREATE TABLE OrderItems (
    order_item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT,
    product_id INT,
    quantity INT DEFAULT 1,
    price DECIMAL(10,2),
    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Products(product_id)
) ENGINE=InnoDB;

-- Пример заказа
INSERT INTO Orders (user_id, pickup_point_id, pickup_code, status_id, order_date, delivery_date) 
VALUES (3, 1, 'PZ-7842', 1, '2026-06-01', '2026-06-10');

INSERT INTO OrderItems (order_id, product_id, quantity, price) VALUES 
(1, 1, 1, 4990),
(1, 4, 2, 3290);

-- =============================================
-- ГОТОВО! База создана.
-- Теперь запустите main.py
-- =============================================