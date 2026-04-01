#!/usr/bin/env python3
"""
session-start-lessons.py
会话开始时读取项目 lessons.md，注入为系统上下文。
若距上次复审超过 7 天且有教训条目，追加提醒信息。

触发条件：SessionStart hook（startup 时）
输入：stdin JSON，包含 cwd、session_id
"""

import json
import sys
import re
from pathlib import Path
from datetime import date, datetime


REVIEW_INTERVAL_DAYS = 7


def get_last_reviewed(content: str) -> date | None:
    """从文件内容解析 last_reviewed 元数据"""
    match = re.search(r'<!--\s*meta:\s*last_reviewed:\s*(\d{4}-\d{2}-\d{2})\s*-->', content)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%d").date()
        except ValueError:
            pass
    return None


def count_lessons(content: str) -> int:
    """统计教训条目数量"""
    return sum(1 for line in content.splitlines() if line.strip().startswith("- ["))


def main():
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)

    cwd = data.get("cwd", "")
    if not cwd:
        sys.exit(0)

    # lessons.md 存放在项目根目录下
    lessons_file = Path(cwd) / "lessons.md"

    if not lessons_file.exists():
        sys.exit(0)

    lessons_content = lessons_file.read_text(encoding="utf-8")

    # 检查是否有实际教训内容
    lesson_count = count_lessons(lessons_content)
    if lesson_count == 0:
        sys.exit(0)

    # 构建系统消息：注入教训内容
    system_msg = f"【历史教训回顾】以下是本项目积累的经验教训，请在本次会话中严格遵守：\n\n{lessons_content}"

    # 检查是否需要提醒复审（距上次复审超过 7 天）
    last_reviewed = get_last_reviewed(lessons_content)
    today = date.today()

    if last_reviewed is None or (today - last_reviewed).days >= REVIEW_INTERVAL_DAYS:
        days_info = f"{(today - last_reviewed).days} 天" if last_reviewed else "从未"
        system_msg += (
            f"\n\n---\n"
            f"⚠️ **教训复审提醒**：距上次复审已过 {days_info}，"
            f"当前共有 {lesson_count} 条教训。\n"
            f"建议本次会话结束前运行 `/promote-lessons` 将重要规则固化到 CLAUDE.md。"
        )

    output = {"systemMessage": system_msg}
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
