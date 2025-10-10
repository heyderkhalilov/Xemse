import tkinter as tk
from tkinter import simpledialog, PhotoImage, ttk
import sqlite3
from datetime import datetime
import math
import os

class CompetitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Competition Manager")

        # Fullscreen
        self.root.state("zoomed")  # Windows
        # self.root.attributes("-fullscreen", True)  # Linux/Mac

        self.conn = sqlite3.connect("competition.db")
        self.create_tables()

        self.current_competition_id = None
        self.teams = {}

        self.team_colors = ["#3498db", "#2ecc71", "#e67e22", "#e74c3c",
                            "#9b59b6", "#1abc9c", "#f39c12", "#2c3e50"]

        # Background image (optional)
        self.bg_image_path = "background.png"  # Place your background image in the same folder
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
        self.conn.commit()

    def set_background(self):
        """Set background image or gradient color."""
        if os.path.exists(self.bg_image_path):
            bg = PhotoImage(file=self.bg_image_path)
            self.bg_label = tk.Label(self.root, image=bg)
            self.bg_label.image = bg
            self.bg_label.place(relwidth=1, relheight=1)
        else:
            # fallback gradient-like background using color blocks
            self.root.configure(bg="#74b9ff")

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.set_background()

    def create_navbar(self, back_command=None, title=""):
        """Creates a colored header with optional back button."""
        header = tk.Frame(self.root, bg="#0984e3", height=60)
        header.pack(fill="x")

        if back_command:
            back_btn = tk.Button(header, text="⬅ Geri", font=("Arial", 14, "bold"),
                                 bg="#d63031", fg="white", activebackground="#e17055",
                                 relief="flat", padx=20, command=back_command)
            back_btn.pack(side="left", padx=20, pady=10)

        tk.Label(header, text=title, font=("Arial", 22, "bold"),
                 bg="#0984e3", fg="white").pack(pady=10)

    def modern_button(self, parent, text, color, command, icon=None):
        """Reusable modern button style."""
        return tk.Button(
            parent,
            text=(icon + " " + text) if icon else text,
            font=("Arial", 18, "bold"),
            bg=color,
            fg="white",
            activebackground="#636e72",
            relief="flat",
            width=25,
            height=2,
            cursor="hand2",
            command=command
        )

    def modern_button_delete(self, parent, text, color, command, icon=None):
        return tk.Button(
            parent,
            text=(icon + " " + text) if icon else text,
            font=("Arial", 18, "bold"),
            bg=color,
            fg="white",
            activebackground="#636e72",
            relief="flat",
            width=5,
            height=2,
            cursor="hand2",
            command=command
        )

    def main_menu(self):
        self.clear_window()
        self.create_navbar(title="🏆 Yarış Meneceri")

        frame = tk.Frame(self.root, bg="#74b9ff")
        frame.pack(expand=True)

        self.modern_button(frame, "Yeni yarış yarat", "#00b894", self.create_competition, "➕").pack(pady=20)
        self.modern_button(frame, "Köhnə yarışlara bax", "#0984e3", self.view_competitions, "📂").pack(pady=20)
        self.modern_button(frame, "Çıxış", "#d63031", self.root.quit, "❌").pack(pady=20)

    def create_competition(self):
        name = simpledialog.askstring("Yarış", "Yarışın adını daxil edin:")
        if name:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO competitions (name, date_created) VALUES (?, ?)", (name, datetime.now()))
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

        self.modern_button(frame, "🚀 Yarışı Başlat", "#6c5ce7", self.start_competition).pack(pady=40)

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
        cursor.execute("SELECT id, name, score FROM teams WHERE competition_id=?", (self.current_competition_id,))
        teams = cursor.fetchall()

        self.teams = {tid: {"name": n, "score": s} for tid, n, s in teams}

        self.render_leaderboard()



    def render_leaderboard(self):
        if hasattr(self, "board") and self.board.winfo_exists():
            self.board.destroy()

        sorted_teams = list(self.teams.items())  # ensure it's a list

        # Create new scoreboard area
        self.board = tk.Frame(self.root, bg="#74b9ff")
        self.board.pack(expand=True, fill="both")

        self.labels = {}
        n = len(sorted_teams)
        cols = 2
        rows = math.ceil(n / cols)

        # Dropdown values
        xal_values = [100 * i for i in range(0, 11)]  # [0,100,200,...,1000]

        # ---------- Xal selector (top row) ----------
        xal_frame = tk.Frame(self.board, bg="#0984e3")
        xal_frame.grid(row=0, column=0, columnspan=cols, sticky="ew", padx=10, pady=(12, 8))

        tk.Label(
            xal_frame,
            text="Xal:",
            font=("Arial", 18, "bold"),
            bg="#0984e3",
            fg="white"
        ).grid(row=0, column=0, padx=(10, 8), pady=8, sticky="w")

        self.xal_var = tk.IntVar(value=0)
        style = ttk.Style()
        style.configure("Large.TCombobox", font=("Arial", 16), padding=6)

        xal_combo = ttk.Combobox(
            xal_frame,
            textvariable=self.xal_var,
            values=xal_values,
            width=6,
            style="Large.TCombobox",
            state="readonly"
        )
        # ipady increases internal vertical padding => visually taller combobox
        xal_combo.grid(row=0, column=1, padx=(0, 10), pady=8, ipady=6, sticky="w")
        xal_combo.set(0)

        # ---------- Team boxes (start from row 1) ----------
        start_row = 1
        for i, (team_id, team) in enumerate(sorted_teams):
            r, c = divmod(i, cols)
            color = self.team_colors[i % len(self.team_colors)]
            frame = tk.Frame(self.board, bg=color, padx=30, pady=15, relief="flat", bd=10)
            frame.grid(row=r + start_row, column=c, padx=60, pady=30, sticky="nsew")

            tk.Label(frame, text=team["name"], font=("Arial", 22, "bold"), bg=color, fg="white") \
                .grid(row=0, column=0, columnspan=3, pady=10)
            lbl = tk.Label(frame, text=str(team["score"]), font=("Arial", 32, "bold"), bg=color, fg="white")
            lbl.grid(row=1, column=1, pady=10)
            self.labels[team_id] = lbl

            tk.Button(frame, text="+", font=("Arial", 22, "bold"), bg="#2ecc71", fg="white", relief="flat",
                      width=3, command=lambda t=team_id: self.update_score(t, self.xal_var.get())) \
                .grid(row=1, column=2, padx=20)
            tk.Button(frame, text="-", font=("Arial", 22, "bold"), bg="#e74c3c", fg="white", relief="flat",
                      width=3, command=lambda t=team_id: self.update_score(t, -100)) \
                .grid(row=1, column=0, padx=20)

        # ---------- Grid configuration ----------
        # Make top row (xal selector) fixed-ish so it doesn't get squashed
        top_row_min = 80  # tweak this to make the top selector taller/shorter
        self.board.grid_rowconfigure(0, weight=0, minsize=top_row_min)

        # Make only the team rows expandable
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

            # Load competition button
            btn = self.modern_button(item_frame, f"{name}", "#0984e3",
                                     lambda cid=comp_id: self.load_old_competition(cid))
            btn.pack(side="left", padx=10)

            # Delete button
            del_btn =  self.modern_button_delete(item_frame, "Sil", "#d63031", 
                                          lambda cid=comp_id: self.delete_competition(cid))
            del_btn.pack(side="left", padx=10)

    def load_old_competition(self, comp_id):
        self.current_competition_id = comp_id
        self.load_scoreboard()

    def delete_competition(self, comp_id):
        from tkinter import messagebox
        confirm = messagebox.askyesno("Təsdiq", "Bu yarışı silmək istədiyinizə əminsiniz?")
        if not confirm:
            return

        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM teams WHERE competition_id=?", (comp_id,))
        cursor.execute("DELETE FROM competitions WHERE id=?", (comp_id,))
        self.conn.commit()

        messagebox.showinfo("Silindi", "Yarış uğurla silindi.")
        self.view_competitions()  # Refresh the list    


if __name__ == "__main__":
    root = tk.Tk()
    app = CompetitionApp(root)
    root.mainloop()
