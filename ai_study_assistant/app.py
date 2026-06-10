"""Tkinter 桌面界面。"""

from __future__ import annotations

import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ai_study_assistant import APP_NAME
from ai_study_assistant.database import DatabaseManager, User
from ai_study_assistant.services import ai_answer, draw_learning_badge, export_report, query_word


class StudyAssistantApp:
    """AI 学习助手主程序，负责界面创建与事件绑定。"""

    def __init__(self, root: tk.Tk, db_path: str | Path = "study_assistant.db") -> None:
        self.root = root
        self.db = DatabaseManager(db_path)
        self.current_user: User | None = None
        self.root.title(APP_NAME)
        self.root.geometry("980x680")
        self.root.minsize(900, 620)
        self._configure_style()
        self._show_login_page()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_style(self) -> None:
        self.root.configure(bg="#eef2ff")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#eef2ff")
        style.configure("Card.TFrame", background="#ffffff", relief="flat")
        style.configure("TLabel", background="#eef2ff", foreground="#111827", font=("Microsoft YaHei", 10))
        style.configure("Title.TLabel", background="#eef2ff", foreground="#3730a3", font=("Microsoft YaHei", 22, "bold"))
        style.configure("Card.TLabel", background="#ffffff", foreground="#111827", font=("Microsoft YaHei", 10))
        style.configure("TButton", font=("Microsoft YaHei", 10), padding=7)
        style.configure("Accent.TButton", background="#4f46e5", foreground="white")
        style.configure("Treeview", font=("Microsoft YaHei", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("Microsoft YaHei", 10, "bold"))

    def _clear_root(self) -> None:
        for widget in self.root.winfo_children():
            widget.destroy()

    def _show_login_page(self) -> None:
        self._clear_root()
        container = ttk.Frame(self.root, padding=30)
        container.pack(expand=True, fill="both")
        ttk.Label(container, text="AI 学习助手系统", style="Title.TLabel").pack(pady=(30, 10))
        ttk.Label(container, text="简化版 ChatGPT 学习助手 · Python 实训大作业", font=("Microsoft YaHei", 12)).pack(pady=(0, 25))

        card = ttk.Frame(container, style="Card.TFrame", padding=30)
        card.pack(ipadx=70, ipady=20)
        ttk.Label(card, text="用户名", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=8)
        ttk.Label(card, text="密码", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=8)
        self.username_var = tk.StringVar(value="student")
        self.password_var = tk.StringVar(value="123456")
        ttk.Entry(card, textvariable=self.username_var, width=30).grid(row=0, column=1, pady=8, padx=8)
        ttk.Entry(card, textvariable=self.password_var, width=30, show="*").grid(row=1, column=1, pady=8, padx=8)
        ttk.Button(card, text="登录", style="Accent.TButton", command=self._login).grid(row=2, column=0, pady=18, sticky="ew")
        ttk.Button(card, text="注册", command=self._register).grid(row=2, column=1, pady=18, sticky="ew")
        ttk.Label(card, text="提示：可直接注册 student / 123456 后登录。", style="Card.TLabel").grid(row=3, column=0, columnspan=2)

    def _register(self) -> None:
        try:
            self.current_user = self.db.register_user(self.username_var.get(), self.password_var.get())
            messagebox.showinfo("注册成功", "注册成功，已自动登录。")
            self._show_main_page()
        except sqlite3.IntegrityError:
            messagebox.showwarning("注册失败", "用户名已存在，请直接登录或更换用户名。")
        except ValueError as exc:
            messagebox.showwarning("注册失败", str(exc))

    def _login(self) -> None:
        try:
            self.current_user = self.db.login_user(self.username_var.get(), self.password_var.get())
            self._show_main_page()
        except ValueError as exc:
            messagebox.showwarning("登录失败", str(exc))

    def _show_main_page(self) -> None:
        self._clear_root()
        header = ttk.Frame(self.root, padding=(20, 12))
        header.pack(fill="x")
        ttk.Label(header, text=f"欢迎，{self.current_user.username}", style="Title.TLabel").pack(side="left")
        ttk.Button(header, text="退出登录", command=self._show_login_page).pack(side="right")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=18, pady=(0, 18))
        self._build_dashboard_tab()
        self._build_word_tab()
        self._build_mistake_tab()
        self._build_plan_tab()
        self._build_score_tab()
        self._build_study_time_tab()
        self._build_ai_tab()
        self.refresh_all()

    @property
    def user_id(self) -> int:
        if self.current_user is None:
            raise RuntimeError("未登录。")
        return self.current_user.id

    def _build_dashboard_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="首页统计")
        self.summary_vars = {
            "total_minutes": tk.StringVar(),
            "mistake_count": tk.StringVar(),
            "finished_plans": tk.StringVar(),
            "avg_score": tk.StringVar(),
        }
        titles = ["累计学习时长", "错题数量", "完成计划", "平均成绩"]
        keys = list(self.summary_vars)
        for index, title in enumerate(titles):
            card = ttk.Frame(tab, style="Card.TFrame", padding=18)
            card.grid(row=0, column=index, padx=10, pady=10, sticky="nsew")
            ttk.Label(card, text=title, style="Card.TLabel", font=("Microsoft YaHei", 11, "bold")).pack()
            ttk.Label(card, textvariable=self.summary_vars[keys[index]], style="Card.TLabel", font=("Arial", 22, "bold")).pack(pady=8)
            tab.columnconfigure(index, weight=1)
        ttk.Button(tab, text="导出学习报告 JSON", command=self._export_report).grid(row=1, column=0, padx=10, pady=20, sticky="ew")
        ttk.Button(tab, text="绘制 Turtle 学习徽章", command=self._draw_badge).grid(row=1, column=1, padx=10, pady=20, sticky="ew")
        self.recent_tree = self._make_tree(tab, ("类型", "内容", "日期"))
        self.recent_tree.grid(row=2, column=0, columnspan=4, sticky="nsew", pady=10)
        tab.rowconfigure(2, weight=1)

    def _build_word_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="单词查询")
        self.word_var = tk.StringVar()
        ttk.Label(tab, text="输入英文单词：").pack(anchor="w")
        row = ttk.Frame(tab)
        row.pack(fill="x", pady=8)
        ttk.Entry(row, textvariable=self.word_var).pack(side="left", expand=True, fill="x")
        ttk.Button(row, text="查询", command=self._query_word).pack(side="left", padx=8)
        self.word_result = tk.Text(tab, height=16, wrap="word", font=("Microsoft YaHei", 11))
        self.word_result.pack(expand=True, fill="both", pady=10)

    def _build_mistake_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="错题管理")
        form = ttk.Frame(tab)
        form.pack(fill="x")
        self.mistake_subject = tk.StringVar(value="数学")
        self.mistake_question = tk.StringVar()
        self.mistake_answer = tk.StringVar()
        for label, var in [("科目", self.mistake_subject), ("题目", self.mistake_question), ("答案", self.mistake_answer)]:
            ttk.Label(form, text=label).pack(side="left", padx=(0, 4))
            ttk.Entry(form, textvariable=var, width=24).pack(side="left", padx=(0, 10))
        ttk.Button(form, text="添加错题", command=self._add_mistake).pack(side="left")
        ttk.Button(form, text="删除选中", command=self._delete_mistake).pack(side="left", padx=8)
        self.mistake_tree = self._make_tree(tab, ("ID", "科目", "题目", "答案", "时间"))
        self.mistake_tree.pack(expand=True, fill="both", pady=12)

    def _build_plan_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="学习计划")
        form = ttk.Frame(tab)
        form.pack(fill="x")
        self.plan_title = tk.StringVar()
        self.plan_date = tk.StringVar(value="2026-06-30")
        ttk.Label(form, text="计划").pack(side="left")
        ttk.Entry(form, textvariable=self.plan_title, width=42).pack(side="left", padx=8)
        ttk.Label(form, text="目标日期 YYYY-MM-DD").pack(side="left")
        ttk.Entry(form, textvariable=self.plan_date, width=16).pack(side="left", padx=8)
        ttk.Button(form, text="添加计划", command=self._add_plan).pack(side="left")
        ttk.Button(form, text="切换完成状态", command=self._toggle_plan).pack(side="left", padx=8)
        self.plan_tree = self._make_tree(tab, ("ID", "计划", "目标日期", "状态"))
        self.plan_tree.pack(expand=True, fill="both", pady=12)

    def _build_score_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="成绩统计")
        form = ttk.Frame(tab)
        form.pack(fill="x")
        self.score_subject = tk.StringVar(value="Python")
        self.score_value = tk.StringVar(value="95")
        ttk.Label(form, text="科目").pack(side="left")
        ttk.Entry(form, textvariable=self.score_subject, width=20).pack(side="left", padx=8)
        ttk.Label(form, text="成绩").pack(side="left")
        ttk.Entry(form, textvariable=self.score_value, width=12).pack(side="left", padx=8)
        ttk.Button(form, text="录入成绩", command=self._add_score).pack(side="left")
        self.score_tree = self._make_tree(tab, ("ID", "科目", "成绩", "日期"))
        self.score_tree.pack(expand=True, fill="both", pady=12)

    def _build_study_time_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="学习时长")
        form = ttk.Frame(tab)
        form.pack(fill="x")
        self.minutes_var = tk.StringVar(value="30")
        self.note_var = tk.StringVar(value="复习 Python 数据库编程")
        ttk.Label(form, text="分钟").pack(side="left")
        ttk.Entry(form, textvariable=self.minutes_var, width=10).pack(side="left", padx=8)
        ttk.Label(form, text="备注").pack(side="left")
        ttk.Entry(form, textvariable=self.note_var, width=45).pack(side="left", padx=8)
        ttk.Button(form, text="记录学习", command=self._add_study_time).pack(side="left")
        self.study_tree = self._make_tree(tab, ("ID", "日期", "时长", "备注"))
        self.study_tree.pack(expand=True, fill="both", pady=12)

    def _build_ai_tab(self) -> None:
        tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(tab, text="AI 问答")
        self.ai_question = tk.StringVar(value="我应该如何制定 Python 学习计划？")
        row = ttk.Frame(tab)
        row.pack(fill="x")
        ttk.Entry(row, textvariable=self.ai_question).pack(side="left", expand=True, fill="x")
        ttk.Button(row, text="提问", command=self._ask_ai).pack(side="left", padx=8)
        self.ai_text = tk.Text(tab, height=18, wrap="word", font=("Microsoft YaHei", 11))
        self.ai_text.pack(expand=True, fill="both", pady=12)

    def _make_tree(self, parent: tk.Widget, columns: tuple[str, ...]) -> ttk.Treeview:
        tree = ttk.Treeview(parent, columns=columns, show="headings")
        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=130, anchor="center")
        return tree

    def _query_word(self) -> None:
        try:
            result = query_word(self.word_var.get())
            self.word_result.delete("1.0", "end")
            self.word_result.insert(
                "end",
                f"单词：{result['word']}\n音标：{result['phonetic']}\n释义：{result['meaning']}\n来源：{result['source']}",
            )
        except ValueError as exc:
            messagebox.showwarning("查询失败", str(exc))

    def _add_mistake(self) -> None:
        try:
            self.db.add_mistake(self.user_id, self.mistake_question.get(), self.mistake_answer.get(), self.mistake_subject.get())
            self.mistake_question.set("")
            self.mistake_answer.set("")
            self.refresh_all()
        except ValueError as exc:
            messagebox.showwarning("添加失败", str(exc))

    def _delete_mistake(self) -> None:
        selected = self.mistake_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要删除的错题。")
            return
        mistake_id = int(self.mistake_tree.item(selected[0], "values")[0])
        self.db.delete_mistake(mistake_id, self.user_id)
        self.refresh_all()

    def _add_plan(self) -> None:
        try:
            self.db.add_plan(self.user_id, self.plan_title.get(), self.plan_date.get())
            self.plan_title.set("")
            self.refresh_all()
        except ValueError as exc:
            messagebox.showwarning("计划错误", f"请检查计划内容和日期格式：{exc}")

    def _toggle_plan(self) -> None:
        selected = self.plan_tree.selection()
        if selected:
            plan_id = int(self.plan_tree.item(selected[0], "values")[0])
            self.db.toggle_plan(plan_id, self.user_id)
            self.refresh_all()

    def _add_score(self) -> None:
        try:
            self.db.add_score(self.user_id, self.score_subject.get(), float(self.score_value.get()))
            self.refresh_all()
        except ValueError as exc:
            messagebox.showwarning("成绩错误", str(exc))

    def _add_study_time(self) -> None:
        try:
            self.db.add_study_record(self.user_id, int(self.minutes_var.get()), self.note_var.get())
            self.refresh_all()
        except ValueError as exc:
            messagebox.showwarning("记录失败", str(exc))

    def _ask_ai(self) -> None:
        try:
            summary = self.db.user_summary(self.user_id)
            answer = ai_answer(self.ai_question.get(), summary)
            self.db.add_qa_history(self.user_id, self.ai_question.get(), answer)
            self.ai_text.insert("end", f"我：{self.ai_question.get()}\n助手：{answer}\n\n")
        except ValueError as exc:
            messagebox.showwarning("提问失败", str(exc))

    def _export_report(self) -> None:
        path = filedialog.asksaveasfilename(
            title="保存学习报告",
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json")],
            initialfile="学习报告.json",
        )
        if not path:
            return
        rows = {
            "study_records": [dict(row) for row in self.db.fetch_all("SELECT record_date, minutes, note FROM study_records WHERE user_id = ?", (self.user_id,))],
            "mistakes": [dict(row) for row in self.db.fetch_all("SELECT subject, question, answer, created_at FROM mistakes WHERE user_id = ?", (self.user_id,))],
            "plans": [dict(row) for row in self.db.fetch_all("SELECT title, target_date, status FROM plans WHERE user_id = ?", (self.user_id,))],
            "scores": [dict(row) for row in self.db.fetch_all("SELECT subject, score, exam_date FROM scores WHERE user_id = ?", (self.user_id,))],
        }
        output = export_report(path, self.current_user.username, self.db.user_summary(self.user_id), rows)
        messagebox.showinfo("导出成功", f"报告已保存到：{output}")

    def _draw_badge(self) -> None:
        if self.current_user:
            draw_learning_badge(self.current_user.username)

    def refresh_all(self) -> None:
        if self.current_user is None:
            return
        summary = self.db.user_summary(self.user_id)
        self.summary_vars["total_minutes"].set(f"{summary['total_minutes']} 分钟")
        self.summary_vars["mistake_count"].set(f"{summary['mistake_count']} 道")
        self.summary_vars["finished_plans"].set(f"{summary['finished_plans']} 个")
        self.summary_vars["avg_score"].set(f"{summary['avg_score']} 分")
        self._fill_tree(self.mistake_tree, self.db.fetch_all("SELECT id, subject, question, answer, created_at FROM mistakes WHERE user_id = ? ORDER BY id DESC", (self.user_id,)))
        self._fill_tree(self.plan_tree, self.db.fetch_all("SELECT id, title, target_date, status FROM plans WHERE user_id = ? ORDER BY target_date", (self.user_id,)))
        self._fill_tree(self.score_tree, self.db.fetch_all("SELECT id, subject, score, exam_date FROM scores WHERE user_id = ? ORDER BY exam_date DESC", (self.user_id,)))
        self._fill_tree(self.study_tree, self.db.fetch_all("SELECT id, record_date, minutes, note FROM study_records WHERE user_id = ? ORDER BY record_date DESC, id DESC", (self.user_id,)))
        self._refresh_recent()

    def _refresh_recent(self) -> None:
        rows = []
        rows.extend(("错题", row["question"], row["created_at"][:10]) for row in self.db.fetch_all("SELECT question, created_at FROM mistakes WHERE user_id = ? ORDER BY id DESC LIMIT 5", (self.user_id,)))
        rows.extend(("计划", row["title"], row["target_date"]) for row in self.db.fetch_all("SELECT title, target_date FROM plans WHERE user_id = ? ORDER BY id DESC LIMIT 5", (self.user_id,)))
        self._fill_tree(self.recent_tree, rows[:8])

    def _fill_tree(self, tree: ttk.Treeview, rows: list[object]) -> None:
        tree.delete(*tree.get_children())
        for row in rows:
            values = tuple(row) if not isinstance(row, sqlite3.Row) else tuple(row)
            tree.insert("", "end", values=values)

    def _on_close(self) -> None:
        self.db.close()
        self.root.destroy()
