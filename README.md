# AI 学习助手系统（Python 实训大作业）

这是一个使用 Python 编写的桌面版「AI 学习助手系统」，定位为**简化版 ChatGPT 学习助手**。项目难度适中，适合作为 Python 实训课大作业展示，重点覆盖 Python 语法、函数模块、类与对象、GUI、数据库、文件操作、异常处理、海龟绘图和网络 API 等知识点。

## 功能清单

- **用户系统**：支持注册、登录，用户密码使用 SHA-256 摘要保存。
- **单词查询**：内置常用 Python 学习词汇；本地未命中时会调用 `dictionaryapi.dev` 网络词典 API。
- **错题管理**：按科目录入题目与答案，支持删除错题。
- **学习计划制定**：添加计划、设置目标日期、切换完成状态。
- **成绩统计**：录入科目成绩，首页自动计算平均分。
- **学习时长记录**：记录每天学习分钟数和备注，首页自动累计。
- **AI 问答模块**：基于关键词和个人学习数据生成学习建议，并保存问答历史。
- **学习报告导出**：将学习记录、错题、计划、成绩导出为 JSON 文件。
- **海龟绘图**：使用 Turtle 绘制专属学习徽章。

## 知识点对应表

| 课程知识点 | 项目中的体现 |
| --- | --- |
| Python 语法基础 | 变量、条件判断、循环、字符串格式化、异常分支等 |
| 组合数据类型 | `dict`、`list`、`tuple` 保存词典、统计数据和表格行 |
| 函数与模块 | `database.py`、`services.py`、`app.py` 分模块组织函数 |
| 海龟绘图 | `draw_learning_badge()` 使用 `turtle` 绘制学习徽章 |
| 文件操作 | `export_report()` 将学习报告写入 JSON 文件 |
| 异常处理 | 登录、注册、日期、成绩、网络查询等场景均有异常提示 |
| 类与对象 | `DatabaseManager`、`User`、`StudyAssistantApp` 封装数据和行为 |
| 界面设计 | 使用 `tkinter` 和 `ttk.Notebook` 制作多标签页桌面程序 |
| 数据库编程 | 使用 SQLite 建立用户表、学习记录表、错题表、计划表、成绩表 |
| requests / 网络 API | 若安装 `requests` 会优先使用；未安装时自动使用标准库 `urllib` 调用网络词典 |

## 数据库设计

项目启动后会自动创建 `study_assistant.db`，包含以下主要表：

### 用户表 users

| 字段 | 说明 |
| --- | --- |
| id | 用户 ID |
| username | 用户名 |
| password | 密码摘要 |

### 学习记录表 study_records

| 字段 | 说明 |
| --- | --- |
| id | 记录 ID |
| user_id | 用户 ID |
| record_date | 日期 |
| minutes | 学习时长（分钟） |
| note | 备注 |

### 错题表 mistakes

| 字段 | 说明 |
| --- | --- |
| id | 错题 ID |
| user_id | 用户 ID |
| question | 题目 |
| answer | 答案 |
| subject | 科目 |
| created_at | 创建时间 |

另外还包含 `plans`（学习计划表）、`scores`（成绩表）、`qa_history`（问答历史表）。

## 运行方式

本项目主要依赖 Python 标准库，建议使用 Python 3.10 或更高版本。

```bash
python main.py
```

首次使用时可以输入任意用户名和密码点击「注册」，之后再用该账号登录。界面中默认填入了 `student / 123456`，方便演示。

## 可选依赖

如希望网络词典优先使用 `requests`，可安装：

```bash
python -m pip install -r requirements.txt
```

即使没有安装 `requests`，程序也会使用 Python 标准库 `urllib` 查询网络词典。

## 项目结构

```text
.
├── main.py                         # 程序入口
├── ai_study_assistant/
│   ├── __init__.py                  # 应用名称和版本
│   ├── app.py                       # Tkinter 图形界面
│   ├── database.py                  # SQLite 数据库访问层
│   └── services.py                  # 单词查询、AI 问答、导出、Turtle 绘图
├── requirements.txt                 # 可选 requests 依赖
└── README.md                        # 项目说明
```

## 答辩展示建议

1. 先注册并登录，说明用户表和密码摘要。
2. 录入一条学习时长、一条错题、一条计划和一条成绩。
3. 回到首页展示累计时长、错题数量、完成计划和平均成绩。
4. 查询 `python` 或 `algorithm`，说明本地词典和网络 API。
5. 在 AI 问答中输入“我应该如何制定 Python 学习计划？”。
6. 点击导出 JSON 报告，说明文件操作。
7. 点击 Turtle 学习徽章，展示海龟绘图效果。
