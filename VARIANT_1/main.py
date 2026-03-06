import customtkinter as ctk
from tkinter import messagebox, ttk
import psycopg2
from datetime import datetime

# Настройки подключения к БД (ИЗМЕНИТЕ ПОД СВОИ)
DB_CONFIG = {
    'dbname': 'repair_service',
    'user': 'postgres',
    'password': '123qwe',  # Смените на свой пароль
    'host': 'localhost',
    'port': '5432'
}

class RepairServiceApp:
    def __init__(self):
        # Настройка главного окна
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")
        
        self.window = ctk.CTk()
        self.window.title("Учет заявок на ремонт бытовой техники v1.0")
        self.window.geometry("1300x650")
        
        # Подключение к БД
        self.connect_to_db()
        
        # Создание интерфейса
        self.create_widgets()
        
        # Загрузка данных
        self.load_requests()
        
        # Запуск приложения
        self.window.mainloop()
    
    def connect_to_db(self):
        """Подключение к PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            print("✅ Подключено к БД")
        except Exception as e:
            messagebox.showerror("Ошибка подключения", 
                                f"Не удалось подключиться к БД:\n{e}\n\n"
                                f"Проверьте:\n"
                                f"1. Запущен ли PostgreSQL\n"
                                f"2. Создана ли БД 'repair_service'\n"
                                f"3. Правильный ли пароль в DB_CONFIG")
            exit(1)
    
    def create_widgets(self):
        """Создание интерфейса"""
        # Заголовок
        title_label = ctk.CTkLabel(
            self.window, 
            text="СИСТЕМА УЧЕТА ЗАЯВОК НА РЕМОНТ",
            font=("Arial", 20, "bold")
        )
        title_label.pack(pady=10)
        
        # Верхняя панель с кнопками
        top_frame = ctk.CTkFrame(self.window)
        top_frame.pack(pady=10, padx=10, fill="x")
        
        # Кнопки
        buttons = [
            ("➕ Добавить заявку", self.open_add_window, "green"),
            ("✏️ Редактировать", self.edit_request, "blue"),
            ("🗑️ Удалить", self.delete_request, "red"),
            ("🔄 Обновить", self.load_requests, "gray"),
            ("📊 Среднее время", self.show_avg_time, "purple")
        ]
        
        for text, command, color in buttons:
            btn = ctk.CTkButton(
                top_frame, 
                text=text, 
                command=command,
                fg_color=color,
                hover_color=color,
                width=120
            )
            btn.pack(side="left", padx=5)
        
        # Панель поиска
        search_frame = ctk.CTkFrame(top_frame)
        search_frame.pack(side="right", padx=5)
        
        self.search_entry = ctk.CTkEntry(
            search_frame, 
            placeholder_text="Поиск по клиенту, телефону, модели...",
            width=250
        )
        self.search_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(
            search_frame, 
            text="🔍 Найти",
            command=self.search_requests,
            width=80
        ).pack(side="left")
        
        # Таблица для отображения заявок
        columns = ('ID', 'Клиент', 'Телефон', 'Тип', 'Модель', 'Проблема', 'Статус', 'Мастер', 'Дата')
        self.tree = ttk.Treeview(self.window, columns=columns, show='headings', height=20)
        
        # Настройка колонок
        widths = [50, 150, 120, 100, 120, 200, 100, 120, 100]
        for col, width in zip(columns, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width)
        
        # Скроллбары
        v_scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(self.window, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Размещение таблицы и скроллбаров
        self.tree.pack(side="left", fill="both", expand=True, padx=(10,0), pady=10)
        v_scrollbar.pack(side="right", fill="y", padx=(0,10), pady=10)
        h_scrollbar.pack(side="bottom", fill="x", padx=10)
        
        # Статус бар
        status_frame = ctk.CTkFrame(self.window, height=30)
        status_frame.pack(side="bottom", fill="x")
        
        self.status_label = ctk.CTkLabel(status_frame, text="Готов к работе", anchor="w")
        self.status_label.pack(side="left", padx=10, pady=5)
        
        self.count_label = ctk.CTkLabel(status_frame, text="", anchor="e")
        self.count_label.pack(side="right", padx=10, pady=5)
    
    def load_requests(self):
        """Загрузка списка заявок"""
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
                ORDER BY r.creation_date DESC
            """
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            
            # Очищаем таблицу
            for row in self.tree.get_children():
                self.tree.delete(row)
            
            # Заполняем данными
            for row in rows:
                self.tree.insert('', 'end', values=row)
            
            # Обновляем статус
            self.status_label.configure(text="✅ Данные загружены")
            self.count_label.configure(text=f"Всего заявок: {len(rows)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные:\n{e}")
            self.status_label.configure(text="❌ Ошибка загрузки")
    
    def search_requests(self):
        """Поиск заявок"""
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
            
            # Очищаем таблицу
            for row in self.tree.get_children():
                self.tree.delete(row)
            
            # Заполняем результатами поиска
            for row in rows:
                self.tree.insert('', 'end', values=row)
            
            # Обновляем статус
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
    
    def delete_request(self):
        """Удаление заявки"""
        request_id = self.get_selected_id()
        if not request_id:
            return
        
        # Запрос подтверждения
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
        """Показать среднее время ремонта (Модуль 1 - расчетная функция)"""
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
            
            # Формируем сообщение
            msg = "📊 СРЕДНЕЕ ВРЕМЯ РЕМОНТА (дни):\n\n"
            for master, count, avg in results:
                msg += f"👨‍🔧 {master}:\n"
                msg += f"   • Выполнено заявок: {count}\n"
                msg += f"   • Среднее время: {avg} дней\n\n"
            
            messagebox.showinfo("Аналитика", msg)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить аналитику:\n{e}")
    
    def open_add_window(self):
        """Окно добавления заявки"""
        add_window = ctk.CTkToplevel(self.window)
        add_window.title("Новая заявка на ремонт")
        add_window.geometry("450x600")
        add_window.resizable(False, False)
        
        # Делаем окно модальным
        add_window.transient(self.window)
        add_window.grab_set()
        
        # Заголовок
        ctk.CTkLabel(
            add_window, 
            text="ДОБАВЛЕНИЕ НОВОЙ ЗАЯВКИ",
            font=("Arial", 16, "bold")
        ).pack(pady=10)
        
        # Поля ввода
        fields = {}
        
        # Клиент
        ctk.CTkLabel(add_window, text="ФИО клиента *").pack(pady=(10,0))
        fields['client_name'] = ctk.CTkEntry(add_window, width=350, placeholder_text="Иванов Иван Иванович")
        fields['client_name'].pack(pady=5)
        
        ctk.CTkLabel(add_window, text="Телефон *").pack()
        fields['phone'] = ctk.CTkEntry(add_window, width=350, placeholder_text="+7(999)123-45-67")
        fields['phone'].pack(pady=5)
        
        ctk.CTkLabel(add_window, text="Email").pack()
        fields['email'] = ctk.CTkEntry(add_window, width=350, placeholder_text="ivan@mail.ru")
        fields['email'].pack(pady=5)
        
        # Получаем типы устройств из БД
        try:
            self.cursor.execute("SELECT type_name FROM device_types ORDER BY type_name")
            device_types = [row[0] for row in self.cursor.fetchall()]
        except:
            device_types = ['Стиральная машина', 'Холодильник', 'Телевизор']
        
        ctk.CTkLabel(add_window, text="Тип устройства *").pack()
        fields['device_type'] = ctk.CTkComboBox(add_window, values=device_types, width=350)
        fields['device_type'].pack(pady=5)
        if device_types:
            fields['device_type'].set(device_types[0])
        
        ctk.CTkLabel(add_window, text="Модель *").pack()
        fields['model'] = ctk.CTkEntry(add_window, width=350, placeholder_text="Samsung WW90T")
        fields['model'].pack(pady=5)
        
        ctk.CTkLabel(add_window, text="Описание проблемы").pack()
        fields['problem'] = ctk.CTkTextbox(add_window, width=350, height=100)
        fields['problem'].pack(pady=5)
        
        # Статусы
        try:
            self.cursor.execute("SELECT status_name FROM request_statuses ORDER BY status_id")
            statuses = [row[0] for row in self.cursor.fetchall()]
        except:
            statuses = ['Новая']
        
        ctk.CTkLabel(add_window, text="Статус").pack()
        fields['status'] = ctk.CTkComboBox(add_window, values=statuses, width=350)
        fields['status'].pack(pady=5)
        if statuses:
            fields['status'].set(statuses[0])
        
        # Подсказка
        ctk.CTkLabel(add_window, text="* - обязательные поля", text_color="gray", font=("Arial", 10)).pack(pady=5)
        
        def save_request():
            """Сохранение новой заявки"""
            # Валидация
            if not fields['client_name'].get().strip():
                messagebox.showerror("Ошибка", "Введите ФИО клиента")
                return
            if not fields['phone'].get().strip():
                messagebox.showerror("Ошибка", "Введите телефон")
                return
            if not fields['model'].get().strip():
                messagebox.showerror("Ошибка", "Введите модель устройства")
                return
            
            try:
                # Разбираем ФИО
                name_parts = fields['client_name'].get().strip().split()
                last_name = name_parts[0] if len(name_parts) > 0 else ""
                first_name = name_parts[1] if len(name_parts) > 1 else ""
                middle_name = name_parts[2] if len(name_parts) > 2 else ""
                
                # Проверяем, есть ли клиент
                self.cursor.execute(
                    "SELECT client_id FROM clients WHERE phone = %s", 
                    (fields['phone'].get().strip(),)
                )
                client = self.cursor.fetchone()
                
                if client:
                    client_id = client[0]
                else:
                    # Добавляем нового клиента
                    self.cursor.execute("""
                        INSERT INTO clients (last_name, first_name, middle_name, phone, email)
                        VALUES (%s, %s, %s, %s, %s) RETURNING client_id
                    """, (
                        last_name, first_name, middle_name,
                        fields['phone'].get().strip(),
                        fields['email'].get().strip() or None
                    ))
                    client_id = self.cursor.fetchone()[0]
                
                # Получаем type_id
                self.cursor.execute(
                    "SELECT type_id FROM device_types WHERE type_name = %s",
                    (fields['device_type'].get(),)
                )
                type_id = self.cursor.fetchone()[0]
                
                # Получаем status_id
                self.cursor.execute(
                    "SELECT status_id FROM request_statuses WHERE status_name = %s",
                    (fields['status'].get(),)
                )
                status_id = self.cursor.fetchone()[0]
                
                # Добавляем заявку
                self.cursor.execute("""
                    INSERT INTO repair_requests 
                    (client_id, device_type_id, device_model, problem_description, status_id, creation_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    client_id, type_id,
                    fields['model'].get().strip(),
                    fields['problem'].get("1.0", "end-1c").strip() or None,
                    status_id,
                    datetime.now()
                ))
                
                self.conn.commit()
                messagebox.showinfo("Успех", "✅ Заявка успешно добавлена")
                add_window.destroy()
                self.load_requests()
                self.status_label.configure(text="✅ Новая заявка добавлена")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить заявку:\n{e}")
        
        # Кнопки
        btn_frame = ctk.CTkFrame(add_window)
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="💾 Сохранить", command=save_request, fg_color="green").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="✖ Отмена", command=add_window.destroy, fg_color="gray").pack(side="left", padx=5)
    
    def edit_request(self):
        """Редактирование заявки"""
        request_id = self.get_selected_id()
        if not request_id:
            return
        
        # Получаем данные заявки
        try:
            self.cursor.execute("""
                SELECT 
                    r.request_id, r.client_id, r.device_type_id, r.device_model,
                    r.problem_description, r.status_id,
                    c.last_name, c.first_name, c.middle_name, c.phone, c.email,
                    dt.type_name
                FROM repair_requests r
                JOIN clients c ON r.client_id = c.client_id
                JOIN device_types dt ON r.device_type_id = dt.type_id
                WHERE r.request_id = %s
            """, (request_id,))
            request = self.cursor.fetchone()
            
            if not request:
                messagebox.showerror("Ошибка", "Заявка не найдена")
                return
            
            # Создаем окно редактирования (аналогично добавлению, но с заполненными полями)
            # Для краткости - показываем сообщение, что функция в разработке
            messagebox.showinfo("Информация", "Редактирование будет доступно в следующей версии")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные заявки:\n{e}")
    
    def __del__(self):
        """Закрытие соединения с БД"""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            print("🔌 Соединение с БД закрыто")

if __name__ == "__main__":
    app = RepairServiceApp()