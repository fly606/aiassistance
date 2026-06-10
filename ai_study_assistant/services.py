"""业务函数：单词查询、简易 AI 问答、报告导出与海龟绘图。"""

from __future__ import annotations

import importlib
import importlib.util
import json
import math
import turtle
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

LOCAL_WORDS: dict[str, dict[str, str]] = {
    "python": {"phonetic": "['paɪθən]", "meaning": "蟒蛇；Python 编程语言"},
    "algorithm": {"phonetic": "['ælɡərɪðəm]", "meaning": "算法，解题步骤"},
    "database": {"phonetic": "['deɪtəbeɪs]", "meaning": "数据库"},
    "function": {"phonetic": "['fʌŋkʃn]", "meaning": "函数；功能"},
    "object": {"phonetic": "['ɒbdʒɪkt]", "meaning": "对象；物体"},
    "exception": {"phonetic": "[ɪk'sepʃn]", "meaning": "异常；例外"},
}


def query_word(word: str) -> dict[str, str]:
    """先查本地词典，再尝试网络 API，最后给出友好提示。"""
    cleaned = word.strip().lower()
    if not cleaned:
        raise ValueError("请输入要查询的英文单词。")
    if cleaned in LOCAL_WORDS:
        return {"word": cleaned, **LOCAL_WORDS[cleaned], "source": "本地词典"}

    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{cleaned}"
    try:
        data = _get_json(url)
        first = data[0]
        phonetic = first.get("phonetic") or "暂无音标"
        definitions = first.get("meanings", [{}])[0].get("definitions", [{}])
        meaning = definitions[0].get("definition", "暂无释义")
        return {"word": cleaned, "phonetic": phonetic, "meaning": meaning, "source": "dictionaryapi.dev"}
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        return {
            "word": cleaned,
            "phonetic": "暂无音标",
            "meaning": f"未查到释义，可检查拼写或稍后重试。错误信息：{exc}",
            "source": "异常处理提示",
        }


def _get_json(url: str) -> Any:
    """优先使用 requests；未安装时使用 urllib，便于课堂环境直接运行。"""
    if importlib.util.find_spec("requests") is not None:
        requests = importlib.import_module("requests")
        response = requests.get(url, timeout=4)
        response.raise_for_status()
        return response.json()

    with urllib.request.urlopen(url, timeout=4) as response:
        return json.loads(response.read().decode("utf-8"))


def ai_answer(question: str, summary: dict[str, Any]) -> str:
    """规则型简易 AI：根据关键词和学习数据生成建议。"""
    q = question.strip()
    if not q:
        raise ValueError("请输入问题。")

    lower_q = q.lower()
    if any(keyword in lower_q for keyword in ["计划", "plan", "安排"]):
        return (
            "建议采用 25 分钟专注 + 5 分钟休息的番茄钟。"
            f"你目前累计学习 {summary['total_minutes']} 分钟，可以把今天任务拆成：复习错题、背单词、完成练习三步。"
        )
    if any(keyword in lower_q for keyword in ["错题", "mistake", "不会"]):
        return (
            f"你的错题本中已有 {summary['mistake_count']} 道题。"
            "建议按“错误原因—正确思路—同类题训练”三列整理，每周至少复盘一次。"
        )
    if any(keyword in lower_q for keyword in ["成绩", "score", "考试"]):
        return (
            f"当前录入成绩平均分为 {summary['avg_score']}。"
            "如果波动较大，先找出薄弱科目，再为每个薄弱点设置可量化的小目标。"
        )
    if any(keyword in lower_q for keyword in ["python", "编程", "代码"]):
        return "学习 Python 时可以按“语法—函数—文件—数据库—界面项目”的顺序推进，并坚持用小项目巩固。"

    return (
        "我是本地规则型 AI 学习助手。你可以问我：如何制定计划、如何整理错题、如何提高成绩、如何学习 Python。"
        "我会结合你的学习记录给出建议。"
    )


def export_report(path: str | Path, username: str, summary: dict[str, Any], rows: dict[str, list[dict[str, Any]]]) -> Path:
    """把学习报告导出为 JSON 文件，体现文件写入操作。"""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "username": username,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "details": rows,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def draw_learning_badge(username: str) -> None:
    """用 turtle 绘制学习徽章，体现海龟绘图知识点。"""
    screen = turtle.Screen()
    screen.title("学习徽章 - Turtle 海龟绘图")
    pen = turtle.Turtle()
    pen.speed(8)
    pen.pensize(3)

    colors = ["#4f46e5", "#06b6d4", "#22c55e", "#f59e0b", "#ef4444"]
    for index, color in enumerate(colors):
        pen.color(color)
        pen.penup()
        pen.goto(0, -20 - index * 8)
        pen.pendown()
        pen.circle(80 + index * 8)

    pen.penup()
    pen.goto(-65, 15)
    pen.color("#111827")
    pen.write("AI Study", font=("Arial", 22, "bold"))
    pen.goto(-70, -20)
    pen.write(f"{username} 加油!", font=("Arial", 15, "normal"))

    pen.goto(0, -95)
    pen.color("#f59e0b")
    pen.begin_fill()
    for _ in range(5):
        pen.forward(35)
        pen.right(144)
    pen.end_fill()

    pen.hideturtle()
    angle = 0
    while angle < 360:
        pen.penup()
        pen.goto(math.cos(math.radians(angle)) * 130, math.sin(math.radians(angle)) * 130)
        pen.dot(6, colors[(angle // 45) % len(colors)])
        angle += 45
    screen.mainloop()
