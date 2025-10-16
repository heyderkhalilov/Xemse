import tkinter as tk
from tkinter import simpledialog, PhotoImage, ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
import math
import os

class CompetitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Competition Manager")

        # Fullscreen
        self.root.state("zoomed")

        self.conn = sqlite3.connect("competition.db")
        self.create_tables()

        self.current_competition_id = None
        self.teams = {}
        self.team_colors = ["#3498db", "#2ecc71", "#e67e22", "#e74c3c",
                            "#9b59b6", "#1abc9c", "#f39c12", "#2c3e50"]

        self.bg_image_path = "background.png"
        self.bg_label = None

        self.main_menu()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                date_created TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competition_id INTEGER,
                name TEXT,
                score INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_number INTEGER,
                competition_id INTEGER,
                question_text TEXT,
                answer TEXT,
                points INTEGER,
                image_path TEXT
            )
        """)
        self.conn.commit()

    def set_background(self):
        if os.path.exists(self.bg_image_path):
            bg = PhotoImage(file=self.bg_image_path)
            self.bg_label = tk.Label(self.root, image=bg)
            self.bg_label.image = bg
            self.bg_label.place(relwidth=1, relheight=1)
        else:
            self.root.configure(bg="#74b9ff")

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.set_background()

    def create_navbar(self, back_command=None, title=""):
        header = tk.Frame(self.root, bg="#0984e3", height=60)
        header.pack(fill="x")

        if back_command:
            back_btn = tk.Button(header, text="⬅ Geri", font=("Arial", 14, "bold"),
                                 bg="#d63031", fg="white", relief="flat", padx=20,
                                 command=back_command)
            back_btn.pack(side="left", padx=20, pady=10)

        tk.Label(header, text=title, font=("Arial", 22, "bold"),
                 bg="#0984e3", fg="white").pack(pady=10)

    def modern_button(self, parent, text, color, command, icon=None, width=25):
        return tk.Button(
            parent,
            text=(icon + " " + text) if icon else text,
            font=("Arial", 18, "bold"),
            bg=color, fg="white",
            relief="flat", width=width, height=2,
            cursor="hand2", command=command
        )

    def main_menu(self):
        self.clear_window()
        self.create_navbar(title="🏆 Yarış Meneceri")

        frame = tk.Frame(self.root, bg="#74b9ff")
        frame.pack(expand=True)

        self.modern_button(frame, "Yeni yarış yarat", "#00b894",
                           self.create_competition, "➕").pack(pady=20)
        self.modern_button(frame, "Köhnə yarışlara bax", "#0984e3",
                           self.view_competitions, "📂").pack(pady=20)
        self.modern_button(frame, "Çıxış", "#d63031",
                           self.root.quit, "❌").pack(pady=20)

    def create_competition(self):
        name = simpledialog.askstring("Yarış", "Yarışın adını daxil edin:")
        if name:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO competitions (name, date_created) VALUES (?, ?)",
                           (name, datetime.now()))
            self.conn.commit()
            self.current_competition_id = cursor.lastrowid
            self.add_teams()

    def add_teams(self):
        self.clear_window()
        self.create_navbar(self.main_menu, "Komandaları əlavə et")

        frame = tk.Frame(self.root, bg="#74b9ff")
        frame.pack(expand=True)

        self.team_entries = []
        for i in range(4):
            entry = tk.Entry(frame, font=("Arial", 18), width=25, justify="center", bd=3, relief="ridge")
            entry.insert(0, f"Komanda {i+1}")
            entry.pack(pady=10)
            self.team_entries.append(entry)

        self.modern_button(frame, "🚀 Yarışı Başlat", "#6c5ce7",
                           self.start_competition).pack(pady=40)

    def start_competition(self):
        cursor = self.conn.cursor()
        for entry in self.team_entries:
            team_name = entry.get().strip()
            if team_name:
                cursor.execute("INSERT INTO teams (competition_id, name, score) VALUES (?, ?, ?)",
                               (self.current_competition_id, team_name, 0))
        self.conn.commit()
        self.load_scoreboard()

    def load_scoreboard(self):
        self.clear_window()
        self.create_navbar(self.main_menu, "Canlı xal lövhəsi")

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, score FROM teams WHERE competition_id=?",
                       (self.current_competition_id,))
        teams = cursor.fetchall()

        self.teams = {tid: {"name": n, "score": s} for tid, n, s in teams}
        self.render_leaderboard()

    def render_leaderboard(self):
        if hasattr(self, "board") and self.board.winfo_exists():
            self.board.destroy()

        sorted_teams = list(self.teams.items())
        self.board = tk.Frame(self.root, bg="#74b9ff")
        self.board.pack(expand=True, fill="both")

        self.labels = {}
        n = len(sorted_teams)
        cols = 2
        rows = math.ceil(n / cols)

        xal_values = [100 * i for i in range(0, 11)]
        xal_frame = tk.Frame(self.board, bg="#0984e3")
        xal_frame.grid(row=0, column=0, columnspan=cols, sticky="ew", padx=10, pady=(12, 8))

        tk.Label(xal_frame, text="Xal:", font=("Arial", 18, "bold"),
                 bg="#0984e3", fg="white").grid(row=0, column=0, padx=(10, 8), pady=8, sticky="w")

        self.xal_var = tk.IntVar(value=0)
        style = ttk.Style()
        style.configure("Large.TCombobox", font=("Arial", 16), padding=6)

        xal_combo = ttk.Combobox(xal_frame, textvariable=self.xal_var,
                                 values=xal_values, width=6, style="Large.TCombobox",
                                 state="readonly")
        xal_combo.grid(row=0, column=1, padx=(0, 10), pady=8, ipady=6, sticky="w")
        xal_combo.set(0)

        start_row = 1
        for i, (team_id, team) in enumerate(sorted_teams):
            r, c = divmod(i, cols)
            color = self.team_colors[i % len(self.team_colors)]
            frame = tk.Frame(self.board, bg=color, padx=30, pady=15, relief="flat", bd=10)
            frame.grid(row=r + start_row, column=c, padx=60, pady=30, sticky="nsew")

            tk.Label(frame, text=team["name"], font=("Arial", 22, "bold"), bg=color, fg="white").grid(row=0, column=0, columnspan=3, pady=10)
            lbl = tk.Label(frame, text=str(team["score"]), font=("Arial", 32, "bold"), bg=color, fg="white")
            lbl.grid(row=1, column=1, pady=10)
            self.labels[team_id] = lbl

            tk.Button(frame, text="+", font=("Arial", 22, "bold"), bg="#2ecc71", fg="white", relief="flat", width=3,
                      command=lambda t=team_id: self.update_score(t, self.xal_var.get())).grid(row=1, column=2, padx=20)
            tk.Button(frame, text="-", font=("Arial", 22, "bold"), bg="#e74c3c", fg="white", relief="flat", width=3,
                      command=lambda t=team_id: self.update_score(t, -100)).grid(row=1, column=0, padx=20)

        self.board.grid_rowconfigure(0, weight=0, minsize=80)
        for r in range(start_row, rows + start_row):
            self.board.grid_rowconfigure(r, weight=1)
        for c in range(cols):
            self.board.grid_columnconfigure(c, weight=1)

    def update_score(self, team_id, points):
        if points == 0:
            return
        self.teams[team_id]["score"] += points
        cursor = self.conn.cursor()
        cursor.execute("UPDATE teams SET score=? WHERE id=?", (self.teams[team_id]["score"], team_id))
        self.conn.commit()
        self.render_leaderboard()

    def view_competitions(self):
        self.clear_window()
        self.create_navbar(self.main_menu, "Köhnə yarışlar")

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, date_created FROM competitions")
        competitions = cursor.fetchall()

        frame = tk.Frame(self.root, bg="#74b9ff")
        frame.pack(expand=True)

        for comp_id, name, date in competitions:
            item_frame = tk.Frame(frame, bg="#74b9ff")
            item_frame.pack(pady=10)

            btn = self.modern_button(item_frame, f"{name}", "#0984e3",
                                     lambda cid=comp_id: self.load_old_competition(cid), width=20)
            btn.pack(side="left", padx=10)

            del_btn = self.modern_button(item_frame, "Sil", "#d63031",
                                         lambda cid=comp_id: self.delete_competition(cid), width=6)
            del_btn.pack(side="left", padx=10)

            q_btn = self.modern_button(item_frame, "Suallar", "#6c5ce7",
                                       lambda cid=comp_id: self.manage_questions(cid), width=10)
            q_btn.pack(side="left", padx=10)

    def manage_questions(self, comp_id):
        win = tk.Toplevel(self.root)
        win.title("Suallar")
        win.geometry("800x500")
        win.configure(bg="#74b9ff")

        tk.Label(win, text="Suallar", font=("Arial", 20, "bold"), bg="#0984e3", fg="white").pack(fill="x")

        container = ttk.Frame(win)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        canvas = tk.Canvas(container, bg="#74b9ff")
        scrollbar_x = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)
        scrollbar_y = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(xscrollcommand=scrollbar_x.set, yscrollcommand=scrollbar_y.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_x.pack(side="bottom", fill="x")
        scrollbar_y.pack(side="right", fill="y")

        self.render_question_table(scrollable_frame, comp_id)

        tk.Button(win, text="Sual Əlavə Et", bg="#00b894", fg="white",
                  font=("Arial", 16, "bold"), command=lambda: self.add_question(win, comp_id)).pack(pady=10)

    def render_question_table(self, parent, comp_id):
        for widget in parent.winfo_children():
            widget.destroy()

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, question_text, image_path FROM questions WHERE competition_id=?", (comp_id,))
        questions = cursor.fetchall()

        headers = ["ID", "Sual", "Şəkil", "Redaktə", "Sil"]
        for col, h in enumerate(headers):
            tk.Label(parent, text=h, font=("Arial", 14, "bold"), bg="#0984e3", fg="white", padx=10, pady=5)\
                .grid(row=0, column=col, sticky="nsew")

        for i, (qid, text, img) in enumerate(questions, start=1):
            tk.Label(parent, text=str(qid), bg="#74b9ff", font=("Arial", 12)).grid(row=i, column=0, padx=5, pady=5)
            tk.Label(parent, text=text[:50], bg="#74b9ff", font=("Arial", 12)).grid(row=i, column=1, padx=5, pady=5)
            tk.Label(parent, text=os.path.basename(img) if img else "-", bg="#74b9ff", font=("Arial", 12)).grid(row=i, column=2, padx=5, pady=5)

            tk.Button(parent, text="✏", bg="#6c5ce7", fg="white", width=5,
                      command=lambda qid=qid: self.edit_question(parent, comp_id, qid)).grid(row=i, column=3, padx=5)
            tk.Button(parent, text="🗑", bg="#e74c3c", fg="white", width=5,
                      command=lambda qid=qid: self.delete_question(parent, comp_id, qid)).grid(row=i, column=4, padx=5)




    def add_question(self, parent, comp_id):
        win = tk.Toplevel(self.root)
        win.title("Yeni Sual Əlavə Et")
        win.geometry("520x480")
        win.configure(bg="#f7f9fc")
        win.grab_set()

        # --- Title ---
        title = tk.Label(win, text="Yeni Sual Əlavə Et", font=("Arial", 16, "bold"), bg="#f7f9fc")
        title.pack(pady=10)

        # --- Form Frame ---
        form_frame = tk.Frame(win, bg="#f7f9fc")
        form_frame.pack(padx=20, pady=10, fill="both", expand=True)

        # --- Question Number ---
        tk.Label(form_frame, text="Sual nömrəsi:", bg="#f7f9fc", anchor="w", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        q_num_entry = ttk.Entry(form_frame, width=10)
        q_num_entry.grid(row=0, column=1, sticky="w", pady=5)

        # --- Question Text ---
        tk.Label(form_frame, text="Sual mətni:", bg="#f7f9fc", anchor="w", font=("Arial", 11, "bold")).grid(row=1, column=0, sticky="nw", pady=(10, 0))
        q_entry = tk.Text(form_frame, height=4, width=50, wrap="word", relief="solid", borderwidth=1)
        q_entry.grid(row=2, column=0, columnspan=2, pady=5, sticky="we")

        # --- Answer ---
        tk.Label(form_frame, text="Cavab:", bg="#f7f9fc", anchor="w", font=("Arial", 11, "bold")).grid(row=3, column=0, sticky="w", pady=(10, 0))
        answer_entry = ttk.Entry(form_frame, width=50)
        answer_entry.grid(row=4, column=0, columnspan=2, pady=5, sticky="we")

        # --- Points ---
        tk.Label(form_frame, text="Xal:", bg="#f7f9fc", anchor="w", font=("Arial", 11, "bold")).grid(row=5, column=0, sticky="w", pady=(10, 0))
        points_entry = ttk.Spinbox(form_frame, from_=1, to=100, width=10)
        points_entry.set(1)
        points_entry.grid(row=5, column=1, sticky="w", pady=5)

        # --- Image ---
        tk.Label(form_frame, text="Şəkil:", bg="#f7f9fc", anchor="w", font=("Arial", 11, "bold")).grid(row=6, column=0, sticky="w", pady=(10, 0))
        img_path_var = tk.StringVar()
        img_label = tk.Label(form_frame, textvariable=img_path_var, bg="#f7f9fc", fg="#444", wraplength=250, anchor="w", justify="left")
        img_label.grid(row=7, column=0, columnspan=2, sticky="w")

        def choose_image():
            path = filedialog.askopenfilename(
                title="Şəkil seçin",
                filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")]
            )
            if path:
                img_path_var.set(path)

        choose_btn = ttk.Button(form_frame, text="Şəkil Seç", command=choose_image)
        choose_btn.grid(row=6, column=1, sticky="e", pady=5)

        # --- Save button ---
        def save_question():
            q_num = q_num_entry.get().strip()
            q_text = q_entry.get("1.0", "end").strip()
            if not q_text:
                messagebox.showerror("Xəta", "Sual mətni boş ola bilməz!")
                return

            answer = answer_entry.get().strip()
            try:
                points = int(points_entry.get())
            except ValueError:
                points = 1
            img_path = img_path_var.get() or None

            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO questions (id, competition_id, question_text, answer, points, image_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (q_num if q_num else None, comp_id, q_text, answer, points, img_path))
            self.conn.commit()

            messagebox.showinfo("Uğurlu əməliyyat", "Yeni sual əlavə olundu ✅")
            win.destroy()
            self.render_question_table(parent, comp_id)

        # --- Button Row ---
        btn_frame = tk.Frame(win, bg="#f7f9fc")
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="Yadda saxla", command=save_question).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Bağla", command=win.destroy).pack(side="left", padx=10)



    def edit_question(self, parent, comp_id, qid):
        cursor = self.conn.cursor()
        cursor.execute("SELECT question_text, image_path FROM questions WHERE id=?", (qid,))
        q_text, img_path = cursor.fetchone()

        new_text = simpledialog.askstring("Redaktə", "Yeni sual mətni:", initialvalue=q_text)
        if not new_text:
            return

        new_img = filedialog.askopenfilename(title="Yeni şəkil seçin (istəyə görə)",
                                             filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if not new_img:
            new_img = img_path

        cursor.execute("UPDATE questions SET question_text=?, image_path=? WHERE id=?",
                       (new_text, new_img, qid))
        self.conn.commit()
        self.render_question_table(parent, comp_id)

    def delete_question(self, parent, comp_id, qid):
        if not messagebox.askyesno("Təsdiq", "Bu sualı silmək istədiyinizə əminsiniz?"):
            return
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM questions WHERE id=?", (qid,))
        self.conn.commit()
        self.render_question_table(parent, comp_id)

    def load_old_competition(self, comp_id):
        self.current_competition_id = comp_id
        self.load_scoreboard()

    def delete_competition(self, comp_id):
        if not messagebox.askyesno("Təsdiq", "Bu yarışı silmək istədiyinizə əminsiniz?"):
            return

        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM teams WHERE competition_id=?", (comp_id,))
        cursor.execute("DELETE FROM questions WHERE competition_id=?", (comp_id,))
        cursor.execute("DELETE FROM competitions WHERE id=?", (comp_id,))
        self.conn.commit()

        messagebox.showinfo("Silindi", "Yarış uğurla silindi.")
        self.view_competitions()


if __name__ == "__main__":
    root = tk.Tk()
    app = CompetitionApp(root)
    root.mainloop()
