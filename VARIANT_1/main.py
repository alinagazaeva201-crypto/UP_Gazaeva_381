import customtkinter as ctk
from tkinter import messagebox, ttk
import psycopg2
from datetime import datetime
import re
import hashlib

DB_CONFIG = {
    'dbname': 'repair_service',
    'user': 'postgres',
    'password': '123qwe',
    'host': 'localhost',
    'port': '5432'
}


class Validators:
    """Класс с методами валидации данных"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Проверка корректности email"""
        if not email:
            return True
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Проверка телефона в формате +7(XXX)XXX-XX-XX"""
        pattern = r'^\+7\(\d{3}\)\d{3}-\d{2}-\d{2}$'
        return re.match(pattern, phone) is not None

    @staticmethod
    def validate_name(name: str) -> bool:
        """Проверка ФИО (только буквы и пробелы)"""
        return bool(re.match(r'^[А-Яа-яA-Za-z\s-]+$', name.strip()))

    @staticmethod
    def validate_login(login: str) -> bool:
        """Проверка логина (только буквы и цифры)"""
        return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', login))

    @staticmethod
    def validate_password(password: str) -> bool:
        """Проверка пароля (минимум 6 символов)"""
        return len(password) >= 6

    @staticmethod
    def hash_password(password: str) -> str:
        """Хеширование пароля"""
        return hashlib.sha256(password.encode()).hexdigest()


class LoginWindow(ctk.CTkToplevel):
    """Окно авторизации и регистрации"""

    def __init__(self, parent, db_manager, on_login_success):
        super().__init__(parent)
        self.parent = parent
        self.db_manager = db_manager
        self.on_login_success = on_login_success

        self.title("Авторизация - Сервисный центр")
        self.geometry("520x520")
        self.resizable(False, False)


        self.transient(parent)
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):

        main_frame = ctk.CTkFrame(self, corner_radius=15)
        main_frame.pack(expand=True, padx=40, pady=40)

        title = ctk.CTkLabel(
            main_frame,
            text="Система учета ремонта техники",
            font=("Arial", 26, "bold")
        )
        title.pack(pady=(20, 10))

        subtitle = ctk.CTkLabel(
            main_frame,
            text="Авторизация",
            font=("Arial", 18)
        )
        subtitle.pack(pady=(0, 20))


        ctk.CTkLabel(
            main_frame,
            text="Логин",
            font=("Arial", 14)
        ).pack(anchor="w")

        self.login_username = ctk.CTkEntry(
            main_frame,
            width=320,
            height=38,
            placeholder_text="Введите логин"
        )
        self.login_username.pack(pady=8)


        ctk.CTkLabel(
            main_frame,
            text="Пароль",
            font=("Arial", 14)
        ).pack(anchor="w")

        self.login_password = ctk.CTkEntry(
            main_frame,
            width=320,
            height=38,
            show="*",
            placeholder_text="Введите пароль"
        )
        self.login_password.pack(pady=8)


        login_btn = ctk.CTkButton(
            main_frame,
            text="🔑 Войти",
            command=self.login,
            width=320,
            height=40,
            font=("Arial", 15)
        )
        login_btn.pack(pady=20)


        test = ctk.CTkLabel(
            main_frame,
            text="Тестовый вход:\nadmin / admin123",
            font=("Arial", 12),
            text_color="gray"
        )
        test.pack(pady=10)

    def create_widgets(self):
        """Создание вкладок входа и регистрации"""

        self.tabview = ctk.CTkTabview(self, width=380, height=420)
        self.tabview.pack(pady=20, padx=20)

        self.tabview.add("Вход")
        self.create_login_tab()

        self.tabview.add("Регистрация")
        self.create_register_tab()

    def create_login_tab(self):
        """Создание вкладки входа"""
        tab = self.tabview.tab("Вход")

        ctk.CTkLabel(
            tab,
            text="ВХОД В СИСТЕМУ",
            font=("Arial", 18, "bold")
        ).pack(pady=30)

        ctk.CTkLabel(tab, text="Логин:").pack()
        self.login_username = ctk.CTkEntry(tab, width=250, placeholder_text="Введите логин")
        self.login_username.pack(pady=5)
        self.login_username.focus()

        ctk.CTkLabel(tab, text="Пароль:").pack()
        self.login_password = ctk.CTkEntry(tab, width=250, placeholder_text="••••••••", show="*")
        self.login_password.pack(pady=5)

        ctk.CTkButton(
            tab,
            text="🔑 Войти",
            command=self.login,
            width=200,
            height=35
        ).pack(pady=20)

        info_text = "Тестовые данные:\nadmin / admin123"
        ctk.CTkLabel(
            tab,
            text=info_text,
            font=("Arial", 10),
            text_color="gray"
        ).pack(pady=10)

        self.login_password.bind('<Return>', lambda e: self.login())

    def create_register_tab(self):
        """Создание вкладки регистрации"""
        tab = self.tabview.tab("Регистрация")

        ctk.CTkLabel(
            tab,
            text="РЕГИСТРАЦИЯ НОВОГО КЛИЕНТА",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        self.reg_fields = {}

        ctk.CTkLabel(tab, text="Логин *").pack()
        self.reg_fields['login'] = ctk.CTkEntry(
            tab, width=250, placeholder_text="от 3 до 20 символов"
        )
        self.reg_fields['login'].pack(pady=5)

        ctk.CTkLabel(tab, text="Пароль *").pack()
        self.reg_fields['password'] = ctk.CTkEntry(
            tab, width=250, placeholder_text="минимум 6 символов", show="*"
        )
        self.reg_fields['password'].pack(pady=5)

        ctk.CTkLabel(tab, text="Подтвердите пароль *").pack()
        self.reg_fields['password_confirm'] = ctk.CTkEntry(
            tab, width=250, placeholder_text="повторите пароль", show="*"
        )
        self.reg_fields['password_confirm'].pack(pady=5)

        ctk.CTkLabel(tab, text="ФИО *").pack()
        self.reg_fields['full_name'] = ctk.CTkEntry(
            tab, width=250, placeholder_text="Иванов Иван Иванович"
        )
        self.reg_fields['full_name'].pack(pady=5)

        ctk.CTkLabel(tab, text="Телефон *").pack()
        self.reg_fields['phone'] = ctk.CTkEntry(
            tab, width=250, placeholder_text="+7(999)123-45-67"
        )
        self.reg_fields['phone'].pack(pady=5)

        ctk.CTkLabel(tab, text="Email").pack()
        self.reg_fields['email'] = ctk.CTkEntry(
            tab, width=250, placeholder_text="email@example.com"
        )
        self.reg_fields['email'].pack(pady=5)

        ctk.CTkButton(
            tab,
            text="📝 Зарегистрироваться",
            command=self.register,
            width=200,
            height=35,
            fg_color="green"
        ).pack(pady=15)

        ctk.CTkLabel(
            tab,
            text="* - обязательные поля",
            font=("Arial", 10),
            text_color="gray"
        ).pack()

    def login(self):
        """Проверка логина и пароля"""
        username = self.login_username.get().strip()
        password = self.login_password.get().strip()

        if not username or not password:
            messagebox.showerror(
                "Ошибка входа",
                "Введите логин и пароль"
            )
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
                messagebox.showerror(
                    "Ошибка входа",
                    "Неверный логин или пароль"
                )
        except Exception as e:
            self.db_manager.cursor.execute("ROLLBACK")
            messagebox.showerror("Ошибка", f"Ошибка при входе:\n{e}")

    def register(self):
        """Регистрация нового клиента"""

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
            messagebox.showerror(
                "Ошибка",
                "Логин должен содержать только буквы и цифры (3-20 символов)"
            )
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

            self.db_manager.cursor.execute(
                "SELECT user_id FROM users WHERE username = %s",
                (login,)
            )
            if self.db_manager.cursor.fetchone():
                messagebox.showerror("Ошибка", "Пользователь с таким логином уже существует")
                self.db_manager.cursor.execute("ROLLBACK")
                return

            self.db_manager.cursor.execute(
                "SELECT client_id FROM clients WHERE phone = %s",
                (phone,)
            )
            if self.db_manager.cursor.fetchone():
                messagebox.showerror("Ошибка", "Клиент с таким телефоном уже зарегистрирован")
                self.db_manager.cursor.execute("ROLLBACK")
                return

            self.db_manager.cursor.execute("""
                INSERT INTO clients (last_name, first_name, middle_name, phone, email)
                VALUES (%s, %s, %s, %s, %s) RETURNING client_id
            """, (last_name, first_name, middle_name, phone, email or None))
            client_id = self.db_manager.cursor.fetchone()[0]

            self.db_manager.cursor.execute(
                "SELECT role_id FROM roles WHERE role_name = 'Клиент'"
            )
            role_id = self.db_manager.cursor.fetchone()[0]

            password_hash = Validators.hash_password(password)

            self.db_manager.cursor.execute("""
                INSERT INTO users (username, password_hash, role_id, client_id)
                VALUES (%s, %s, %s, %s)
            """, (login, password_hash, role_id, client_id))

            self.db_manager.conn.commit()

            messagebox.showinfo(
                "Успех",
                "Регистрация прошла успешно!\nТеперь вы можете войти в систему."
            )

            for field in self.reg_fields.values():
                field.delete(0, 'end')
            self.tabview.set("Вход")

        except Exception as e:
            self.db_manager.conn.rollback()
            messagebox.showerror("Ошибка", f"Не удалось зарегистрироваться:\n{e}")


class RepairServiceApp:
    """Главное окно приложения"""

    def __init__(self):
    
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        self.window = ctk.CTk()
        self.window.title("Учет заявок на ремонт бытовой техники v1.0")
        self.window.geometry("1300x650")

        self.connect_to_db()

        self.current_user = None

        self.window.withdraw()
        self.show_login()

        self.window.mainloop()

    def connect_to_db(self):
        """Подключение к PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print("✅ Подключено к БД")
        except Exception as e:
            messagebox.showerror(
                "Ошибка подключения",
                f"Не удалось подключиться к БД:\n{e}\n\n"
                f"Проверьте:\n"
                f"1. Запущен ли PostgreSQL\n"
                f"2. Создана ли БД 'repair_service'\n"
                f"3. Правильный ли пароль в DB_CONFIG"
            )
            exit(1)

    def show_login(self):
        """Показать окно входа"""
        LoginWindow(self.window, self, self.on_login_success)

    def on_login_success(self, user_data):
        """Callback после успешного входа"""

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
        
        self.status_label.configure(
            text=f"Добро пожаловать, {self.current_user['username']}! "
                 f"Роль: {self.current_user['role']}"
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

        btn_add = ctk.CTkButton(
        toolbar_frame,
        text="➕ Новая заявка",
        command=self.open_add_window,
        width=170,
        height=45,
        font=("Arial", 16),
        fg_color="#00b4d8", 
        hover_color="#0096c7" 
    )
        btn_add.pack(side="left", padx=10, pady=10)

        btn_edit = ctk.CTkButton(
        toolbar_frame,
        text="✏ Редактировать",
        command=self.open_edit_window,
        width=170,
        height=45,
        font=("Arial", 16),
        fg_color="#48cae4",
        hover_color="#00b4d8"
    )
        btn_edit.pack(side="left", padx=10)

        btn_delete = ctk.CTkButton(
            toolbar_frame,
            text="🗑 Удалить",
            command=self.delete_request,
            width=170,
            height=45,
            fg_color="#ba3055",
            hover_color="#ba3055",
            font=("Arial", 16)
        )
        btn_delete.pack(side="left", padx=10)

        btn_refresh = ctk.CTkButton(
            toolbar_frame,
            text="🔄 Обновить",
            command=self.load_requests,
            width=170,
            height=45,
            fg_color="#73a0a4",
            hover_color="#73a0a4",
            font=("Arial", 16)
        )
        btn_refresh.pack(side="left", padx=10)

        btn_stats = ctk.CTkButton(
            toolbar_frame,
            text="📊 Среднее время",
            command=self.show_avg_time,
            width=190,
            height=45,
            fg_color="#3c9298",
            hover_color="#3c9298",
            font=("Arial", 16)
        )
        btn_stats.pack(side="left", padx=10)

        btn_logout = ctk.CTkButton(
            toolbar_frame,
            text="🚪 Выйти",
            command=self.logout,
            width=130,
            height=45,
            fg_color="#3c9298",
            hover_color="#3c9298",
            font=("Arial", 16)
        )
        btn_logout.pack(side="right", padx=15)


        table_frame = ctk.CTkFrame(self.window, corner_radius=12)
        table_frame.pack(fill="both", expand=True, padx=15, pady=10)

        columns = (
            "ID",
            "Клиент",
            "Телефон",
            "Тип устройства",
            "Модель",
            "Проблема",
            "Статус",
            "Мастер",
            "Дата"
        )

        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 13), rowheight=32)
        style.configure("Treeview.Heading", font=("Arial", 14, "bold"))

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=18
        )

        for col in columns:
            self.tree.heading(col, text=col)

        self.tree.column("ID", width=60)
        self.tree.column("Клиент", width=200)
        self.tree.column("Телефон", width=150)
        self.tree.column("Тип устройства", width=160)
        self.tree.column("Модель", width=170)
        self.tree.column("Проблема", width=260)
        self.tree.column("Статус", width=140)
        self.tree.column("Мастер", width=170)
        self.tree.column("Дата", width=120)

        scrollbar_y = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        scrollbar_x = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.tree.xview
        )

        self.tree.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")


        status_frame = ctk.CTkFrame(self.window, height=40, corner_radius=12)
        status_frame.pack(fill="x", padx=15, pady=10)

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Готово к работе",
            font=("Arial", 14)
        )
        self.status_label.pack(side="left", padx=15, pady=5)

        self.count_label = ctk.CTkLabel(
            status_frame,
            text="",
            font=("Arial", 14)
        )
        self.count_label.pack(side="right", padx=15)

    def logout(self):
        """Выход из системы"""
        result = messagebox.askyesno("Выход", "Вы действительно хотите выйти?")
        if result:
            self.window.withdraw()
            self.current_user = None
    
            for row in self.tree.get_children():
                self.tree.delete(row)
   
            self.show_login()

    def load_requests(self):
        """Загрузка списка заявок"""
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
                        to_char(r.creation_date, 'DD.MM.YYYY') as date
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
                        to_char(r.creation_date, 'DD.MM.YYYY') as date
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
        """Поиск заявок (только для админа и менеджера)"""
        if self.current_user['role'] not in ['Администратор', 'Менеджер']:
            return

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
                    to_char(r.creation_date, 'DD.MM.YYYY') as date
                FROM repair_requests r
                LEFT JOIN clients c ON r.client_id = c.client_id
                LEFT JOIN technicians t ON r.technician_id = t.technician_id
                LEFT JOIN device_types dt ON r.device_type_id = dt.type_id
                LEFT JOIN request_statuses s ON r.status_id = s.status_id
                WHERE 
                    c.last_name ILIKE %s OR
                    c.first_name ILIKE %s OR
                    c.phone ILIKE %s OR
                    dt.type_name ILIKE %s OR
                    r.device_model ILIKE %s OR
                    r.problem_description ILIKE %s
                ORDER BY r.creation_date DESC
            """
            like_pattern = f'%{search_text}%'
            params = [like_pattern] * 6
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

    def get_selected_id(self):
        """Получить ID выбранной заявки"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите заявку из списка")
            return None
        return self.tree.item(selection[0])['values'][0]

    def can_edit_request(self, request_id):
        """Проверка, может ли пользователь редактировать заявку"""
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

    def delete_request(self):
        """Удаление заявки"""
        if self.current_user['role'] not in ['Администратор', 'Менеджер']:
            messagebox.showerror("Ошибка", "У вас нет прав для удаления заявок")
            return

        request_id = self.get_selected_id()
        if not request_id:
            return

        result = messagebox.askyesno(
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить заявку №{request_id}?\n\nЭто действие нельзя отменить!",
            icon='warning'
        )

        if result:
            try:
                self.cursor.execute("DELETE FROM repair_requests WHERE request_id = %s", (request_id,))
                self.conn.commit()
                messagebox.showinfo("Успех", f"✅ Заявка №{request_id} успешно удалена")
                self.load_requests()
                self.status_label.configure(text=f"✅ Заявка {request_id} удалена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить заявку:\n{e}")

    def show_avg_time(self):
        """Показать среднее время ремонта (только для админа и менеджера)"""
        if self.current_user['role'] not in ['Администратор', 'Менеджер']:
            messagebox.showerror("Ошибка", "У вас нет прав для просмотра аналитики")
            return

        try:
            query = """
                SELECT 
                    t.last_name || ' ' || t.first_name as master,
                    COUNT(r.request_id) as requests_count,
                    COALESCE(ROUND(AVG(r.completion_date - r.creation_date::DATE), 1), 0) as avg_days
                FROM technicians t
                LEFT JOIN repair_requests r ON t.technician_id = r.technician_id 
                    AND r.status_id = (SELECT status_id FROM request_statuses WHERE status_name = 'Выполнена')
                GROUP BY t.technician_id, t.last_name, t.first_name
                HAVING COUNT(r.request_id) > 0
                ORDER BY avg_days DESC
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()

            if not results:
                messagebox.showinfo("Информация", "Нет данных о выполненных ремонтах")
                return

            msg = "📊 СРЕДНЕЕ ВРЕМЯ РЕМОНТА (дни):\n\n"
            for master, count, avg in results:
                msg += f"👨‍🔧 {master}:\n"
                msg += f"   • Выполнено заявок: {count}\n"
                msg += f"   • Среднее время: {avg} дней\n\n"

            messagebox.showinfo("Аналитика", msg)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить аналитику:\n{e}")

    def open_add_window(self):
        """Открыть окно добавления заявки"""
        AddRequestWindow(self.window, self)

    def open_edit_window(self):
        """Открыть окно редактирования заявки"""
        request_id = self.get_selected_id()
        if not request_id:
            return

        if not self.can_edit_request(request_id):
            messagebox.showerror(
                "Ошибка",
                "Вы не можете редактировать эту заявку"
            )
            return

        EditRequestWindow(self.window, self, request_id)

    def open_clients_window(self):
        """Открыть окно управления клиентами (только для админа)"""
        if self.current_user['role'] != 'Администратор':
            messagebox.showerror("Ошибка", "У вас нет прав для управления клиентами")
            return

        ClientsWindow(self.window, self)

    def __del__(self):
        """Закрытие соединения с БД"""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            print("🔌 Соединение с БД закрыто")


class AddRequestWindow(ctk.CTkToplevel):
    """Окно для добавления новой заявки"""

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
        """Создание элементов окна"""

        ctk.CTkLabel(
            self,
            text="ДОБАВЛЕНИЕ НОВОЙ ЗАЯВКИ",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        self.fields = {}

        if self.app.current_user['role'] == 'Клиент':
    
            ctk.CTkLabel(self, text="ФИО клиента").pack(pady=(10, 0))
            client_name = ctk.CTkEntry(self, width=350)
            client_name.insert(0, self.app.current_user['client_name'] or "")
            client_name.configure(state="disabled")
            client_name.pack(pady=5)

            ctk.CTkLabel(self, text="Телефон").pack()
            client_phone = ctk.CTkEntry(self, width=350)
            self.app.cursor.execute(
                "SELECT phone FROM clients WHERE client_id = %s",
                (self.app.current_user['client_id'],)
            )
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
        self.fields['model'] = ctk.CTkEntry(
            self, width=350, placeholder_text="Samsung WW90T"
        )
        self.fields['model'].pack(pady=5)

        ctk.CTkLabel(self, text="Описание проблемы").pack()
        self.fields['problem'] = ctk.CTkTextbox(self, width=350, height=100)
        self.fields['problem'].pack(pady=5)

        if self.app.current_user['role'] in ['Администратор', 'Менеджер']:
            ctk.CTkLabel(self, text="Статус").pack()
            self.load_statuses()
            self.fields['status'].pack(pady=5)

        ctk.CTkLabel(
            self, text="* - обязательные поля", text_color="gray", font=("Arial", 10)
        ).pack(pady=5)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame, text="💾 Сохранить", command=self.save_request, fg_color="green"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="✖ Отмена", command=self.destroy, fg_color="gray"
        ).pack(side="left", padx=5)

    def load_clients(self):
        """Загрузка списка клиентов для выбора"""
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
        """Загрузка типов устройств из БД"""
        try:
            self.app.cursor.execute("SELECT type_name FROM device_types ORDER BY type_name")
            device_types = [row[0] for row in self.app.cursor.fetchall()]
        except:
            device_types = ['Стиральная машина', 'Холодильник', 'Телевизор']

        self.fields['device_type'] = ctk.CTkComboBox(self, values=device_types, width=350)
        if device_types:
            self.fields['device_type'].set(device_types[0])

    def load_statuses(self):
        """Загрузка статусов из БД"""
        try:
            self.app.cursor.execute("SELECT status_name FROM request_statuses ORDER BY status_id")
            statuses = [row[0] for row in self.app.cursor.fetchall()]
        except:
            statuses = ['Новая']

        self.fields['status'] = ctk.CTkComboBox(self, values=statuses, width=350)
        if statuses:
            self.fields['status'].set(statuses[0])

    def save_request(self):
        """Сохранение новой заявки"""
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

            self.app.cursor.execute(
                "SELECT type_id FROM device_types WHERE type_name = %s",
                (self.fields['device_type'].get(),)
            )
            type_id = self.app.cursor.fetchone()[0]

            if self.app.current_user['role'] in ['Администратор', 'Менеджер'] and 'status' in self.fields:
                self.app.cursor.execute(
                    "SELECT status_id FROM request_statuses WHERE status_name = %s",
                    (self.fields['status'].get(),)
                )
                status_id = self.app.cursor.fetchone()[0]
            else:
         
                self.app.cursor.execute(
                    "SELECT status_id FROM request_statuses WHERE status_name = 'Новая'"
                )
                status_id = self.app.cursor.fetchone()[0]


            self.app.cursor.execute("""
                INSERT INTO repair_requests 
                (client_id, device_type_id, device_model, problem_description, status_id, creation_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                client_id, type_id,
                self.fields['model'].get().strip(),
                self.fields['problem'].get("1.0", "end-1c").strip() or None,
                status_id,
                datetime.now()
            ))

            self.app.conn.commit()
            messagebox.showinfo("Успех", "✅ Заявка успешно добавлена")
            self.app.load_requests()
            self.app.status_label.configure(text="✅ Новая заявка добавлена")
            self.destroy()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить заявку:\n{e}")

class EditRequestWindow(ctk.CTkToplevel):
    """Окно для редактирования заявки"""

    def __init__(self, parent, app, request_id):
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.request_id = request_id

        self.title(f"Редактирование заявки №{request_id}")
        self.geometry("450x550")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self.load_request_data()
        self.create_widgets()

    def load_request_data(self):
        """Загрузка данных заявки"""
        try:
            query = """
                SELECT 
                    r.client_id,
                    c.last_name || ' ' || c.first_name || COALESCE(' ' || c.middle_name, ''),
                    c.phone,
                    dt.type_name,
                    r.device_model,
                    r.problem_description,
                    s.status_name
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
        """Создание элементов окна"""
  
        ctk.CTkLabel(
            self,
            text=f"РЕДАКТИРОВАНИЕ ЗАЯВКИ №{self.request_id}",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

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

        ctk.CTkLabel(self, text="Статус").pack()
        self.load_statuses()
        self.fields['status'].set(self.request_data[6])
        self.fields['status'].pack(pady=5)

        ctk.CTkLabel(
            self, text="* - обязательные поля", text_color="gray", font=("Arial", 10)
        ).pack(pady=5)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame, text="💾 Сохранить", command=self.save_request, fg_color="green"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="✖ Отмена", command=self.destroy, fg_color="gray"
        ).pack(side="left", padx=5)

    def load_device_types(self):
        """Загрузка типов устройств"""
        try:
            self.app.cursor.execute("SELECT type_name FROM device_types ORDER BY type_name")
            device_types = [row[0] for row in self.app.cursor.fetchall()]
        except:
            device_types = ['Стиральная машина', 'Холодильник', 'Телевизор']

        self.fields['device_type'] = ctk.CTkComboBox(self, values=device_types, width=350)

    def load_statuses(self):
        """Загрузка статусов"""
        try:
            self.app.cursor.execute("SELECT status_name FROM request_statuses ORDER BY status_id")
            statuses = [row[0] for row in self.app.cursor.fetchall()]
        except:
            statuses = ['Новая']

        self.fields['status'] = ctk.CTkComboBox(self, values=statuses, width=350)

    def save_request(self):
        """Сохранение изменений"""
        try:
          
            if not self.fields['model'].get().strip():
                messagebox.showerror("Ошибка", "Введите модель устройства")
                return

            self.app.cursor.execute(
                "SELECT type_id FROM device_types WHERE type_name = %s",
                (self.fields['device_type'].get(),)
            )
            type_id = self.app.cursor.fetchone()[0]

            self.app.cursor.execute(
                "SELECT status_id FROM request_statuses WHERE status_name = %s",
                (self.fields['status'].get(),)
            )
            status_id = self.app.cursor.fetchone()[0]

            self.app.cursor.execute("""
                UPDATE repair_requests 
                SET device_type_id = %s,
                    device_model = %s,
                    problem_description = %s,
                    status_id = %s
                WHERE request_id = %s
            """, (
                type_id,
                self.fields['model'].get().strip(),
                self.fields['problem'].get("1.0", "end-1c").strip() or None,
                status_id,
                self.request_id
            ))

            if self.fields['status'].get() == 'Выполнена':
                self.app.cursor.execute("""
                    UPDATE repair_requests 
                    SET completion_date = %s
                    WHERE request_id = %s AND completion_date IS NULL
                """, (datetime.now().date(), self.request_id))

            self.app.conn.commit()
            messagebox.showinfo("Успех", "✅ Заявка успешно обновлена")
            self.app.load_requests()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить изменения:\n{e}")


class ClientsWindow(ctk.CTkToplevel):
    """Отдельная форма для работы с клиентами"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.parent = parent
        self.app = app

        self.title("Управление клиентами")
        self.geometry("900x500")

        self.create_widgets()
        self.load_clients()

    def create_widgets(self):
        """Создание интерфейса"""
    
        ctk.CTkLabel(
            self,
            text="КЛИЕНТЫ",
            font=("Arial", 18, "bold")
        ).pack(pady=10)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            btn_frame,
            text="➕ Добавить клиента",
            command=self.add_client,
            fg_color="green"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="✏️ Редактировать",
            command=self.edit_client,
            fg_color="blue"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="🗑️ Удалить",
            command=self.delete_client,
            fg_color="red"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="← Назад",
            command=self.destroy,
            fg_color="gray"
        ).pack(side="right", padx=5)

        search_frame = ctk.CTkFrame(btn_frame)
        search_frame.pack(side="right", padx=5)

        self.search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="Поиск клиентов...", width=200
        )
        self.search_entry.pack(side="left", padx=5)

        ctk.CTkButton(
            search_frame,
            text="🔍",
            command=self.search_clients,
            width=30
        ).pack(side="left")

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
        """Загрузка списка клиентов"""
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
        """Поиск клиентов"""
        search_text = self.search_entry.get().strip()
        self.load_clients(search_text if search_text else None)

    def get_selected_id(self):
        """Получить ID выбранного клиента"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите клиента из списка")
            return None
        return self.tree.item(selection[0])['values'][0]

    def add_client(self):
        """Добавление нового клиента (с созданием пользователя)"""
        self.edit_client_dialog()

    def edit_client(self):
        """Редактирование клиента"""
        client_id = self.get_selected_id()
        if client_id:
            self.edit_client_dialog(client_id)

    def edit_client_dialog(self, client_id=None):
        """Диалог добавления/редактирования клиента"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Редактирование клиента" if client_id else "Новый клиент")
        dialog.geometry("450x550")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="ДАННЫЕ КЛИЕНТА",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

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
        fields['phone'] = ctk.CTkEntry(
            dialog, width=350, placeholder_text="+7(999)123-45-67"
        )
        fields['phone'].pack(pady=5)

        ctk.CTkLabel(dialog, text="Email").pack()
        fields['email'] = ctk.CTkEntry(
            dialog, width=350, placeholder_text="email@example.com"
        )
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
              
                self.app.cursor.execute(
                    """SELECT last_name, first_name, middle_name, phone, email 
                       FROM clients WHERE client_id = %s""",
                    (client_id,)
                )
                client = self.app.cursor.fetchone()
                if client:
                    fields['last_name'].insert(0, client[0] or "")
                    fields['first_name'].insert(0, client[1] or "")
                    fields['middle_name'].insert(0, client[2] or "")
                    fields['phone'].insert(0, client[3] or "")
                    fields['email'].insert(0, client[4] or "")
                
                self.app.cursor.execute(
                    "SELECT username, password_hash FROM users WHERE client_id = %s",
                    (client_id,)
                )
                user = self.app.cursor.fetchone()
                if user:
                    fields['login'].insert(0, user[0] or "")
                   
                    fields['password'].insert(0, "********")
                    
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить данные:\n{e}")

        ctk.CTkLabel(
            dialog, text="* - обязательные поля", text_color="gray", font=("Arial", 10)
        ).pack(pady=5)

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
                    params = (
                        last_name, first_name,
                        fields['middle_name'].get().strip() or None,
                        phone, email or None,
                        client_id
                    )
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
                    params = (
                        last_name, first_name,
                        fields['middle_name'].get().strip() or None,
                        phone, email or None
                    )
                    self.app.cursor.execute(query, params)
                    client_id = self.app.cursor.fetchone()[0]

                    self.app.cursor.execute(
                        "SELECT role_id FROM roles WHERE role_name = 'Клиент'"
                    )
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

        ctk.CTkButton(
            btn_frame, text="💾 Сохранить", command=save, fg_color="green"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="✖ Отмена", command=dialog.destroy, fg_color="gray"
        ).pack(side="left", padx=5)

    def delete_client(self):
        """Удаление клиента"""
        client_id = self.get_selected_id()
        if not client_id:
            return

        try:
           
            self.app.cursor.execute(
                "SELECT COUNT(*) FROM repair_requests WHERE client_id = %s",
                (client_id,)
            )
            count = self.app.cursor.fetchone()[0]

            if count > 0:
                result = messagebox.askyesno(
                    "Подтверждение",
                    f"У клиента есть {count} заявок. При удалении клиента все его заявки также будут удалены.\n\nПродолжить?",
                    icon='warning'
                )
            else:
                result = messagebox.askyesno(
                    "Подтверждение",
                    "Удалить клиента?",
                    icon='question'
                )

            if result:
                self.app.cursor.execute(
                    "DELETE FROM clients WHERE client_id = %s",
                    (client_id,),
                )
                self.app.conn.commit()
                messagebox.showinfo("Успех", "Клиент удален")
                self.load_clients()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить клиента:\n{e}")

if __name__ == "__main__":
    app = RepairServiceApp()