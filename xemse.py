import tkinter as tk
from tkinter import simpledialog, PhotoImage, ttk, filedialog, messagebox
from PIL import Image, ImageTk
import sqlite3
from datetime import datetime
import math
import os


class CompetitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Competition Manager")

        # Fullscreen-ish
        try:
            self.root.state("zoomed")
        except Exception:
            pass

        self.conn = sqlite3.connect("competition.db")
        self.create_tables()

        self.current_competition_id = None
        self.teams = {}

        self.team_colors = ["#3498db", "#2ecc71", "#e67e22", "#e74c3c",
                            "#9b59b6", "#1abc9c", "#f39c12", "#2c3e50"]

        self.bg_image_path = "background.png"
        self.bg_label = None

        self.main_menu()

    # ---------------------- DATABASE ----------------------

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
                competition_id INTEGER,
                question_text TEXT,
                image_path TEXT,
                FOREIGN KEY (competition_id) REFERENCES competitions(id)
            )
        """)
        self.conn.commit()

    # ---------------------- UI HELPERS ----------------------

    def set_background(self):
        if os.path.exists(self.bg_image_path):
            try:
                bg = PhotoImage(file=self.bg_image_path)
                self.bg_label = tk.Label(self.root, image=bg)
                self.bg_label.image = bg
                self.bg_label.place(relwidth=1, relheight=1)
                return
            except Exception:
                pass
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
                                 bg="#d63031", fg="white", activebackground="#e17055",
                                 relief="flat", padx=20, command=back_command)
            back_btn.pack(side="left", padx=20, pady=10)

        tk.Label(header, text=title, font=("Arial", 22, "bold"),
                 bg="#0984e3", fg="white").pack(pady=10)

    def modern_button(self, parent, text, color, command, icon=None):
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

    # ---------------------- MAIN MENU ----------------------

    def main_menu(self):
        self.clear_window()
        self.create_navbar(title="🏆 Yarış Meneceri")

        frame = tk.Frame(self.root, bg="#74b9ff")
        frame.pack(expand=True)

        self.modern_button(frame, "Yeni yarış yarat", "#00b894", self.create_competition, "➕").pack(pady=20)
        self.modern_button(frame, "Köhnə yarışlara bax", "#0984e3", self.view_competitions, "📂").pack(pady=20)
        self.modern_button(frame, "Çıxış", "#d63031", self.root.quit, "❌").pack(pady=20)

    # ---------------------- COMPETITION CREATION ----------------------

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

    # ---------------------- SCOREBOARD ----------------------

    def load_scoreboard(self):
        if not self.current_competition_id:
            messagebox.showwarning("Xəbərdarlıq", "Əvvəlcə yarış yaradın və ya köhnə yarışı yükləyin.")
            return

        self.clear_window()
        self.create_navbar(self.main_menu, "Canlı xal lövhəsi")

        toolbar = tk.Frame(self.root, bg="#74b9ff")
        toolbar.pack(pady=10)

        self.modern_button(toolbar, "📋 Suallara bax", "#6c5ce7", self.open_questions_modal).pack(side="left", padx=10)
        self.modern_button(toolbar, "➕ Yeni sual əlavə et", "#00b894", self.add_questions).pack(side="left", padx=10)

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, score FROM teams WHERE competition_id=?", (self.current_competition_id,))
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
        rows = math.ceil(max(1, n) / cols)

        xal_values = [100 * i for i in range(0, 11)]

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

            tk.Button(frame, text="+", font=("Arial", 22, "bold"), bg="#2ecc71", fg="white", relief="flat",
                      width=3, command=lambda t=team_id: self.update_score(t, self.xal_var.get())).grid(row=1, column=2, padx=20)
            tk.Button(frame, text="-", font=("Arial", 22, "bold"), bg="#e74c3c", fg="white", relief="flat",
                      width=3, command=lambda t=team_id: self.update_score(t, -100)).grid(row=1, column=0, padx=20)

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

    # ---------------------- QUESTIONS (Add / Save) ----------------------

    def add_questions(self):
        if not self.current_competition_id:
            messagebox.showwarning("Xəbərdarlıq", "Əvvəlcə yarış yaradın və ya köhnə yarışı yükləyin.")
            return

        self.clear_window()
        self.create_navbar(lambda: self.load_scoreboard(), "Suallar əlavə et")

        frame = tk.Frame(self.root, bg="#74b9ff")
        frame.pack(expand=True, pady=20)

        self.questions_data = []

        for i in range(3):
            q_frame = tk.Frame(frame, bg="#0984e3", padx=20, pady=20, relief="raised", bd=3)
            q_frame.pack(pady=15, fill="x", padx=30)

            tk.Label(q_frame, text=f"Sual {i+1}:", font=("Arial", 16, "bold"), bg="#0984e3", fg="white").pack(anchor="w")

            entry = tk.Entry(q_frame, font=("Arial", 16), width=80, bd=3, relief="ridge")
            entry.pack(pady=5)

            img_label = tk.Label(q_frame, bg="#0984e3")
            img_label.pack(pady=5)

            btn_frame = tk.Frame(q_frame, bg="#0984e3")
            btn_frame.pack(pady=5)

            def choose_image(lbl=img_label, idx=i):
                path = filedialog.askopenfilename(
                    title="Şəkil seçin",
                    filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif")]
                )
                if path:
                    try:
                        img = Image.open(path)
                        img.thumbnail((200, 200))
                        img_tk = ImageTk.PhotoImage(img)
                        lbl.config(image=img_tk)
                        lbl.image = img_tk
                        # store
                        self.questions_data[idx]["img_path"] = path
                    except Exception as e:
                        messagebox.showerror("Xəta", f"Şəkil yüklənərkən xəta: {e}")

            add_img_btn = tk.Button(btn_frame, text="📷 Şəkil əlavə et", font=("Arial", 14),
                                    bg="#00b894", fg="white", relief="flat", command=choose_image)
            add_img_btn.pack(side="left", padx=8)

            remove_img_btn = tk.Button(btn_frame, text="❌ Şəkili sil", font=("Arial", 14),
                                       bg="#e17055", fg="white", relief="flat",
                                       command=lambda lbl=img_label, idx=i: self._remove_image_preview(lbl, idx))
            remove_img_btn.pack(side="left", padx=8)

            self.questions_data.append({
                "text_entry": entry,
                "img_label": img_label,
                "img_path": None
            })

        self.modern_button(frame, "💾 Yadda saxla", "#0984e3", self.save_questions).pack(pady=30)

    def _remove_image_preview(self, lbl, idx):
        lbl.config(image="", text="")
        if 0 <= idx < len(self.questions_data):
            self.questions_data[idx]["img_path"] = None

    def save_questions(self):
        cursor = self.conn.cursor()
        saved_any = False
        for q in self.questions_data:
            text = q["text_entry"].get().strip()
            img_path = q["img_path"]
            if text:
                cursor.execute("""
                    INSERT INTO questions (competition_id, question_text, image_path)
                    VALUES (?, ?, ?)
                """, (self.current_competition_id, text, img_path))
                saved_any = True
        self.conn.commit()
        if saved_any:
            messagebox.showinfo("Uğurla", "Suallar əlavə olundu!")
        else:
            messagebox.showinfo("Məlumat", "Yadda saxlanacaq heç bir sual tapılmadı.")
        self.load_scoreboard()

    # ---------------------- QUESTIONS (Modal viewer + edit/delete) ----------------------

    def open_questions_modal(self):
        if not self.current_competition_id:
            messagebox.showwarning("Xəbərdarlıq", "Əvvəlcə yarış yaradın və ya köhnə yarışı yükləyin.")
            return

        modal = tk.Toplevel(self.root)
        modal.title("📋 Yarış sualları")
        modal.geometry("900x700")
        modal.configure(bg="#74b9ff")
        modal.transient(self.root)
        modal.grab_set()

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, question_text, image_path FROM questions WHERE competition_id=?",
                       (self.current_competition_id,))
        questions = cursor.fetchall()

        if not questions:
            tk.Label(modal, text="Bu yarış üçün sual yoxdur.",
                     font=("Arial", 18, "bold"), bg="#74b9ff", fg="red").pack(pady=50)
            return

        index = tk.IntVar(value=0)

        content_frame = tk.Frame(modal, bg="#74b9ff")
        content_frame.pack(expand=True, fill="both")

        # functions that mutate questions MUST declare nonlocal if they change it:
        def show_question():
            for w in content_frame.winfo_children():
                w.destroy()

            qid, q_text, img_path = questions[index.get()]

            tk.Label(content_frame, text=f"{index.get()+1}. {q_text}",
                     font=("Arial", 22, "bold"), bg="#74b9ff", wraplength=800, justify="left").pack(pady=20)

            if img_path and os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    img.thumbnail((500, 400))
                    img_tk = ImageTk.PhotoImage(img)
                    lbl = tk.Label(content_frame, image=img_tk, bg="#74b9ff")
                    lbl.image = img_tk
                    lbl.pack(pady=10)
                except Exception:
                    tk.Label(content_frame, text="(Şəkil yüklənə bilmədi)", bg="#74b9ff").pack(pady=10)

            btn_frame = tk.Frame(content_frame, bg="#74b9ff")
            btn_frame.pack(pady=10)

            tk.Button(btn_frame, text="✏ Düzəliş et", font=("Arial", 14),
                      bg="#f39c12", fg="white", relief="flat",
                      command=lambda q=qid: edit_question(q)).pack(side="left", padx=10)
            tk.Button(btn_frame, text="🗑 Sil", font=("Arial", 14),
                      bg="#e74c3c", fg="white", relief="flat",
                      command=lambda q=qid: delete_question(q)).pack(side="left", padx=10)

        def next_q():
            if index.get() < len(questions) - 1:
                index.set(index.get() + 1)
                show_question()

        def prev_q():
            if index.get() > 0:
                index.set(index.get() - 1)
                show_question()

        def edit_question(qid):
            # nonlocal usage: we will re-query questions after update and reassign
            nonlocal questions

            # load current data to pre-fill
            cur = self.conn.cursor()
            cur.execute("SELECT question_text, image_path FROM questions WHERE id=?", (qid,))
            row = cur.fetchone()
            if not row:
                messagebox.showerror("Xəta", "Sual tapılmadı.")
                return
            cur_text, cur_img = row

            # Open a small edit window
            edit_win = tk.Toplevel(modal)
            edit_win.title("Sualı düzəliş et")
            edit_win.geometry("700x400")
            edit_win.transient(modal)
            edit_win.grab_set()

            tk.Label(edit_win, text="Sual mətni:", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
            text_entry = tk.Text(edit_win, font=("Arial", 14), height=6, wrap="word")
            text_entry.pack(fill="x", padx=10, pady=5)
            text_entry.insert("1.0", cur_text)

            img_preview = tk.Label(edit_win)
            img_preview.pack(pady=8)

            # show current image preview
            if cur_img and os.path.exists(cur_img):
                try:
                    im = Image.open(cur_img)
                    im.thumbnail((300, 250))
                    imtk = ImageTk.PhotoImage(im)
                    img_preview.config(image=imtk)
                    img_preview.image = imtk
                except Exception:
                    img_preview.config(text="(Şəkil yüklənə bilmədi)")

            new_image_path = {"path": cur_img}

            def choose_new_image():
                path = filedialog.askopenfilename(
                    title="Yeni şəkil seçin",
                    filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif")]
                )
                if path:
                    try:
                        im = Image.open(path)
                        im.thumbnail((300, 250))
                        imtk = ImageTk.PhotoImage(im)
                        img_preview.config(image=imtk)
                        img_preview.image = imtk
                        new_image_path["path"] = path
                    except Exception as e:
                        messagebox.showerror("Xəta", f"Şəkil yüklənərkən xeta: {e}")

            def remove_image_choice():
                new_image_path["path"] = None
                img_preview.config(image="", text="(Şəkil silinmişdir)")

            btns = tk.Frame(edit_win)
            btns.pack(pady=5)
            tk.Button(btns, text="📷 Yeni şəkil", bg="#00b894", fg="white", command=choose_new_image).pack(side="left", padx=6)
            tk.Button(btns, text="❌ Şəkili sil", bg="#e17055", fg="white", command=remove_image_choice).pack(side="left", padx=6)

            def apply_edit():
                new_text = text_entry.get("1.0", "end").strip()
                cur2 = self.conn.cursor()
                cur2.execute("UPDATE questions SET question_text=?, image_path=? WHERE id=?",
                             (new_text, new_image_path["path"], qid))
                self.conn.commit()
                # re-fetch questions list and refresh modal content
                cur2.execute("SELECT id, question_text, image_path FROM questions WHERE competition_id=?",
                             (self.current_competition_id,))
                questions = cur2.fetchall()
                # adjust index to point to updated question
                for idx, t in enumerate(questions):
                    if t[0] == qid:
                        index.set(idx)
                        break
                edit_win.destroy()
                show_question()

            tk.Button(edit_win, text="Yadda saxla", bg="#0984e3", fg="white", font=("Arial", 12), command=apply_edit).pack(pady=10)

        def delete_question(qid):
            nonlocal questions
            confirm = messagebox.askyesno("Təsdiq", "Bu sualı silmək istədiyinizə əminsiniz?")
            if confirm:
                cur = self.conn.cursor()
                cur.execute("DELETE FROM questions WHERE id=?", (qid,))
                self.conn.commit()
                cur.execute("SELECT id, question_text, image_path FROM questions WHERE competition_id=?",
                            (self.current_competition_id,))
                questions = cur.fetchall()
                if not questions:
                    modal.destroy()
                    return
                # clamp index
                index.set(min(index.get(), len(questions) - 1))
                show_question()

        nav_frame = tk.Frame(modal, bg="#74b9ff")
        nav_frame.pack(pady=20)
        tk.Button(nav_frame, text="⬅ Əvvəlki", font=("Arial", 16),
                  bg="#0984e3", fg="white", width=10, command=prev_q).pack(side="left", padx=10)
        tk.Button(nav_frame, text="Növbəti ➡", font=("Arial", 16),
                  bg="#0984e3", fg="white", width=10, command=next_q).pack(side="left", padx=10)

        show_question()

    # ---------------------- OLD COMPETITIONS ----------------------

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
            item_frame.pack(pady=10, fill="x", padx=20)

            btn = self.modern_button(item_frame, f"{name}", "#0984e3",
                                     lambda cid=comp_id: self.load_old_competition(cid))
            btn.pack(side="left", padx=10)

            del_btn = self.modern_button_delete(item_frame, "Sil", "#d63031",
                                                lambda cid=comp_id: self.delete_competition(cid))
            del_btn.pack(side="left", padx=10)

    def load_old_competition(self, comp_id):
        self.current_competition_id = comp_id
        self.load_scoreboard()

    def delete_competition(self, comp_id):
        confirm = messagebox.askyesno("Təsdiq", "Bu yarışı silmək istədiyinizə əminsiniz?")
        if not confirm:
            return

        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM teams WHERE competition_id=?", (comp_id,))
        cursor.execute("DELETE FROM questions WHERE competition_id=?", (comp_id,))
        cursor.execute("DELETE FROM competitions WHERE id=?", (comp_id,))
        self.conn.commit()

        messagebox.showinfo("Silindi", "Yarış uğurla silindi.")
        self.view_competitions()  # Refresh the list


if __name__ == "__main__":
    root = tk.Tk()
    app = CompetitionApp(root)
    root.mainloop()
