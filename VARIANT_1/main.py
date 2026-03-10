import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
import psycopg2
from datetime import datetime
import re
import hashlib
import csv
from tkinter import font as tkfont

DB_CONFIG = {
    'dbname': 'repair_service',
    'user': 'postgres',
    'password': '123qwe',
    'host': 'localhost',
    'port': '5432'
}

class Validators:
    @staticmethod
    def validate_email(email: str) -> bool:
        if not email:
            return True
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_phone(phone: str) -> bool:
        pattern = r'^\+7\(\d{3}\)\d{3}-\d{2}-\d{2}$'
        return re.match(pattern, phone) is not None

    @staticmethod
    def validate_name(name: str) -> bool:
        return bool(re.match(r'^[А-Яа-яA-Za-z\s-]+$', name.strip()))

    @staticmethod
    def validate_login(login: str) -> bool:
        return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', login))

    @staticmethod
    def validate_password(password: str) -> bool:
        return len(password) >= 6

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

class LoginWindow(ctk.CTkToplevel):
    def __init__(self, parent, db_manager, on_login_success):
        super().__init__(parent)
        self.parent = parent
        self.db_manager = db_manager
        self.on_login_success = on_login_success

        self.title("Авторизация - Сервисный центр")
        self.geometry("400x400")
        self.resizable(False, False)

        self.center_window()
        self.transient(parent)
        self.grab_set()

        self.tabview = ctk.CTkTabview(self, width=450, height=480)
        self.tabview.pack(pady=20, padx=20)

        self.tabview.add("Вход")
        self.tabview.add("Регистрация")

        self.create_login_tab()
        self.create_register_tab()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def create_login_tab(self):
        tab = self.tabview.tab("Вход")

        ctk.CTkLabel(tab, text="ВХОД В СИСТЕМУ", font=("Arial", 20, "bold")).pack(pady=30)

        ctk.CTkLabel(tab, text="Логин:").pack()
        self.login_username = ctk.CTkEntry(tab, width=300, placeholder_text="Введите логин")
        self.login_username.pack(pady=8)
        self.login_username.focus()

        ctk.CTkLabel(tab, text="Пароль:").pack()
        self.login_password = ctk.CTkEntry(tab, width=300, placeholder_text="••••••••", show="*")
        self.login_password.pack(pady=8)

        ctk.CTkButton(tab, text="🔑 Войти", command=self.login, width=300, height=40, font=("Arial", 14)).pack(pady=20)

        info_text = "Тестовые данные:\nadmin / admin123\nmanager / manager123"
        ctk.CTkLabel(tab, text=info_text, font=("Arial", 11), text_color="gray").pack(pady=10)

        self.login_password.bind('<Return>', lambda e: self.login())

    def create_register_tab(self):
        tab = self.tabview.tab("Регистрация")

        ctk.CTkLabel(tab, text="РЕГИСТРАЦИЯ НОВОГО КЛИЕНТА", font=("Arial", 18, "bold")).pack(pady=10)

        self.reg_fields = {}

        ctk.CTkLabel(tab, text="Логин *").pack()
        self.reg_fields['login'] = ctk.CTkEntry(tab, width=300, placeholder_text="от 3 до 20 символов")
        self.reg_fields['login'].pack(pady=5)

        ctk.CTkLabel(tab, text="Пароль *").pack()
        self.reg_fields['password'] = ctk.CTkEntry(tab, width=300, placeholder_text="минимум 6 символов", show="*")
        self.reg_fields['password'].pack(pady=5)

        ctk.CTkLabel(tab, text="Подтвердите пароль *").pack()
        self.reg_fields['password_confirm'] = ctk.CTkEntry(tab, width=300, placeholder_text="повторите пароль", show="*")
        self.reg_fields['password_confirm'].pack(pady=5)

        ctk.CTkLabel(tab, text="ФИО *").pack()
        self.reg_fields['full_name'] = ctk.CTkEntry(tab, width=300, placeholder_text="Иванов Иван Иванович")
        self.reg_fields['full_name'].pack(pady=5)

        ctk.CTkLabel(tab, text="Телефон *").pack()
        self.reg_fields['phone'] = ctk.CTkEntry(tab, width=300, placeholder_text="+7(999)123-45-67")
        self.reg_fields['phone'].pack(pady=5)

        ctk.CTkLabel(tab, text="Email").pack()
        self.reg_fields['email'] = ctk.CTkEntry(tab, width=300, placeholder_text="email@example.com")
        self.reg_fields['email'].pack(pady=5)

        ctk.CTkButton(tab, text="📝 Зарегистрироваться", command=self.register, width=300, height=40, fg_color="green", font=("Arial", 14)).pack(pady=15)

        ctk.CTkLabel(tab, text="* - обязательные поля", font=("Arial", 10), text_color="gray").pack()

    def login(self):
        username = self.login_username.get().strip()
        password = self.login_password.get().strip()

        if not username or not password:
            messagebox.showerror("Ошибка входа", "Введите логин и пароль")
            return

        try:
            self.db_manager.cursor.execute("ROLLBACK")
            password_hash = Validators.hash_password(password)

            query = """
                SELECT u.user_id, u.username, r.role_name, 
                       c.client_id, c.last_name, c.first_name
                FROM users u
                JOIN roles r ON u.role_id = r.role_id
                LEFT JOIN clients c ON u.client_id = c.client_id
                WHERE u.username = %s AND u.password_hash = %s
            """
            self.db_manager.cursor.execute(query, (username, password_hash))
            user = self.db_manager.cursor.fetchone()

            if user:
                self.db_manager.cursor.execute(
                    "UPDATE users SET last_login = %s WHERE user_id = %s",
                    (datetime.now(), user[0])
                )
                self.db_manager.conn.commit()

                messagebox.showinfo("Успех", f"Добро пожаловать, {username}!")
                self.on_login_success(user)
                self.destroy()
            else:
                messagebox.showerror("Ошибка входа", "Неверный логин или пароль")
        except Exception as e:
            self.db_manager.cursor.execute("ROLLBACK")
            messagebox.showerror("Ошибка", f"Ошибка при входе:\n{e}")

    def register(self):
        try:
            self.db_manager.cursor.execute("ROLLBACK")
        except:
            pass

        login = self.reg_fields['login'].get().strip()
        password = self.reg_fields['password'].get().strip()
        password_confirm = self.reg_fields['password_confirm'].get().strip()
        full_name = self.reg_fields['full_name'].get().strip()
        phone = self.reg_fields['phone'].get().strip()
        email = self.reg_fields['email'].get().strip()

        if not all([login, password, password_confirm, full_name, phone]):
            messagebox.showerror("Ошибка", "Заполните все обязательные поля")
            return

        if not Validators.validate_login(login):
            messagebox.showerror("Ошибка", "Логин должен содержать только буквы и цифры (3-20 символов)")
            return

        if not Validators.validate_password(password):
            messagebox.showerror("Ошибка", "Пароль должен быть минимум 6 символов")
            return

        if password != password_confirm:
            messagebox.showerror("Ошибка", "Пароли не совпадают")
            return

        name_parts = full_name.split()
        if len(name_parts) < 2:
            messagebox.showerror("Ошибка", "Введите полное ФИО (Имя Фамилия)")
            return

        last_name = name_parts[0]
        first_name = name_parts[1]
        middle_name = name_parts[2] if len(name_parts) > 2 else None

        if not Validators.validate_name(last_name) or not Validators.validate_name(first_name):
            messagebox.showerror("Ошибка", "ФИО должно содержать только буквы")
            return

        if not Validators.validate_phone(phone):
            messagebox.showerror("Ошибка", "Телефон должен быть в формате +7(999)123-45-67")
            return

        if email and not Validators.validate_email(email):
            messagebox.showerror("Ошибка", "Введите корректный email")
            return

        try:
            self.db_manager.cursor.execute("BEGIN")

            self.db_manager.cursor.execute("SELECT user_id FROM users WHERE username = %s", (login,))
            if self.db_manager.cursor.fetchone():
                messagebox.showerror("Ошибка", "Пользователь с таким логином уже существует")
                self.db_manager.cursor.execute("ROLLBACK")
                return

            self.db_manager.cursor.execute("SELECT client_id FROM clients WHERE phone = %s", (phone,))
            if self.db_manager.cursor.fetchone():
                messagebox.showerror("Ошибка", "Клиент с таким телефоном уже зарегистрирован")
                self.db_manager.cursor.execute("ROLLBACK")
                return

            self.db_manager.cursor.execute("""
                INSERT INTO clients (last_name, first_name, middle_name, phone, email)
                VALUES (%s, %s, %s, %s, %s) RETURNING client_id
            """, (last_name, first_name, middle_name, phone, email or None))
            client_id = self.db_manager.cursor.fetchone()[0]

            self.db_manager.cursor.execute("SELECT role_id FROM roles WHERE role_name = 'Клиент'")
            role_id = self.db_manager.cursor.fetchone()[0]

            password_hash = Validators.hash_password(password)

            self.db_manager.cursor.execute("""
                INSERT INTO users (username, password_hash, role_id, client_id)
                VALUES (%s, %s, %s, %s)
            """, (login, password_hash, role_id, client_id))

            self.db_manager.conn.commit()

            messagebox.showinfo("Успех", "Регистрация прошла успешно!\nТеперь вы можете войти в систему.")

            for field in self.reg_fields.values():
                field.delete(0, 'end')
            self.tabview.set("Вход")

        except Exception as e:
            self.db_manager.conn.rollback()
            messagebox.showerror("Ошибка", f"Не удалось зарегистрироваться:\n{e}")

class NotificationWindow(ctk.CTkToplevel):
    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x200")
        self.resizable(False, False)
        
        self.center_window()
        self.transient(parent)
        self.grab_set()
        
        ctk.CTkLabel(self, text="🔔 УВЕДОМЛЕНИЕ", font=("Arial", 18, "bold"), text_color="#2c3e50").pack(pady=15)
        ctk.CTkLabel(self, text=message, font=("Arial", 14), wraplength=350).pack(pady=20, padx=20)
        ctk.CTkButton(self, text="OK", command=self.destroy, width=150, height=40, fg_color="#3498db").pack(pady=10)
    
    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

class RepairServiceApp:
    def __init__(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        self.window = ctk.CTk()
        self.window.title("Учет заявок на ремонт бытовой техники v2.0")
        self.window.geometry("1400x700")

        self.connect_to_db()
        self.current_user = None
        self.notifications = []

        self.window.withdraw()
        self.show_login()

        self.window.mainloop()

    def connect_to_db(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print("✅ Подключено к БД")
            self.create_notification_trigger()
        except Exception as e:
            messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к БД:\n{e}\n\nПроверьте:\n1. Запущен ли PostgreSQL\n2. Создана ли БД 'repair_service'\n3. Правильный ли пароль в DB_CONFIG")
            exit(1)
    
    def create_notification_trigger(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    notification_id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                    request_id INTEGER REFERENCES repair_requests(request_id) ON DELETE CASCADE,
                    message TEXT NOT NULL,
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
        except:
            pass

    def show_login(self):
        LoginWindow(self.window, self, self.on_login_success)

    def on_login_success(self, user_data):
        self.current_user = {
            'id': user_data[0],
            'username': user_data[1],
            'role': user_data[2],
            'client_id': user_data[3],
            'client_name': f"{user_data[4]} {user_data[5]}" if user_data[4] else None
        }
        
        self.window.deiconify()
        self.create_widgets()
        self.load_requests()
        self.check_notifications()
        
        self.status_label.configure(
            text=f"Добро пожаловать, {self.current_user['username']}! Роль: {self.current_user['role']}"
        )

    def create_widgets(self):
        header_frame = ctk.CTkFrame(self.window, corner_radius=12)
        header_frame.pack(fill="x", padx=15, pady=10)

        title_label = ctk.CTkLabel(
            header_frame,
            text="СИСТЕМА УЧЕТА ЗАЯВОК НА РЕМОНТ ТЕХНИКИ",
            font=("Arial", 28, "bold")
        )
        title_label.pack(side="left", padx=20, pady=15)

        user_label = ctk.CTkLabel(
            header_frame,
            text=f"👤 {self.current_user['username']} ({self.current_user['role']})",
            font=("Arial", 18)
        )
        user_label.pack(side="right", padx=20)

        toolbar_frame = ctk.CTkFrame(self.window, corner_radius=12)
        toolbar_frame.pack(fill="x", padx=15, pady=5)

        if self.current_user['role'] == 'Администратор':
            btn_add = ctk.CTkButton(toolbar_frame, text="➕ Новая заявка", command=self.open_add_window, width=150, height=45, font=("Arial", 16), fg_color="#00b4d8", hover_color="#0096c7")
            btn_add.pack(side="left", padx=10, pady=10)

            btn_edit = ctk.CTkButton(toolbar_frame, text="✏ Редактировать", command=self.open_edit_window, width=150, height=45, font=("Arial", 16), fg_color="#48cae4", hover_color="#00b4d8")
            btn_edit.pack(side="left", padx=10)

            btn_delete = ctk.CTkButton(toolbar_frame, text="🗑 Удалить", command=self.delete_request, width=150, height=45, fg_color="#ba3055", hover_color="#ba3055", font=("Arial", 16))
            btn_delete.pack(side="left", padx=10)

            btn_refresh = ctk.CTkButton(toolbar_frame, text="🔄 Обновить", command=self.load_requests, width=150, height=45, fg_color="#73a0a4", hover_color="#73a0a4", font=("Arial", 16))
            btn_refresh.pack(side="left", padx=10)

            btn_stats = ctk.CTkButton(toolbar_frame, text="📊 Расширенная статистика", command=self.show_detailed_stats, width=200, height=45, fg_color="#3c9298", hover_color="#3c9298", font=("Arial", 16))
            btn_stats.pack(side="left", padx=10)

            btn_export = ctk.CTkButton(toolbar_frame, text="📥 Экспорт отчетов", command=self.export_reports, width=180, height=45, fg_color="#3c9298", hover_color="#3c9298", font=("Arial", 16))
            btn_export.pack(side="left", padx=10)

            btn_clients = ctk.CTkButton(toolbar_frame, text="👥 Клиенты", command=self.open_clients_window, width=150, height=45, fg_color="#3c9298", hover_color="#3c9298", font=("Arial", 16))
            btn_clients.pack(side="left", padx=10)

            btn_notifications = ctk.CTkButton(toolbar_frame, text="🔔 Уведомления", command=self.show_notifications, width=150, height=45, fg_color="#f39c12", hover_color="#e67e22", font=("Arial", 16))
            btn_notifications.pack(side="left", padx=10)

        elif self.current_user['role'] == 'Менеджер':
            btn_edit = ctk.CTkButton(toolbar_frame, text="✏ Редактировать (назначить мастера)", command=self.open_edit_window, width=270, height=45, font=("Arial", 16), fg_color="#48cae4", hover_color="#00b4d8")
            btn_edit.pack(side="left", padx=10, pady=10)

            btn_refresh = ctk.CTkButton(toolbar_frame, text="🔄 Обновить", command=self.load_requests, width=170, height=45, fg_color="#73a0a4", hover_color="#73a0a4", font=("Arial", 16))
            btn_refresh.pack(side="left", padx=10)

            btn_stats = ctk.CTkButton(toolbar_frame, text="📊 Статистика", command=self.show_detailed_stats, width=150, height=45, fg_color="#3c9298", hover_color="#3c9298", font=("Arial", 16))
            btn_stats.pack(side="left", padx=10)

            btn_notifications = ctk.CTkButton(toolbar_frame, text="🔔 Уведомления", command=self.show_notifications, width=150, height=45, fg_color="#f39c12", hover_color="#e67e22", font=("Arial", 16))
            btn_notifications.pack(side="left", padx=10)

        else:
            btn_add = ctk.CTkButton(toolbar_frame, text="➕ Новая заявка", command=self.open_add_window, width=170, height=45, font=("Arial", 16), fg_color="#00b4d8", hover_color="#0096c7")
            btn_add.pack(side="left", padx=10, pady=10)

            btn_edit = ctk.CTkButton(toolbar_frame, text="✏ Редактировать", command=self.open_edit_window, width=170, height=45, font=("Arial", 16), fg_color="#48cae4", hover_color="#00b4d8")
            btn_edit.pack(side="left", padx=10)

            btn_refresh = ctk.CTkButton(toolbar_frame, text="🔄 Обновить", command=self.load_requests, width=170, height=45, fg_color="#73a0a4", hover_color="#73a0a4", font=("Arial", 16))
            btn_refresh.pack(side="left", padx=10)

            btn_notifications = ctk.CTkButton(toolbar_frame, text="🔔 Уведомления", command=self.show_notifications, width=150, height=45, fg_color="#f39c12", hover_color="#e67e22", font=("Arial", 16))
            btn_notifications.pack(side="left", padx=10)

        btn_logout = ctk.CTkButton(toolbar_frame, text="🚪 Выйти", command=self.logout, width=130, height=45, fg_color="#3c9298", hover_color="#3c9298", font=("Arial", 16))
        btn_logout.pack(side="right", padx=15)

        search_frame = ctk.CTkFrame(toolbar_frame)
        search_frame.pack(side="right", padx=5)

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Поиск по номеру, клиенту, телефону...", width=250, font=("Arial", 14))
        self.search_entry.pack(side="left", padx=5)

        ctk.CTkButton(search_frame, text="🔍 Найти", command=self.search_requests, width=80, font=("Arial", 14)).pack(side="left")

        table_frame = ctk.CTkFrame(self.window, corner_radius=12)
        table_frame.pack(fill="both", expand=True, padx=15, pady=10)

        columns = ("ID", "Клиент", "Телефон", "Тип устройства", "Модель", "Проблема", "Статус", "Мастер", "Дата", "Комментарий", "Запчасти")

        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 12), rowheight=35)
        style.configure("Treeview.Heading", font=("Arial", 13, "bold"))

        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)

        for col in columns:
            self.tree.heading(col, text=col)

        self.tree.column("ID", width=50)
        self.tree.column("Клиент", width=180)
        self.tree.column("Телефон", width=140)
        self.tree.column("Тип устройства", width=150)
        self.tree.column("Модель", width=150)
        self.tree.column("Проблема", width=200)
        self.tree.column("Статус", width=130)
        self.tree.column("Мастер", width=150)
        self.tree.column("Дата", width=100)
        self.tree.column("Комментарий", width=150)
        self.tree.column("Запчасти", width=150)

        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")

        status_frame = ctk.CTkFrame(self.window, height=40, corner_radius=12)
        status_frame.pack(fill="x", padx=15, pady=10)

        self.status_label = ctk.CTkLabel(status_frame, text="Готово к работе", font=("Arial", 14))
        self.status_label.pack(side="left", padx=15, pady=5)

        self.count_label = ctk.CTkLabel(status_frame, text="", font=("Arial", 14))
        self.count_label.pack(side="right", padx=15)

    def logout(self):
        result = messagebox.askyesno("Выход", "Вы действительно хотите выйти?")
        if result:
            self.window.withdraw()
            self.current_user = None
            for row in self.tree.get_children():
                self.tree.delete(row)
            self.show_login()

    def load_requests(self):
        try:
            print(f"Загрузка заявок для роли: {self.current_user['role']}") 
            
            if self.current_user['role'] == 'Клиент':
                query = """
                    SELECT 
                        r.request_id,
                        c.last_name || ' ' || c.first_name || COALESCE(' ' || c.middle_name, '') as client,
                        c.phone,
                        dt.type_name,
                        r.device_model,
                        substring(r.problem_description, 1, 50) || 
                            CASE WHEN length(r.problem_description) > 50 THEN '...' ELSE '' END as problem,
                        s.status_name,
                        COALESCE(t.last_name || ' ' || t.first_name, 'Не назначен') as master,
                        to_char(r.creation_date, 'DD.MM.YYYY') as date,
                        COALESCE(r.master_comment, '') as comment,
                        COALESCE(r.parts_needed, '') as parts
                    FROM repair_requests r
                    LEFT JOIN clients c ON r.client_id = c.client_id
                    LEFT JOIN technicians t ON r.technician_id = t.technician_id
                    LEFT JOIN device_types dt ON r.device_type_id = dt.type_id
                    LEFT JOIN request_statuses s ON r.status_id = s.status_id
                    WHERE c.client_id = %s
                    ORDER BY r.creation_date DESC
                """
                self.cursor.execute(query, (self.current_user['client_id'],))
            else:
                query = """
                    SELECT 
                        r.request_id,
                        c.last_name || ' ' || c.first_name || COALESCE(' ' || c.middle_name, '') as client,
                        c.phone,
                        dt.type_name,
                        r.device_model,
                        substring(r.problem_description, 1, 50) || 
                            CASE WHEN length(r.problem_description) > 50 THEN '...' ELSE '' END as problem,
                        s.status_name,
                        COALESCE(t.last_name || ' ' || t.first_name, 'Не назначен') as master,
                        to_char(r.creation_date, 'DD.MM.YYYY') as date,
                        COALESCE(r.master_comment, '') as comment,
                        COALESCE(r.parts_needed, '') as parts
                    FROM repair_requests r
                    LEFT JOIN clients c ON r.client_id = c.client_id
                    LEFT JOIN technicians t ON r.technician_id = t.technician_id
                    LEFT JOIN device_types dt ON r.device_type_id = dt.type_id
                    LEFT JOIN request_statuses s ON r.status_id = s.status_id
                    ORDER BY r.creation_date DESC
                """
                self.cursor.execute(query)
            
            rows = self.cursor.fetchall()
            print(f"Найдено заявок: {len(rows)}") 
            
            for row in self.tree.get_children():
                self.tree.delete(row)

            for row in rows:
                self.tree.insert('', 'end', values=row)
                print(f"Добавлена заявка: {row[0]} - {row[1]}") 

            self.status_label.configure(text="✅ Данные загружены")
            self.count_label.configure(text=f"Всего заявок: {len(rows)}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные:\n{e}")
            self.status_label.configure(text="❌ Ошибка загрузки")

    def search_requests(self):
        search_text = self.search_entry.get().strip()
        if not search_text:
            self.load_requests()
            return

        try:
            query = """
                SELECT 
                    r.request_id,
                    c.last_name || ' ' || c.first_name || COALESCE(' ' || c.middle_name, '') as client,
                    c.phone,
                    dt.type_name,
                    r.device_model,
                    substring(r.problem_description, 1, 50) || 
                        CASE WHEN length(r.problem_description) > 50 THEN '...' ELSE '' END as problem,
                    s.status_name,
                    COALESCE(t.last_name || ' ' || t.first_name, 'Не назначен') as master,
                    to_char(r.creation_date, 'DD.MM.YYYY') as date,
                    COALESCE(r.master_comment, '') as comment,
                    COALESCE(r.parts_needed, '') as parts
                FROM repair_requests r
                LEFT JOIN clients c ON r.client_id = c.client_id
                LEFT JOIN technicians t ON r.technician_id = t.technician_id
                LEFT JOIN device_types dt ON r.device_type_id = dt.type_id
                LEFT JOIN request_statuses s ON r.status_id = s.status_id
                WHERE 
                    CAST(r.request_id AS TEXT) ILIKE %s OR
                    c.last_name ILIKE %s OR
                    c.first_name ILIKE %s OR
                    c.phone ILIKE %s OR
                    dt.type_name ILIKE %s OR
                    r.device_model ILIKE %s
                ORDER BY r.creation_date DESC
            """
            like_pattern = f'%{search_text}%'
            params = [like_pattern] * 7
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()

            for row in self.tree.get_children():
                self.tree.delete(row)

            for row in rows:
                self.tree.insert('', 'end', values=row)

            if rows:
                self.status_label.configure(text=f"🔍 Найдено заявок: {len(rows)}")
                self.count_label.configure(text=f'Результаты по запросу: "{search_text}"')
            else:
                self.status_label.configure(text=f'❌ Ничего не найдено по запросу: "{search_text}"')
                self.count_label.configure(text="")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка поиска:\n{e}")

    def check_notifications(self):
        try:
            self.cursor.execute("""
                SELECT COUNT(*) FROM notifications 
                WHERE user_id = %s AND is_read = FALSE
            """, (self.current_user['id'],))
            count = self.cursor.fetchone()[0]
            if count > 0:
                messagebox.showinfo("Уведомления", f"У вас {count} непрочитанных уведомлений")
        except:
            pass

    def show_notifications(self):
        try:
            self.cursor.execute("""
                SELECT n.notification_id, n.message, n.created_at, 
                       r.request_id, c.last_name || ' ' || c.first_name
                FROM notifications n
                LEFT JOIN repair_requests r ON n.request_id = r.request_id
                LEFT JOIN clients c ON r.client_id = c.client_id
                WHERE n.user_id = %s
                ORDER BY n.created_at DESC
            """, (self.current_user['id'],))
            notifications = self.cursor.fetchall()
            
            if not notifications:
                messagebox.showinfo("Уведомления", "Нет уведомлений")
                return
            
            msg = "🔔 ВАШИ УВЕДОМЛЕНИЯ:\n\n"
            for n in notifications[:10]:
                msg += f"📅 {n[2].strftime('%d.%m.%Y %H:%M')}\n"
                msg += f"📝 {n[1]}\n"
                if n[3]:
                    msg += f"📋 Заявка №{n[3]} - {n[4]}\n"
                msg += "-" * 40 + "\n"
            
            self.cursor.execute("UPDATE notifications SET is_read = TRUE WHERE user_id = %s", (self.current_user['id'],))
            self.conn.commit()
            
            messagebox.showinfo("Уведомления", msg)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить уведомления:\n{e}")

    def add_notification(self, user_id, request_id, message):
        try:
            self.cursor.execute("""
                INSERT INTO notifications (user_id, request_id, message)
                VALUES (%s, %s, %s)
            """, (user_id, request_id, message))
            self.conn.commit()
        except:
            pass

    def show_detailed_stats(self):
        try:
            stats_window = ctk.CTkToplevel(self.window)
            stats_window.title("Расширенная статистика")
            stats_window.geometry("800x600")
            stats_window.transient(self.window)
            stats_window.grab_set()
            
            tabview = ctk.CTkTabview(stats_window, width=750, height=500)
            tabview.pack(pady=20, padx=20)
            
            tabview.add("По мастерам")
            tabview.add("По типам неисправностей")
            tabview.add("По статусам")
            tabview.add("Динамика")
            
            tab1 = tabview.tab("По мастерам")
            self.cursor.execute("""
                SELECT 
                    COALESCE(t.last_name || ' ' || t.first_name, 'Не назначен') as master,
                    COUNT(r.request_id) as total,
                    COUNT(CASE WHEN r.status_id = (SELECT status_id FROM request_statuses WHERE status_name = 'Выполнена') THEN 1 END) as completed,
                    COALESCE(ROUND(AVG(CASE 
                        WHEN r.status_id = (SELECT status_id FROM request_statuses WHERE status_name = 'Выполнена') 
                        THEN r.completion_date - r.creation_date::DATE 
                    END), 1), 0) as avg_days,
                    COUNT(CASE WHEN r.status_id = (SELECT status_id FROM request_statuses WHERE status_name = 'В работе') THEN 1 END) as in_progress
                FROM technicians t
                RIGHT JOIN repair_requests r ON t.technician_id = r.technician_id
                GROUP BY t.technician_id, t.last_name, t.first_name
                UNION ALL
                SELECT 
                    'Не назначен',
                    COUNT(r.request_id),
                    COUNT(CASE WHEN r.status_id = (SELECT status_id FROM request_statuses WHERE status_name = 'Выполнена') THEN 1 END),
                    0,
                    COUNT(CASE WHEN r.status_id = (SELECT status_id FROM request_statuses WHERE status_name = 'В работе') THEN 1 END)
                FROM repair_requests r
                WHERE r.technician_id IS NULL
                ORDER BY total DESC
            """)
            rows = self.cursor.fetchall()
            
            text1 = ctk.CTkTextbox(tab1, font=("Arial", 13))
            text1.pack(fill="both", expand=True, padx=10, pady=10)
            
            text1.insert("end", "📊 СТАТИСТИКА ПО МАСТЕРАМ\n\n")
            for master, total, completed, avg_days, in_progress in rows:
                text1.insert("end", f"👨‍🔧 {master}\n")
                text1.insert("end", f"   Всего заявок: {total}\n")
                text1.insert("end", f"   Выполнено: {completed}\n")
                text1.insert("end", f"   В работе: {in_progress}\n")
                text1.insert("end", f"   Среднее время: {avg_days} дней\n\n")
            
            tab2 = tabview.tab("По типам неисправностей")
            self.cursor.execute("""
                SELECT 
                    dt.type_name,
                    COUNT(r.request_id) as count,
                    ROUND(COUNT(r.request_id) * 100.0 / (SELECT COUNT(*) FROM repair_requests), 2) as percent
                FROM device_types dt
                LEFT JOIN repair_requests r ON dt.type_id = r.device_type_id
                GROUP BY dt.type_name
                ORDER BY count DESC
            """)
            rows = self.cursor.fetchall()
            
            text2 = ctk.CTkTextbox(tab2, font=("Arial", 13))
            text2.pack(fill="both", expand=True, padx=10, pady=10)
            
            text2.insert("end", "📊 СТАТИСТИКА ПО ТИПАМ УСТРОЙСТВ\n\n")
            for device, count, percent in rows:
                text2.insert("end", f"🔧 {device}\n")
                text2.insert("end", f"   Заявок: {count} ({percent}%)\n\n")
            
            tab3 = tabview.tab("По статусам")
            self.cursor.execute("""
                SELECT 
                    s.status_name,
                    COUNT(r.request_id) as count,
                    ROUND(COUNT(r.request_id) * 100.0 / (SELECT COUNT(*) FROM repair_requests), 2) as percent
                FROM request_statuses s
                LEFT JOIN repair_requests r ON s.status_id = r.status_id
                GROUP BY s.status_name
                ORDER BY count DESC
            """)
            rows = self.cursor.fetchall()
            
            text3 = ctk.CTkTextbox(tab3, font=("Arial", 13))
            text3.pack(fill="both", expand=True, padx=10, pady=10)
            
            text3.insert("end", "📊 СТАТИСТИКА ПО СТАТУСАМ\n\n")
            for status, count, percent in rows:
                text3.insert("end", f"📌 {status}\n")
                text3.insert("end", f"   Заявок: {count} ({percent}%)\n\n")
            
            tab4 = tabview.tab("Динамика")
            self.cursor.execute("""
                SELECT 
                    to_char(creation_date, 'YYYY-MM') as month,
                    COUNT(*) as count
                FROM repair_requests
                GROUP BY to_char(creation_date, 'YYYY-MM')
                ORDER BY month DESC
                LIMIT 12
            """)
            rows = self.cursor.fetchall()
            
            text4 = ctk.CTkTextbox(tab4, font=("Arial", 13))
            text4.pack(fill="both", expand=True, padx=10, pady=10)
            
            text4.insert("end", "📊 ДИНАМИКА ЗАЯВОК ПО МЕСЯЦАМ\n\n")
            for month, count in rows:
                text4.insert("end", f"📅 {month}: {count} заявок\n")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить статистику:\n{e}")

    def export_reports(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Сохранить отчет как"
            )
            if not filename:
                return
            
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["ID", "Клиент", "Телефон", "Тип устройства", "Модель", "Проблема", "Статус", "Мастер", "Дата создания", "Дата завершения", "Комментарий", "Запчасти"])
                
                self.cursor.execute("""
                    SELECT 
                        r.request_id,
                        c.last_name || ' ' || c.first_name || COALESCE(' ' || c.middle_name, ''),
                        c.phone,
                        dt.type_name,
                        r.device_model,
                        r.problem_description,
                        s.status_name,
                        COALESCE(t.last_name || ' ' || t.first_name, 'Не назначен'),
                        r.creation_date,
                        COALESCE(r.completion_date::TEXT, ''),
                        COALESCE(r.master_comment, ''),
                        COALESCE(r.parts_needed, '')
                    FROM repair_requests r
                    LEFT JOIN clients c ON r.client_id = c.client_id
                    LEFT JOIN technicians t ON r.technician_id = t.technician_id
                    LEFT JOIN device_types dt ON r.device_type_id = dt.type_id
                    LEFT JOIN request_statuses s ON r.status_id = s.status_id
                    ORDER BY r.creation_date DESC
                """)
                
                for row in self.cursor.fetchall():
                    writer.writerow(row)
            
            messagebox.showinfo("Успех", f"Отчет сохранен в файл:\n{filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать отчет:\n{e}")

    def get_selected_id(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите заявку из списка")
            return None
        return self.tree.item(selection[0])['values'][0]

    def can_edit_request(self, request_id):
        if self.current_user['role'] in ['Администратор', 'Менеджер']:
            return True
        elif self.current_user['role'] == 'Клиент':
            try:
                self.cursor.execute("""
                    SELECT r.status_id, s.status_name
                    FROM repair_requests r
                    JOIN request_statuses s ON r.status_id = s.status_id
                    WHERE r.request_id = %s AND r.client_id = %s
                """, (request_id, self.current_user['client_id']))
                result = self.cursor.fetchone()
                return result and result[1] == 'Новая'
            except:
                return False
        return False

    def can_delete_request(self):
        return self.current_user['role'] == 'Администратор'

    def can_add_request(self):
        return self.current_user['role'] in ['Администратор', 'Клиент']

    def delete_request(self):
        if not self.can_delete_request():
            messagebox.showerror("Ошибка", "У вас нет прав для удаления заявок")
            return

        request_id = self.get_selected_id()
        if not request_id:
            return

        result = messagebox.askyesno("Подтверждение удаления", f"Вы уверены, что хотите удалить заявку №{request_id}?\n\nЭто действие нельзя отменить!", icon='warning')

        if result:
            try:
                self.cursor.execute("DELETE FROM repair_requests WHERE request_id = %s", (request_id,))
                self.conn.commit()
                messagebox.showinfo("Успех", f"✅ Заявка №{request_id} успешно удалена")
                self.load_requests()
                self.status_label.configure(text=f"✅ Заявка {request_id} удалена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить заявку:\n{e}")

    def open_add_window(self):
        if not self.can_add_request():
            messagebox.showerror("Ошибка", "У вас нет прав для добавления заявок")
            return
        AddRequestWindow(self.window, self)

    def open_edit_window(self):
        request_id = self.get_selected_id()
        if not request_id:
            return

        if not self.can_edit_request(request_id):
            messagebox.showerror("Ошибка", "Вы не можете редактировать эту заявку")
            return

        if self.current_user['role'] == 'Менеджер':
            AssignTechnicianWindow(self.window, self, request_id)
        else:
            EditRequestWindow(self.window, self, request_id)

    def open_clients_window(self):
        if not self.can_manage_clients():
            messagebox.showerror("Ошибка", "У вас нет прав для управления клиентами")
            return
        ClientsWindow(self.window, self)

    def can_manage_clients(self):
        return self.current_user['role'] == 'Администратор'

    def __del__(self):
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            print("🔌 Соединение с БД закрыто")

class AssignTechnicianWindow(ctk.CTkToplevel):
    def __init__(self, parent, app, request_id):
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.request_id = request_id

        self.title(f"Назначение мастера на заявку №{request_id}")
        self.geometry("600x700")
        self.minsize(600, 700)
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self.load_request_data()
        self.create_widgets()

    def load_request_data(self):
        try:
            query = """
                SELECT 
                    c.last_name || ' ' || c.first_name || COALESCE(' ' || c.middle_name, ''),
                    c.phone,
                    dt.type_name,
                    r.device_model,
                    s.status_name,
                    COALESCE(t.last_name || ' ' || t.first_name, 'Не назначен'),
                    COALESCE(r.master_comment, ''),
                    COALESCE(r.parts_needed, '')
                FROM repair_requests r
                JOIN clients c ON r.client_id = c.client_id
                JOIN device_types dt ON r.device_type_id = dt.type_id
                JOIN request_statuses s ON r.status_id = s.status_id
                LEFT JOIN technicians t ON r.technician_id = t.technician_id
                WHERE r.request_id = %s
            """
            self.app.cursor.execute(query, (self.request_id,))
            self.request_data = self.app.cursor.fetchone()

            if not self.request_data:
                messagebox.showerror("Ошибка", "Заявка не найдена")
                self.destroy()
                return

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные заявки:\n{e}")
            self.destroy()

    def create_widgets(self):
        scroll_frame = ctk.CTkScrollableFrame(self, width=580, height=500)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(scroll_frame, text=f"НАЗНАЧЕНИЕ МАСТЕРА НА ЗАЯВКУ №{self.request_id}", font=("Arial", 22, "bold"), text_color="#2c3e50").pack(pady=(0, 20))

        info_frame = ctk.CTkFrame(scroll_frame, corner_radius=10, fg_color="#f8f9fa")
        info_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(info_frame, text="📋 ИНФОРМАЦИЯ О ЗАЯВКЕ", font=("Arial", 18, "bold")).pack(pady=10)

        info_items = [
            ("Клиент:", self.request_data[0]),
            ("Телефон:", self.request_data[1]),
            ("Устройство:", f"{self.request_data[2]} {self.request_data[3]}"),
            ("Статус:", self.request_data[4]),
            ("Текущий мастер:", self.request_data[5])
        ]

        for label, value in info_items:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(row, text=label, font=("Arial", 14, "bold"), width=120).pack(side="left")
            ctk.CTkLabel(row, text=value, font=("Arial", 14)).pack(side="left", padx=10)

        ctk.CTkFrame(scroll_frame, height=2, fg_color="gray").pack(fill="x", pady=15)

        master_frame = ctk.CTkFrame(scroll_frame, corner_radius=10, fg_color="#e8f5e9")
        master_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(master_frame, text="👨‍🔧 НАЗНАЧЕНИЕ МАСТЕРА", font=("Arial", 18, "bold"), text_color="#2e7d32").pack(pady=10)
        ctk.CTkLabel(master_frame, text="Выберите мастера для выполнения работы:", font=("Arial", 14)).pack()
        self.load_technicians(master_frame)

        ctk.CTkFrame(scroll_frame, height=2, fg_color="gray").pack(fill="x", pady=15)

        status_frame = ctk.CTkFrame(scroll_frame, corner_radius=10, fg_color="#e3f2fd")
        status_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(status_frame, text="📊 ИЗМЕНЕНИЕ СТАТУСА", font=("Arial", 18, "bold"), text_color="#1565c0").pack(pady=10)
        ctk.CTkLabel(status_frame, text="Выберите новый статус заявки:", font=("Arial", 14)).pack()
        self.load_statuses(status_frame)

        ctk.CTkFrame(scroll_frame, height=2, fg_color="gray").pack(fill="x", pady=15)

        comment_frame = ctk.CTkFrame(scroll_frame, corner_radius=10, fg_color="#fff3e0")
        comment_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(comment_frame, text="💬 КОММЕНТАРИЙ МАСТЕРА", font=("Arial", 18, "bold"), text_color="#e65100").pack(pady=10)
        ctk.CTkLabel(comment_frame, text="Добавьте комментарий к работе:", font=("Arial", 14)).pack()

        self.comment_text = ctk.CTkTextbox(comment_frame, width=500, height=80, font=("Arial", 13))
        self.comment_text.pack(pady=10, padx=20)
        if self.request_data[6]:
            self.comment_text.insert("1.0", self.request_data[6])

        ctk.CTkFrame(scroll_frame, height=2, fg_color="gray").pack(fill="x", pady=15)

        parts_frame = ctk.CTkFrame(scroll_frame, corner_radius=10, fg_color="#ffebee")
        parts_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(parts_frame, text="🔧 ЗАПЧАСТИ И МАТЕРИАЛЫ", font=("Arial", 18, "bold"), text_color="#c62828").pack(pady=10)
        ctk.CTkLabel(parts_frame, text="Укажите необходимые запчасти:", font=("Arial", 14)).pack()

        self.parts_text = ctk.CTkTextbox(parts_frame, width=500, height=80, font=("Arial", 13))
        self.parts_text.pack(pady=10, padx=20)
        if self.request_data[7]:
            self.parts_text.insert("1.0", self.request_data[7])

        button_frame = ctk.CTkFrame(self, fg_color="transparent", height=80)
        button_frame.pack(fill="x", padx=20, pady=(10, 20), side="bottom")
        button_frame.pack_propagate(False)

        save_btn = ctk.CTkButton(button_frame, text="💾 СОХРАНИТЬ ИЗМЕНЕНИЯ", command=self.assign_technician, fg_color="#2e7d32", hover_color="#1b5e20", width=250, height=50, font=("Arial", 16, "bold"), corner_radius=8)
        save_btn.pack(side="left", padx=10, expand=True)

        cancel_btn = ctk.CTkButton(button_frame, text="✖ ОТМЕНА", command=self.destroy, fg_color="#c62828", hover_color="#b71c1c", width=200, height=50, font=("Arial", 16, "bold"), corner_radius=8)
        cancel_btn.pack(side="left", padx=10, expand=True)

    def load_technicians(self, parent_frame):
        try:
            self.app.cursor.execute("""
                SELECT technician_id, 
                       last_name || ' ' || first_name || COALESCE(' ' || middle_name, '') as full_name
                FROM technicians 
                ORDER BY last_name, first_name
            """)
            techs = self.app.cursor.fetchall()
            
            tech_list = [t[1] for t in techs]
            self.technician_values = {tech_list[i]: techs[i][0] for i in range(len(techs))}
            
            tech_list.insert(0, "Не назначен")
            self.technician_values["Не назначен"] = None
            
            self.technician_combo = ctk.CTkComboBox(parent_frame, values=tech_list, width=500, height=40, font=("Arial", 14), dropdown_font=("Arial", 13))
            self.technician_combo.pack(pady=10, padx=20)
            
            if self.request_data[5] != "Не назначен":
                self.technician_combo.set(self.request_data[5])
            else:
                self.technician_combo.set("Не назначен")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить список мастеров:\n{e}")
            self.technician_combo = ctk.CTkComboBox(parent_frame, values=["Не назначен"], width=500, height=40)
            self.technician_combo.pack(pady=10, padx=20)

    def load_statuses(self, parent_frame):
        try:
            self.app.cursor.execute("SELECT status_name FROM request_statuses ORDER BY status_id")
            statuses = [row[0] for row in self.app.cursor.fetchall()]
            
            self.status_combo = ctk.CTkComboBox(parent_frame, values=statuses, width=500, height=40, font=("Arial", 14), dropdown_font=("Arial", 13))
            self.status_combo.pack(pady=10, padx=20)
            self.status_combo.set(self.request_data[4])
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить статусы:\n{e}")
            statuses = ['Новая', 'В работе', 'Выполнена']
            self.status_combo = ctk.CTkComboBox(parent_frame, values=statuses, width=500, height=40)
            self.status_combo.pack(pady=10, padx=20)

    def assign_technician(self):
        try:
            selected_tech = self.technician_combo.get()
            selected_status = self.status_combo.get()
            comment = self.comment_text.get("1.0", "end-1c").strip()
            parts = self.parts_text.get("1.0", "end-1c").strip()
            
            if not selected_tech or not selected_status:
                messagebox.showerror("Ошибка", "Выберите мастера и статус")
                return
            
            technician_id = self.technician_values.get(selected_tech)
            
            self.app.cursor.execute("SELECT status_id FROM request_statuses WHERE status_name = %s", (selected_status,))
            status_result = self.app.cursor.fetchone()
            if not status_result:
                messagebox.showerror("Ошибка", "Выбранный статус не найден")
                return
            status_id = status_result[0]

            old_status = self.request_data[4]
            
            self.app.cursor.execute("""
                UPDATE repair_requests 
                SET technician_id = %s,
                    status_id = %s,
                    master_comment = %s,
                    parts_needed = %s
                WHERE request_id = %s
            """, (technician_id, status_id, comment, parts, self.request_id))

            if selected_status == 'Выполнена':
                self.app.cursor.execute("""
                    UPDATE repair_requests 
                    SET completion_date = %s
                    WHERE request_id = %s AND completion_date IS NULL
                """, (datetime.now().date(), self.request_id))

            self.app.cursor.execute("SELECT client_id FROM repair_requests WHERE request_id = %s", (self.request_id,))
            client_id = self.app.cursor.fetchone()[0]
            
            self.app.cursor.execute("SELECT user_id FROM users WHERE client_id = %s", (client_id,))
            user = self.app.cursor.fetchone()
            if user:
                self.app.add_notification(user[0], self.request_id, f"Статус вашей заявки №{self.request_id} изменен на '{selected_status}'")
            
            if selected_status != old_status:
                self.app.cursor.execute("""
                    INSERT INTO request_history (request_id, user_id, action, old_status_id, new_status_id, comment)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (self.request_id, self.app.current_user['id'], 'Статус изменен', 
                      (self.app.cursor.execute("SELECT status_id FROM request_statuses WHERE status_name = %s", (old_status,)) or old_status),
                      status_id, f"Мастер: {selected_tech}"))

            self.app.conn.commit()
            messagebox.showinfo("Успех", "✅ Изменения успешно сохранены")
            self.app.load_requests()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить изменения:\n{e}")

class AddRequestWindow(ctk.CTkToplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.parent = parent
        self.app = app

        self.title("Новая заявка на ремонт")
        self.geometry("450x600")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        ctk.CTkLabel(self, text="ДОБАВЛЕНИЕ НОВОЙ ЗАЯВКИ", font=("Arial", 16, "bold")).pack(pady=10)

        self.fields = {}

        if self.app.current_user['role'] == 'Клиент':
            ctk.CTkLabel(self, text="ФИО клиента").pack(pady=(10, 0))
            client_name = ctk.CTkEntry(self, width=350)
            client_name.insert(0, self.app.current_user['client_name'] or "")
            client_name.configure(state="disabled")
            client_name.pack(pady=5)

            ctk.CTkLabel(self, text="Телефон").pack()
            client_phone = ctk.CTkEntry(self, width=350)
            self.app.cursor.execute("SELECT phone FROM clients WHERE client_id = %s", (self.app.current_user['client_id'],))
            phone = self.app.cursor.fetchone()
            if phone:
                client_phone.insert(0, phone[0])
            client_phone.configure(state="disabled")
            client_phone.pack(pady=5)

            self.fields['client_id'] = self.app.current_user['client_id']
        else:
            ctk.CTkLabel(self, text="Выберите клиента *").pack(pady=(10, 0))
            self.load_clients()
            self.fields['client_combo'].pack(pady=5)

        ctk.CTkLabel(self, text="Тип устройства *").pack()
        self.load_device_types()
        self.fields['device_type'].pack(pady=5)

        ctk.CTkLabel(self, text="Модель *").pack()
        self.fields['model'] = ctk.CTkEntry(self, width=350, placeholder_text="Samsung WW90T")
        self.fields['model'].pack(pady=5)

        ctk.CTkLabel(self, text="Описание проблемы").pack()
        self.fields['problem'] = ctk.CTkTextbox(self, width=350, height=100)
        self.fields['problem'].pack(pady=5)

        if self.app.current_user['role'] == 'Администратор':
            ctk.CTkLabel(self, text="Статус").pack()
            self.load_statuses()
            self.fields['status'].pack(pady=5)

        ctk.CTkLabel(self, text="* - обязательные поля", text_color="gray", font=("Arial", 10)).pack(pady=5)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="💾 Сохранить", command=self.save_request, fg_color="green").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="✖ Отмена", command=self.destroy, fg_color="gray").pack(side="left", padx=5)

    def load_clients(self):
        try:
            self.app.cursor.execute("""
                SELECT client_id, last_name || ' ' || first_name || COALESCE(' ' || middle_name, ''), phone
                FROM clients
                ORDER BY last_name, first_name
            """)
            clients = self.app.cursor.fetchall()
            client_list = [f"{c[1]} ({c[2]})" for c in clients]
            self.fields['client_combo'] = ctk.CTkComboBox(self, values=client_list, width=350)
            self.fields['client_values'] = {client_list[i]: clients[i][0] for i in range(len(clients))}
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить список клиентов:\n{e}")

    def load_device_types(self):
        try:
            self.app.cursor.execute("SELECT type_name FROM device_types ORDER BY type_name")
            device_types = [row[0] for row in self.app.cursor.fetchall()]
        except:
            device_types = ['Стиральная машина', 'Холодильник', 'Телевизор']

        self.fields['device_type'] = ctk.CTkComboBox(self, values=device_types, width=350)
        if device_types:
            self.fields['device_type'].set(device_types[0])

    def load_statuses(self):
        try:
            self.app.cursor.execute("SELECT status_name FROM request_statuses ORDER BY status_id")
            statuses = [row[0] for row in self.app.cursor.fetchall()]
        except:
            statuses = ['Новая']

        self.fields['status'] = ctk.CTkComboBox(self, values=statuses, width=350)
        if statuses:
            self.fields['status'].set(statuses[0])

    def save_request(self):
        try:
            if self.app.current_user['role'] == 'Клиент':
                client_id = self.app.current_user['client_id']
            else:
                selected = self.fields['client_combo'].get()
                if not selected:
                    messagebox.showerror("Ошибка", "Выберите клиента")
                    return
                client_id = self.fields['client_values'][selected]

            if not self.fields['model'].get().strip():
                messagebox.showerror("Ошибка", "Введите модель устройства")
                return

            self.app.cursor.execute("SELECT type_id FROM device_types WHERE type_name = %s", (self.fields['device_type'].get(),))
            type_id = self.app.cursor.fetchone()[0]

            if self.app.current_user['role'] == 'Администратор' and 'status' in self.fields:
                self.app.cursor.execute("SELECT status_id FROM request_statuses WHERE status_name = %s", (self.fields['status'].get(),))
                status_id = self.app.cursor.fetchone()[0]
            else:
                self.app.cursor.execute("SELECT status_id FROM request_statuses WHERE status_name = 'Новая'")
                status_id = self.app.cursor.fetchone()[0]

            self.app.cursor.execute("""
                INSERT INTO repair_requests 
                (client_id, device_type_id, device_model, problem_description, status_id, creation_date, master_comment, parts_needed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                client_id, type_id,
                self.fields['model'].get().strip(),
                self.fields['problem'].get("1.0", "end-1c").strip() or None,
                status_id,
                datetime.now(),
                '',
                ''
            ))

            self.app.conn.commit()
            messagebox.showinfo("Успех", "✅ Заявка успешно добавлена")
            self.app.load_requests()
            self.app.status_label.configure(text="✅ Новая заявка добавлена")
            self.destroy()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить заявку:\n{e}")

class EditRequestWindow(ctk.CTkToplevel):
    def __init__(self, parent, app, request_id):
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.request_id = request_id

        self.title(f"Редактирование заявки №{request_id}")
        self.geometry("450x600")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self.load_request_data()
        self.create_widgets()

    def load_request_data(self):
        try:
            query = """
                SELECT 
                    r.client_id,
                    c.last_name || ' ' || c.first_name || COALESCE(' ' || c.middle_name, ''),
                    c.phone,
                    dt.type_name,
                    r.device_model,
                    r.problem_description,
                    s.status_name,
                    COALESCE(r.master_comment, ''),
                    COALESCE(r.parts_needed, '')
                FROM repair_requests r
                JOIN clients c ON r.client_id = c.client_id
                JOIN device_types dt ON r.device_type_id = dt.type_id
                JOIN request_statuses s ON r.status_id = s.status_id
                WHERE r.request_id = %s
            """
            self.app.cursor.execute(query, (self.request_id,))
            self.request_data = self.app.cursor.fetchone()

            if not self.request_data:
                messagebox.showerror("Ошибка", "Заявка не найдена")
                self.destroy()
                return

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные заявки:\n{e}")
            self.destroy()

    def create_widgets(self):
        ctk.CTkLabel(self, text=f"РЕДАКТИРОВАНИЕ ЗАЯВКИ №{self.request_id}", font=("Arial", 16, "bold")).pack(pady=10)

        self.fields = {}

        ctk.CTkLabel(self, text="Клиент").pack(pady=(10, 0))
        client_info = ctk.CTkEntry(self, width=350)
        client_info.insert(0, f"{self.request_data[1]} ({self.request_data[2]})")
        client_info.configure(state="disabled")
        client_info.pack(pady=5)

        ctk.CTkLabel(self, text="Тип устройства *").pack()
        self.load_device_types()
        self.fields['device_type'].set(self.request_data[3])
        self.fields['device_type'].pack(pady=5)

        ctk.CTkLabel(self, text="Модель *").pack()
        self.fields['model'] = ctk.CTkEntry(self, width=350)
        self.fields['model'].insert(0, self.request_data[4] or "")
        self.fields['model'].pack(pady=5)

        ctk.CTkLabel(self, text="Описание проблемы").pack()
        self.fields['problem'] = ctk.CTkTextbox(self, width=350, height=100)
        if self.request_data[5]:
            self.fields['problem'].insert("1.0", self.request_data[5])
        self.fields['problem'].pack(pady=5)

        if self.app.current_user['role'] == 'Администратор':
            ctk.CTkLabel(self, text="Статус").pack()
            self.load_statuses()
            self.fields['status'].set(self.request_data[6])
            self.fields['status'].pack(pady=5)
        else:
            ctk.CTkLabel(self, text="Статус").pack()
            status_entry = ctk.CTkEntry(self, width=350)
            status_entry.insert(0, self.request_data[6])
            status_entry.configure(state="disabled")
            status_entry.pack(pady=5)

        ctk.CTkLabel(self, text="Комментарий мастера").pack()
        self.comment_text = ctk.CTkTextbox(self, width=350, height=60)
        if self.request_data[7]:
            self.comment_text.insert("1.0", self.request_data[7])
        self.comment_text.pack(pady=5)

        ctk.CTkLabel(self, text="Запчасти и материалы").pack()
        self.parts_text = ctk.CTkTextbox(self, width=350, height=60)
        if self.request_data[8]:
            self.parts_text.insert("1.0", self.request_data[8])
        self.parts_text.pack(pady=5)

        ctk.CTkLabel(self, text="* - обязательные поля", text_color="gray", font=("Arial", 10)).pack(pady=5)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="💾 Сохранить", command=self.save_request, fg_color="green").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="✖ Отмена", command=self.destroy, fg_color="gray").pack(side="left", padx=5)

    def load_device_types(self):
        try:
            self.app.cursor.execute("SELECT type_name FROM device_types ORDER BY type_name")
            device_types = [row[0] for row in self.app.cursor.fetchall()]
        except:
            device_types = ['Стиральная машина', 'Холодильник', 'Телевизор']

        self.fields['device_type'] = ctk.CTkComboBox(self, values=device_types, width=350)

    def load_statuses(self):
        try:
            self.app.cursor.execute("SELECT status_name FROM request_statuses ORDER BY status_id")
            statuses = [row[0] for row in self.app.cursor.fetchall()]
        except:
            statuses = ['Новая']

        self.fields['status'] = ctk.CTkComboBox(self, values=statuses, width=350)

    def save_request(self):
        try:
            if not self.fields['model'].get().strip():
                messagebox.showerror("Ошибка", "Введите модель устройства")
                return

            self.app.cursor.execute("SELECT type_id FROM device_types WHERE type_name = %s", (self.fields['device_type'].get(),))
            type_id = self.app.cursor.fetchone()[0]

            if self.app.current_user['role'] == 'Администратор' and 'status' in self.fields:
                self.app.cursor.execute("SELECT status_id FROM request_statuses WHERE status_name = %s", (self.fields['status'].get(),))
                status_id = self.app.cursor.fetchone()[0]
                
                if self.fields['status'].get() == 'Выполнена':
                    self.app.cursor.execute("""
                        UPDATE repair_requests 
                        SET completion_date = %s
                        WHERE request_id = %s AND completion_date IS NULL
                    """, (datetime.now().date(), self.request_id))
            else:
                self.app.cursor.execute("SELECT status_id FROM request_statuses WHERE status_name = %s", (self.request_data[6],))
                status_id = self.app.cursor.fetchone()[0]

            comment = self.comment_text.get("1.0", "end-1c").strip()
            parts = self.parts_text.get("1.0", "end-1c").strip()

            self.app.cursor.execute("""
                UPDATE repair_requests 
                SET device_type_id = %s,
                    device_model = %s,
                    problem_description = %s,
                    master_comment = %s,
                    parts_needed = %s
                WHERE request_id = %s
            """, (
                type_id,
                self.fields['model'].get().strip(),
                self.fields['problem'].get("1.0", "end-1c").strip() or None,
                comment,
                parts,
                self.request_id
            ))

            self.app.conn.commit()
            messagebox.showinfo("Успех", "✅ Заявка успешно обновлена")
            self.app.load_requests()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить изменения:\n{e}")

class ClientsWindow(ctk.CTkToplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.parent = parent
        self.app = app

        self.title("Управление клиентами")
        self.geometry("900x500")

        self.create_widgets()
        self.load_clients()

    def create_widgets(self):
        ctk.CTkLabel(self, text="КЛИЕНТЫ", font=("Arial", 18, "bold")).pack(pady=10)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(btn_frame, text="➕ Добавить клиента", command=self.add_client, fg_color="green").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="✏️ Редактировать", command=self.edit_client, fg_color="blue").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🗑️ Удалить", command=self.delete_client, fg_color="red").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="← Назад", command=self.destroy, fg_color="gray").pack(side="right", padx=5)

        search_frame = ctk.CTkFrame(btn_frame)
        search_frame.pack(side="right", padx=5)

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Поиск клиентов...", width=200)
        self.search_entry.pack(side="left", padx=5)

        ctk.CTkButton(search_frame, text="🔍", command=self.search_clients, width=30).pack(side="left")

        columns = ('ID', 'Фамилия', 'Имя', 'Отчество', 'Телефон', 'Email', 'Логин')
        self.tree = ttk.Treeview(self, columns=columns, show='headings', height=15)

        widths = [50, 150, 150, 150, 120, 200, 100]
        for col, width in zip(columns, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)

    def load_clients(self, search_term=None):
        try:
            if search_term:
                query = """
                    SELECT 
                        c.client_id, c.last_name, c.first_name, c.middle_name, 
                        c.phone, c.email, u.username
                    FROM clients c
                    LEFT JOIN users u ON c.client_id = u.client_id
                    WHERE 
                        c.last_name ILIKE %s OR
                        c.first_name ILIKE %s OR
                        c.phone ILIKE %s OR
                        c.email ILIKE %s OR
                        u.username ILIKE %s
                    ORDER BY c.last_name, c.first_name
                """
                like_pattern = f'%{search_term}%'
                params = [like_pattern] * 5
                self.app.cursor.execute(query, params)
            else:
                query = """
                    SELECT 
                        c.client_id, c.last_name, c.first_name, c.middle_name, 
                        c.phone, c.email, u.username
                    FROM clients c
                    LEFT JOIN users u ON c.client_id = u.client_id
                    ORDER BY c.last_name, c.first_name
                """
                self.app.cursor.execute(query)

            rows = self.app.cursor.fetchall()

            for row in self.tree.get_children():
                self.tree.delete(row)

            for row in rows:
                self.tree.insert('', 'end', values=row)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить клиентов:\n{e}")

    def search_clients(self):
        search_text = self.search_entry.get().strip()
        self.load_clients(search_text if search_text else None)

    def get_selected_id(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите клиента из списка")
            return None
        return self.tree.item(selection[0])['values'][0]

    def add_client(self):
        self.edit_client_dialog()

    def edit_client(self):
        client_id = self.get_selected_id()
        if client_id:
            self.edit_client_dialog(client_id)

    def edit_client_dialog(self, client_id=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Редактирование клиента" if client_id else "Новый клиент")
        dialog.geometry("450x550")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="ДАННЫЕ КЛИЕНТА", font=("Arial", 16, "bold")).pack(pady=10)

        fields = {}

        ctk.CTkLabel(dialog, text="Фамилия *").pack()
        fields['last_name'] = ctk.CTkEntry(dialog, width=350)
        fields['last_name'].pack(pady=5)

        ctk.CTkLabel(dialog, text="Имя *").pack()
        fields['first_name'] = ctk.CTkEntry(dialog, width=350)
        fields['first_name'].pack(pady=5)

        ctk.CTkLabel(dialog, text="Отчество").pack()
        fields['middle_name'] = ctk.CTkEntry(dialog, width=350)
        fields['middle_name'].pack(pady=5)

        ctk.CTkLabel(dialog, text="Телефон *").pack()
        fields['phone'] = ctk.CTkEntry(dialog, width=350, placeholder_text="+7(999)123-45-67")
        fields['phone'].pack(pady=5)

        ctk.CTkLabel(dialog, text="Email").pack()
        fields['email'] = ctk.CTkEntry(dialog, width=350, placeholder_text="email@example.com")
        fields['email'].pack(pady=5)

        ctk.CTkLabel(dialog, text="ЛОГИН И ПАРОЛЬ", font=("Arial", 14, "bold")).pack(pady=(15, 5))
        
        ctk.CTkLabel(dialog, text="Логин").pack()
        fields['login'] = ctk.CTkEntry(dialog, width=350, placeholder_text="от 3 до 20 символов")
        fields['login'].pack(pady=5)

        ctk.CTkLabel(dialog, text="Пароль").pack()
        fields['password'] = ctk.CTkEntry(dialog, width=350, placeholder_text="минимум 6 символов", show="*")
        fields['password'].pack(pady=5)

        if client_id:
            try:
                self.app.cursor.execute("""SELECT last_name, first_name, middle_name, phone, email FROM clients WHERE client_id = %s""", (client_id,))
                client = self.app.cursor.fetchone()
                if client:
                    fields['last_name'].insert(0, client[0] or "")
                    fields['first_name'].insert(0, client[1] or "")
                    fields['middle_name'].insert(0, client[2] or "")
                    fields['phone'].insert(0, client[3] or "")
                    fields['email'].insert(0, client[4] or "")
                
                self.app.cursor.execute("SELECT username, password_hash FROM users WHERE client_id = %s", (client_id,))
                user = self.app.cursor.fetchone()
                if user:
                    fields['login'].insert(0, user[0] or "")
                    fields['password'].insert(0, "********")
                    
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить данные:\n{e}")

        ctk.CTkLabel(dialog, text="* - обязательные поля", text_color="gray", font=("Arial", 10)).pack(pady=5)

        def save():
            last_name = fields['last_name'].get().strip()
            first_name = fields['first_name'].get().strip()
            phone = fields['phone'].get().strip()
            email = fields['email'].get().strip()
            login = fields['login'].get().strip()
            password = fields['password'].get().strip()

            if not last_name or not first_name or not phone or not login or not password:
                messagebox.showerror("Ошибка", "Заполните все обязательные поля")
                return

            if not Validators.validate_name(last_name) or not Validators.validate_name(first_name):
                messagebox.showerror("Ошибка", "ФИО должно содержать только буквы")
                return

            if not Validators.validate_phone(phone):
                messagebox.showerror("Ошибка", "Телефон должен быть в формате +7(999)123-45-67")
                return

            if email and not Validators.validate_email(email):
                messagebox.showerror("Ошибка", "Введите корректный email")
                return

            if not Validators.validate_login(login):
                messagebox.showerror("Ошибка", "Логин должен содержать только буквы и цифры (3-20 символов)")
                return

            if not Validators.validate_password(password) and password != "********":
                messagebox.showerror("Ошибка", "Пароль должен быть минимум 6 символов")
                return

            try:
                self.app.cursor.execute("BEGIN")

                if client_id:
                    query = """
                        UPDATE clients 
                        SET last_name=%s, first_name=%s, middle_name=%s, phone=%s, email=%s
                        WHERE client_id=%s
                    """
                    params = (last_name, first_name, fields['middle_name'].get().strip() or None, phone, email or None, client_id)
                    self.app.cursor.execute(query, params)
                    
                    if password != "********":
                        password_hash = Validators.hash_password(password)
                        query = """
                            UPDATE users 
                            SET username=%s, password_hash=%s
                            WHERE client_id=%s
                        """
                        self.app.cursor.execute(query, (login, password_hash, client_id))
                    else:
                        query = """
                            UPDATE users 
                            SET username=%s
                            WHERE client_id=%s
                        """
                        self.app.cursor.execute(query, (login, client_id))
                    
                else:
                    query = """
                        INSERT INTO clients (last_name, first_name, middle_name, phone, email)
                        VALUES (%s, %s, %s, %s, %s) RETURNING client_id
                    """
                    params = (last_name, first_name, fields['middle_name'].get().strip() or None, phone, email or None)
                    self.app.cursor.execute(query, params)
                    client_id = self.app.cursor.fetchone()[0]

                    self.app.cursor.execute("SELECT role_id FROM roles WHERE role_name = 'Клиент'")
                    role_id = self.app.cursor.fetchone()[0]

                    password_hash = Validators.hash_password(password)

                    self.app.cursor.execute("""
                        INSERT INTO users (username, password_hash, role_id, client_id)
                        VALUES (%s, %s, %s, %s)
                    """, (login, password_hash, role_id, client_id))

                self.app.conn.commit()
                messagebox.showinfo("Успех", "Данные сохранены")
                dialog.destroy()
                self.load_clients()

            except psycopg2.IntegrityError as e:
                self.app.conn.rollback()
                if "username" in str(e):
                    messagebox.showerror("Ошибка", "Пользователь с таким логином уже существует")
                elif "phone" in str(e):
                    messagebox.showerror("Ошибка", "Клиент с таким телефоном уже существует")
                else:
                    messagebox.showerror("Ошибка", f"Ошибка базы данных:\n{e}")
            except Exception as e:
                self.app.conn.rollback()
                messagebox.showerror("Ошибка", f"Не удалось сохранить:\n{e}")

        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="💾 Сохранить", command=save, fg_color="green").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="✖ Отмена", command=dialog.destroy, fg_color="gray").pack(side="left", padx=5)

    def delete_client(self):
        client_id = self.get_selected_id()
        if not client_id:
            return

        try:
            self.app.cursor.execute("SELECT COUNT(*) FROM repair_requests WHERE client_id = %s", (client_id,))
            count = self.app.cursor.fetchone()[0]

            if count > 0:
                result = messagebox.askyesno("Подтверждение", f"У клиента есть {count} заявок. При удалении клиента все его заявки также будут удалены.\n\nПродолжить?", icon='warning')
            else:
                result = messagebox.askyesno("Подтверждение", "Удалить клиента?", icon='question')

            if result:
                self.app.cursor.execute("DELETE FROM clients WHERE client_id = %s", (client_id,))
                self.app.conn.commit()
                messagebox.showinfo("Успех", "Клиент удален")
                self.load_clients()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить клиента:\n{e}")

if __name__ == "__main__":
    app = RepairServiceApp()