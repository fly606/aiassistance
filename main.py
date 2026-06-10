"""AI 学习助手系统入口。"""

from __future__ import annotations

import tkinter as tk

from ai_study_assistant.app import StudyAssistantApp


def main() -> None:
    root = tk.Tk()
    StudyAssistantApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
