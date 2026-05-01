import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime

# ===== КОНФИГУРАЦИЯ =====
GITHUB_API_URL = "https://api.github.com/users/"
FAVORITES_FILE = "favorites.json"

# ===== ОСНОВНОЕ ПРИЛОЖЕНИЕ =====
class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("750x600")
        self.root.resizable(False, False)

        self.favorites = self.load_favorites()

        self.create_widgets()
        self.update_favorites_display()

    # ===== РАБОТА С JSON =====
    def load_favorites(self):
        if os.path.exists(FAVORITES_FILE):
            try:
                with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def save_favorites(self):
        try:
            with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить избранное: {e}")

    # ===== ИНТЕРФЕЙС =====
    def create_widgets(self):
        # Рамка поиска
        search_frame = ttk.LabelFrame(self.root, text="Поиск пользователя GitHub", padding=10)
        search_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(search_frame, text="Имя пользователя:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.username_entry = ttk.Entry(search_frame, width=30)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        self.username_entry.bind("<Return>", lambda e: self.search_user())

        self.search_btn = ttk.Button(search_frame, text="🔍 Поиск", command=self.search_user)
        self.search_btn.grid(row=0, column=2, padx=5, pady=5)

        # Рамка результатов поиска
        result_frame = ttk.LabelFrame(self.root, text="Результат поиска", padding=10)
        result_frame.pack(fill="x", padx=10, pady=5)

        self.user_info_label = ttk.Label(result_frame, text="", justify="left", font=("Arial", 10))
        self.user_info_label.pack(fill="x", padx=5, pady=5)

        self.add_fav_btn = ttk.Button(result_frame, text="⭐ Добавить в избранное", command=self.add_to_favorites, state="disabled")
        self.add_fav_btn.pack(pady=5)

        # Рамка избранного
        fav_frame = ttk.LabelFrame(self.root, text="⭐ Избранные пользователи", padding=10)
        fav_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Таблица избранных
        columns = ("№", "Логин", "ID", "Дата добавления")
        self.fav_tree = ttk.Treeview(fav_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.fav_tree.heading(col, text=col)
            self.fav_tree.column(col, width=150)

        scrollbar = ttk.Scrollbar(fav_frame, orient="vertical", command=self.fav_tree.yview)
        self.fav_tree.configure(yscrollcommand=scrollbar.set)
        self.fav_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Привязка клика для просмотра профиля
        self.fav_tree.bind("<Double-1>", self.show_user_profile)

        # Кнопка удаления из избранного
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)

        self.remove_btn = ttk.Button(btn_frame, text="❌ Удалить из избранного", command=self.remove_from_favorites)
        self.remove_btn.pack(side="left", padx=5)

        self.clear_btn = ttk.Button(btn_frame, text="🗑 Очистить избранное", command=self.clear_favorites)
        self.clear_btn.pack(side="left", padx=5)

        # Текущий найденный пользователь
        self.current_user = None

    # ===== ПОИСК ПОЛЬЗОВАТЕЛЯ =====
    def search_user(self):
        username = self.username_entry.get().strip()

        # Валидация
        if not username:
            messagebox.showwarning("Ошибка ввода", "Введите имя пользователя GitHub!")
            return

        try:
            response = requests.get(GITHUB_API_URL + username, timeout=5)

            if response.status_code == 200:
                user_data = response.json()
                self.display_user_info(user_data)
                self.current_user = user_data
                self.add_fav_btn.config(state="normal")
            elif response.status_code == 404:
                messagebox.showerror("Не найдено", f"Пользователь '{username}' не найден на GitHub")
                self.user_info_label.config(text="❌ Пользователь не найден")
                self.current_user = None
                self.add_fav_btn.config(state="disabled")
            else:
                messagebox.showerror("Ошибка", f"Ошибка API: {response.status_code}")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Ошибка сети", "Проверьте интернет-соединение")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")

    # ===== ОТОБРАЖЕНИЕ ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЕ =====
    def display_user_info(self, user):
        info_text = f"""
📌 Логин: {user.get('login', 'N/A')}
👤 Имя: {user.get('name', 'Не указано')}
🏢 Компания: {user.get('company', 'Не указана')}
📍 Локация: {user.get('location', 'Не указана')}
📁 Репозитории: {user.get('public_repos', 0)}
👥 Подписчики: {user.get('followers', 0)}
📋 Профиль: {user.get('html_url', 'N/A')}
        """
        self.user_info_label.config(text=info_text)

    # ===== ИЗБРАННОЕ =====
    def add_to_favorites(self):
        if self.current_user is None:
            return

        # Проверяем, есть ли уже в избранном
        for fav in self.favorites:
            if fav["login"] == self.current_user["login"]:
                messagebox.showwarning("Предупреждение", f"@{self.current_user['login']} уже в избранном!")
                return

        favorite = {
            "login": self.current_user["login"],
            "user_id": self.current_user["id"],
            "avatar_url": self.current_user["avatar_url"],
            "html_url": self.current_user["html_url"],
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "name": self.current_user.get("name", ""),
            "public_repos": self.current_user.get("public_repos", 0),
            "followers": self.current_user.get("followers", 0)
        }
        self.favorites.append(favorite)
        self.save_favorites()
        self.update_favorites_display()
        messagebox.showinfo("Успех", f"@{self.current_user['login']} добавлен в избранное!")

    def update_favorites_display(self):
        # Очищаем таблицу
        for row in self.fav_tree.get_children():
            self.fav_tree.delete(row)

        # Заполняем таблицу
        for idx, fav in enumerate(self.favorites, 1):
            self.fav_tree.insert("", "end", values=(
                idx,
                fav["login"],
                fav["user_id"],
                fav["added_at"]
            ))

    def remove_from_favorites(self):
        selected = self.fav_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите пользователя для удаления")
            return

        # Получаем логин пользователя
        item = self.fav_tree.item(selected[0])
        login = item["values"][1]

        # Удаляем
        self.favorites = [fav for fav in self.favorites if fav["login"] != login]
        self.save_favorites()
        self.update_favorites_display()
        messagebox.showinfo("Успех", f"@{login} удалён из избранного")

    def clear_favorites(self):
        if not self.favorites:
            messagebox.showinfo("Инфо", "Избранное уже пусто")
            return

        if messagebox.askyesno("Подтверждение", "Очистить весь список избранных?"):
            self.favorites.clear()
            self.save_favorites()
            self.update_favorites_display()
            messagebox.showinfo("Успех", "Избранное очищено")

    def show_user_profile(self, event):
        """Двойной клик по избранному — открываем профиль в браузере"""
        selected = self.fav_tree.selection()
        if not selected:
            return

        item = self.fav_tree.item(selected[0])
        login = item["values"][1]

        # Ищем полную информацию в избранном
        for fav in self.favorites:
            if fav["login"] == login:
                import webbrowser
                webbrowser.open(fav["html_url"])
                break

# ===== ЗАПУСК =====
if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()
