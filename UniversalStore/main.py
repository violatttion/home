#!/usr/bin/env python3
"""
УНИВЕРСАЛЬНЫЙ МАГАЗИН — Портативная версия (улучшенная)
=======================================================
- Клиент может заказывать товары
- Менеджер имеет расширенный функционал по заказам (смена статуса)
- Светлая классическая тема, мягкие цвета
- Всё в одном файле

Запуск:
    python main.py

После изменений в database.sql и SHOP_NAME ниже — программа instantly меняет тематику.
"""

import sys
import os
import shutil
from datetime import date

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox,
    QScrollArea, QFrame, QFileDialog, QDialog, QFormLayout,
    QDateEdit, QTabWidget, QTextEdit, QSpinBox, QDoubleSpinBox,
    QMenu
)
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtCore import Qt, QDate
import pymysql

# ============================================
# ============ КОНФИГУРАЦИЯ ==================
# ============================================
SHOP_NAME = "Универсальный магазин товаров"

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "root"
DB_NAME = "UniversalStore"

# Мягкие цвета (светлая тема)
COLOR_PRIMARY = "#5b9bd5"       # Мягкий синий
COLOR_SUCCESS = "#70ad47"       # Мягкий зелёный
COLOR_DANGER  = "#d9534f"       # Мягкий красный
COLOR_DISCOUNT = "#5cb85c"      # Для бейджа скидки
COLOR_OUT_OF_STOCK = "#f0ad4e"  # Тёплый оранжевый для "нет в наличии"


# ============================================
# ============ КЛАСС РАБОТЫ С БД =============
# ============================================
class Database:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
                database=DB_NAME, cursorclass=pymysql.cursors.DictCursor,
                charset='utf8mb4'
            )
        except pymysql.MySQLError as e:
            QMessageBox.critical(None, "Ошибка подключения к БД",
                f"Не удалось подключиться к базе.\n"
                f"Убедитесь, что MySQL запущен и выполнен database.sql\n\n{e}")

    def execute(self, query, params=None):
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            self.connection.commit()
            return cursor.lastrowid

    def fetch_all(self, query, params=None):
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def fetch_one(self, query, params=None):
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()


db = Database()


# ============================================
# ============ ОКНО АВТОРИЗАЦИИ ==============
# ============================================
class AuthWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{SHOP_NAME} — Вход")
        self.setFixedSize(400, 480)
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f7fa; }
            QLabel { color: #1a1a1a; }
            QLineEdit {
                padding: 10px; border: 1px solid #ccc; border-radius: 6px;
                font-size: 14px; background: white; color: #000000;
            }
            QPushButton {
                padding: 12px; border-radius: 8px; font-size: 14px;
                font-weight: 500;
            }
            QPushButton#loginBtn { background-color: #5b9bd5; color: white; }
            QPushButton#loginBtn:hover { background-color: #4a8ac4; }
            QPushButton#guestBtn { background-color: #6c757d; color: white; }
            QPushButton#guestBtn:hover { background-color: #5a6268; }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(12)

        title = QLabel(SHOP_NAME)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #000000; margin-bottom: 10px;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Авторизация", alignment=Qt.AlignmentFlag.AlignCenter))

        self.login_edit = QLineEdit(placeholderText="Логин")
        self.pass_edit = QLineEdit(placeholderText="Пароль", echoMode=QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("Логин:"))
        layout.addWidget(self.login_edit)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.pass_edit)

        layout.addSpacing(15)

        btn_login = QPushButton("Войти")
        btn_login.setObjectName("loginBtn")
        btn_login.clicked.connect(self.login)
        layout.addWidget(btn_login)

        btn_guest = QPushButton("Войти как гость")
        btn_guest.setObjectName("guestBtn")
        btn_guest.clicked.connect(self.login_guest)
        layout.addWidget(btn_guest)

        layout.addStretch()

    def login(self):
        user = db.fetch_one("""
            SELECT u.*, r.role_name, r.role_id 
            FROM Users u JOIN Roles r ON r.role_id = u.role_id
            WHERE username=%s AND password_hash=%s
        """, (self.login_edit.text().strip(), self.pass_edit.text().strip()))

        if not user:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
            return
        self.open_main(user)

    def login_guest(self):
        guest = {'role_id': 1, 'role_name': 'Гость', 'user_id': None,
                 'surname': '', 'name': 'Гость', 'patronymic': ''}
        self.open_main(guest)

    def open_main(self, user):
        self.main = MainWindow(user)
        self.main.show()
        self.close()


# ============================================
# ============ КАРТОЧКА ТОВАРА ===============
# ============================================
class ProductCard(QFrame):
    def __init__(self, product, parent_window, role_id):
        super().__init__()
        self.product = product
        self.parent = parent_window
        self.role_id = role_id

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(15)

        # Фото
        img = QLabel()
        img.setFixedSize(120, 95)
        pix = QPixmap(product.get('image_path') or 'images/picture.png')
        if pix.isNull():
            pix = QPixmap('images/picture.png')
        img.setPixmap(pix.scaled(110, 85, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(img)

        # Инфо
        info = QVBoxLayout()
        info.addWidget(QLabel(f"<b>{product['product_name']}</b>"))
        info.addWidget(QLabel(f"Категория: {product.get('category_name', '—')} | {product.get('manufacturer_name', '—')}"))
        desc = product.get('description', '')[:70]
        info.addWidget(QLabel(desc + ("..." if len(product.get('description', '')) > 70 else "")))
        layout.addLayout(info, 1)

        # Правая колонка
        right = QVBoxLayout()
        right.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        price = float(product['price'])
        disc = float(product.get('discount_percentage') or 0)
        if disc > 0:
            new_p = price * (1 - disc/100)
            price_lbl = QLabel(f'<s style="color:#999;">{price:.0f} ₽</s> <b style="color:#2e7d32;">{new_p:.0f} ₽</b>')
        else:
            price_lbl = QLabel(f"<b>{price:.0f} ₽</b>")
        price_lbl.setStyleSheet("font-size: 15px;")
        right.addWidget(price_lbl)

        stock = int(product.get('stock_quantity', 0))
        stock_lbl = QLabel(f"Остаток: {stock} шт.")
        if stock == 0:
            stock_lbl.setStyleSheet("color: #d9534f; font-weight: 500;")
        right.addWidget(stock_lbl)

        if disc > 10:
            badge = QLabel("Скидка!")
            badge.setStyleSheet(f"background: {COLOR_DISCOUNT}; color: white; padding: 1px 8px; border-radius: 4px; font-size: 11px;")
            right.addWidget(badge)

        layout.addLayout(right)

        # Кнопка "Заказать" только для клиента
        if role_id == 2:  # Клиент
            order_btn = QPushButton("Заказать")
            order_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLOR_PRIMARY}; color: white; padding: 6px 18px;
                    border-radius: 6px; font-size: 13px;
                }}
                QPushButton:hover {{ background: #4a8ac4; }}
            """)
            order_btn.clicked.connect(lambda: self.parent.order_product(self.product))
            layout.addWidget(order_btn)

        # Админ: контекстное меню
        if role_id == 4:
            self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.customContextMenuRequested.connect(self.show_admin_menu)

    def show_admin_menu(self, pos):
        menu = QMenu(self)
        menu.addAction("Редактировать", lambda: self.parent.edit_product(self.product))
        menu.addAction("Удалить", lambda: self.parent.delete_product(self.product))
        menu.exec(self.mapToGlobal(pos))


# ============================================
# ============ ГЛАВНОЕ ОКНО ==================
# ============================================
class MainWindow(QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.role_id = user['role_id']
        self.role_name = user['role_name']
        self.user_id = user.get('user_id')
        self.user_fio = f"{user.get('surname','')} {user.get('name','')} {user.get('patronymic','')}".strip()

        self.setWindowTitle(f"{SHOP_NAME} — {self.role_name}")
        self.resize(1150, 720)

        # Светлая тема
        self.setStyleSheet("""
            QMainWindow { background: #f8f9fa; }
            QTabWidget::pane { border: 1px solid #ddd; background: white; }
            QTabBar::tab {
                padding: 10px 24px; background: #f0f2f5; border: 1px solid #ddd;
                border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px;
                color: #1a1a1a;
            }
            QTabBar::tab:selected { background: white; border-bottom: 2px solid #5b9bd5; color: #000000; }
            QLabel { color: #1a1a1a; }
            QPushButton {
                padding: 8px 16px; border-radius: 6px; font-size: 13px;
            }
            QPushButton:hover { background: #e9ecef; }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        main_l = QVBoxLayout(central)
        main_l.setContentsMargins(15, 12, 15, 12)

        # Шапка
        header = QHBoxLayout()
        header.addWidget(QLabel(f"<b>{self.role_name}</b> — {self.user_fio or 'Гость'}"))
        header.addStretch()
        exit_btn = QPushButton("Выйти")
        exit_btn.setStyleSheet("background: #dc3545; color: white;")
        exit_btn.clicked.connect(self.logout)
        header.addWidget(exit_btn)
        main_l.addLayout(header)

        # Вкладки
        self.tabs = QTabWidget()
        main_l.addWidget(self.tabs)

        # === Вкладка Каталог ===
        self.catalog_widget = self.create_catalog_tab()
        self.tabs.addTab(self.catalog_widget, "Каталог товаров")

        # === Вкладка Заказы ===
        if self.role_id >= 2:
            self.orders_widget = self.create_orders_tab()
            self.tabs.addTab(self.orders_widget, "Заказы")

        # Кнопка "Добавить товар" только для Администратора
        if self.role_id == 4:
            add_btn = QPushButton("➕ Добавить товар")
            add_btn.setStyleSheet(f"background: {COLOR_SUCCESS}; color: white; padding: 10px;")
            add_btn.clicked.connect(self.add_product)
            main_l.addWidget(add_btn)

        self.load_products()

    # ------------------ КАТАЛОГ ------------------
    def create_catalog_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)

        # Фильтры
        fl = QHBoxLayout()
        self.search = QLineEdit(placeholderText="Поиск товаров...")
        self.search.textChanged.connect(self.load_products)
        fl.addWidget(self.search, 3)

        self.supplier_cb = QComboBox()
        self.supplier_cb.addItem("Все поставщики")
        for s in db.fetch_all("SELECT supplier_name FROM Suppliers ORDER BY supplier_name"):
            self.supplier_cb.addItem(s['supplier_name'])
        self.supplier_cb.currentTextChanged.connect(self.load_products)
        fl.addWidget(self.supplier_cb, 2)

        self.sort_cb = QComboBox()
        self.sort_cb.addItems(["По убыванию остатка", "По возрастанию остатка"])
        self.sort_cb.currentTextChanged.connect(self.load_products)
        fl.addWidget(self.sort_cb, 2)
        l.addLayout(fl)

        # Список товаров
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.prod_container = QWidget()
        self.prod_layout = QVBoxLayout(self.prod_container)
        self.prod_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.prod_container)
        l.addWidget(scroll)
        return w

    def load_products(self):
        for i in reversed(range(self.prod_layout.count())):
            item = self.prod_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

        search = self.search.text().strip()
        supplier = self.supplier_cb.currentText()
        sort = "DESC" if "убыванию" in self.sort_cb.currentText() else "ASC"

        try:
            if supplier == "Все поставщики":
                q = f"""
                    SELECT p.*, c.category_name, m.manufacturer_name, s.supplier_name
                    FROM Products p
                    LEFT JOIN Categories c ON c.category_id = p.category_id
                    LEFT JOIN Manufacturers m ON m.manufacturer_id = p.manufacturer_id
                    LEFT JOIN Suppliers s ON s.supplier_id = p.supplier_id
                    WHERE p.product_name LIKE %s OR p.description LIKE %s
                       OR c.category_name LIKE %s OR m.manufacturer_name LIKE %s
                    ORDER BY p.stock_quantity {sort}
                """
                params = (f"%{search}%",)*4
            else:
                q = f"""
                    SELECT p.*, c.category_name, m.manufacturer_name, s.supplier_name
                    FROM Products p
                    LEFT JOIN Categories c ON c.category_id = p.category_id
                    LEFT JOIN Manufacturers m ON m.manufacturer_id = p.manufacturer_id
                    LEFT JOIN Suppliers s ON s.supplier_id = p.supplier_id
                    WHERE s.supplier_name = %s AND (
                        p.product_name LIKE %s OR p.description LIKE %s
                        OR c.category_name LIKE %s OR m.manufacturer_name LIKE %s
                    )
                    ORDER BY p.stock_quantity {sort}
                """
                params = (supplier, f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%")

            products = db.fetch_all(q, params)

            for p in products:
                card = ProductCard(p, self, self.role_id)
                self.prod_layout.addWidget(card)

            if not products:
                self.prod_layout.addWidget(QLabel("Товары не найдены", alignment=Qt.AlignmentFlag.AlignCenter))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    # ------------------ ЗАКАЗЫ ------------------
    def create_orders_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)

        header = QHBoxLayout()
        header.addWidget(QLabel("<b>Список заказов</b>"))
        header.addStretch()

        if self.role_id == 3:  # Менеджер — может менять статус
            refresh_btn = QPushButton("Обновить")
            refresh_btn.clicked.connect(self.load_orders)
            header.addWidget(refresh_btn)

        l.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.order_container = QWidget()
        self.order_layout = QVBoxLayout(self.order_container)
        scroll.setWidget(self.order_container)
        l.addWidget(scroll)

        self.load_orders()
        return w

    def load_orders(self):
        for i in reversed(range(self.order_layout.count())):
            w = self.order_layout.itemAt(i).widget()
            if w: w.setParent(None)

        try:
            orders = db.fetch_all("""
                SELECT o.*, pp.full_address, os.status_name,
                       CONCAT(u.surname, ' ', u.name) as client_name
                FROM Orders o
                LEFT JOIN Pickup_points pp ON pp.pickup_point_id = o.pickup_point_id
                LEFT JOIN Order_statuses os ON os.status_id = o.status_id
                LEFT JOIN Users u ON u.user_id = o.user_id
                ORDER BY o.order_date DESC
            """)

            for o in orders:
                frame = QFrame()
                frame.setStyleSheet("background: #ffffff; border: 1px solid #e0e0e0; border-radius: 6px; padding: 8px;")
                v = QVBoxLayout(frame)

                v.addWidget(QLabel(f"<b>Заказ #{o['order_id']}</b> | Статус: <b>{o['status_name']}</b>"))
                v.addWidget(QLabel(f"Пункт выдачи: {o['full_address']}"))
                v.addWidget(QLabel(f"Дата: {o['order_date']} → {o.get('delivery_date') or '—'}"))
                if o.get('client_name'):
                    v.addWidget(QLabel(f"Клиент: {o['client_name']}"))

                # Для менеджера — кнопка смены статуса
                if self.role_id == 3:
                    btn = QPushButton("Изменить статус")
                    btn.setStyleSheet("padding: 4px 12px; font-size: 12px;")
                    btn.clicked.connect(lambda _, order=o: self.change_order_status(order))
                    v.addWidget(btn)

                self.order_layout.addWidget(frame)

        except Exception as e:
            print("Ошибка загрузки заказов:", e)

    def change_order_status(self, order):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Статус заказа #{order['order_id']}")
        form = QFormLayout(dlg)

        status_cb = QComboBox()
        statuses = db.fetch_all("SELECT * FROM Order_statuses")
        for s in statuses:
            status_cb.addItem(s['status_name'], s['status_id'])
        status_cb.setCurrentText(order['status_name'])
        form.addRow("Новый статус:", status_cb)

        btns = QHBoxLayout()
        save = QPushButton("Сохранить")
        cancel = QPushButton("Отмена")
        btns.addWidget(save)
        btns.addWidget(cancel)
        form.addRow(btns)

        def save_status():
            new_status_id = status_cb.currentData()
            db.execute("UPDATE Orders SET status_id=%s WHERE order_id=%s", (new_status_id, order['order_id']))
            QMessageBox.information(dlg, "Готово", "Статус обновлён")
            dlg.accept()
            self.load_orders()

        save.clicked.connect(save_status)
        cancel.clicked.connect(dlg.reject)
        dlg.exec()

    # ------------------ ЗАКАЗ ТОВАРА (КЛИЕНТ) ------------------
    def order_product(self, product):
        if self.role_id != 2:
            QMessageBox.information(self, "Информация", "Оформление заказов доступно только клиентам.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Оформление заказа — {product['product_name']}")
        dlg.setMinimumWidth(420)

        form = QFormLayout(dlg)

        qty = QSpinBox()
        qty.setMinimum(1)
        qty.setMaximum(product['stock_quantity'] or 10)
        qty.setValue(1)
        form.addRow("Количество:", qty)

        pickup_cb = QComboBox()
        pickups = db.fetch_all("SELECT * FROM Pickup_points")
        for p in pickups:
            pickup_cb.addItem(p['full_address'], p['pickup_point_id'])
        form.addRow("Пункт выдачи:", pickup_cb)

        date_edit = QDateEdit(QDate.currentDate().addDays(7))
        date_edit.setCalendarPopup(True)
        form.addRow("Желаемая дата доставки:", date_edit)

        btn_ok = QPushButton("Оформить заказ")
        btn_ok.setStyleSheet(f"background: {COLOR_SUCCESS}; color: white; padding: 10px;")
        btn_cancel = QPushButton("Отмена")

        form.addRow(btn_ok, btn_cancel)

        def confirm_order():
            try:
                pickup_id = pickup_cb.currentData()
                delivery_date = date_edit.date().toString("yyyy-MM-dd")
                quantity = qty.value()

                # Создаём заказ
                order_id = db.execute("""
                    INSERT INTO Orders (user_id, pickup_point_id, pickup_code, status_id, delivery_date)
                    VALUES (%s, %s, %s, 1, %s)
                """, (self.user_id, pickup_id, f"ORD-{order_id}"[:10] if 'order_id' in locals() else "NEW-ORD", delivery_date))

                # Добавляем позицию
                db.execute("""
                    INSERT INTO OrderItems (order_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s)
                """, (order_id, product['product_id'], quantity, product['price']))

                # Уменьшаем остаток (опционально)
                db.execute("UPDATE Products SET stock_quantity = stock_quantity - %s WHERE product_id = %s",
                           (quantity, product['product_id']))

                QMessageBox.information(dlg, "Успех", "Заказ успешно оформлен!")
                dlg.accept()
                self.load_products()          # обновляем остатки
                if hasattr(self, 'load_orders'):
                    self.load_orders()
            except Exception as e:
                QMessageBox.critical(dlg, "Ошибка", str(e))

        btn_ok.clicked.connect(confirm_order)
        btn_cancel.clicked.connect(dlg.reject)
        dlg.exec()

    # ------------------ АДМИН ФУНКЦИИ ------------------
    def add_product(self):
        self.show_product_form()

    def edit_product(self, product):
        self.show_product_form(product)

    def show_product_form(self, product=None):
        dlg = QDialog(self)
        dlg.setWindowTitle("Добавить товар" if not product else "Редактировать товар")
        dlg.setMinimumWidth(480)

        form = QFormLayout(dlg)

        article = QLineEdit(product['article'] if product else "")
        name = QLineEdit(product['product_name'] if product else "")
        price = QDoubleSpinBox()
        price.setMaximum(1000000)
        price.setValue(float(product['price']) if product else 4990)
        stock = QSpinBox()
        stock.setMaximum(99999)
        stock.setValue(int(product.get('stock_quantity', 0)) if product else 10)
        discount = QDoubleSpinBox()
        discount.setMaximum(100)
        discount.setValue(float(product.get('discount_percentage', 0)) if product else 0)
        desc = QTextEdit(product.get('description', '') if product else "")

        form.addRow("Артикул:", article)
        form.addRow("Название товара:", name)
        form.addRow("Цена:", price)
        form.addRow("Количество на складе:", stock)
        form.addRow("Скидка %:", discount)
        form.addRow("Описание:", desc)

        # Фото
        current_img = [product['image_path'] if product else "images/picture.png"]
        photo_btn = QPushButton("Выбрать фото...")
        photo_lbl = QLabel(os.path.basename(current_img[0]))

        def choose_img():
            path, _ = QFileDialog.getOpenFileName(dlg, "Выберите изображение", "", "Images (*.jpg *.png)")
            if path:
                current_img[0] = path
                photo_lbl.setText(os.path.basename(path))
        photo_btn.clicked.connect(choose_img)
        form.addRow("Фото:", photo_btn)
        form.addRow("", photo_lbl)

        btn_save = QPushButton("Сохранить")
        btn_save.setStyleSheet(f"background: {COLOR_SUCCESS}; color: white;")
        btn_cancel = QPushButton("Отмена")
        form.addRow(btn_save, btn_cancel)

        def save():
            try:
                img_path = current_img[0]
                if not img_path.startswith("images/") and os.path.exists(img_path):
                    os.makedirs("images", exist_ok=True)
                    new_path = os.path.join("images", os.path.basename(img_path))
                    shutil.copy(img_path, new_path)
                    img_path = new_path

                if product:
                    db.execute("""
                        UPDATE Products SET article=%s, product_name=%s, price=%s,
                        stock_quantity=%s, discount_percentage=%s, description=%s, image_path=%s
                        WHERE product_id=%s
                    """, (article.text(), name.text(), price.value(), stock.value(),
                          discount.value(), desc.toPlainText(), img_path, product['product_id']))
                else:
                    db.execute("""
                        INSERT INTO Products (article, product_name, category_id, description,
                            manufacturer_id, supplier_id, price, unit, stock_quantity,
                            discount_percentage, image_path)
                        VALUES (%s,%s,1,%s,1,1,%s,'шт.',%s,%s,%s)
                    """, (article.text(), name.text(), desc.toPlainText(),
                          price.value(), stock.value(), discount.value(), img_path))

                QMessageBox.information(dlg, "Готово", "Товар сохранён")
                dlg.accept()
                self.load_products()
            except Exception as e:
                QMessageBox.critical(dlg, "Ошибка", str(e))

        btn_save.clicked.connect(save)
        btn_cancel.clicked.connect(dlg.reject)
        dlg.exec()

    def delete_product(self, product):
        if QMessageBox.question(self, "Удаление", f"Удалить «{product['product_name']}»?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                used = db.fetch_one("SELECT 1 FROM OrderItems WHERE product_id=%s", (product['product_id'],))
                if used:
                    QMessageBox.warning(self, "Нельзя удалить", "Товар присутствует в заказах.")
                    return
                db.execute("DELETE FROM Products WHERE product_id=%s", (product['product_id'],))
                self.load_products()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def logout(self):
        self.auth = AuthWindow()
        self.auth.show()
        self.close()


# ================== ЗАПУСК ==================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    os.makedirs("images", exist_ok=True)

    win = AuthWindow()
    win.show()
    sys.exit(app.exec())
