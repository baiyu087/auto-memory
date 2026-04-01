#!/usr/bin/env python3
"""
session-end-analyze.py
会话结束时分析对话，提取值得固化的教训，写入项目的 lessons.md

触发条件：SessionEnd hook
输入：stdin JSON，包含 transcript_path、cwd、session_id
"""

import json
import sys
import os
import subprocess
import tempfile
from pathlib import Path
from datetime import date


def extract_transcript(transcript_path: str) -> str:
    """从 JSONL transcript 文件提取对话文本"""
    messages = []
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue

                # transcript 格式：实际消息在 message 字段内
                msg = entry.get("message", entry)
                role = msg.get("role", "")
                if role not in ("user", "assistant"):
                    continue

                content = msg.get("content", "")
                if isinstance(content, list):
                    texts = [
                        c.get("text", "")
                        for c in content
                        if isinstance(c, dict) and c.get("type") == "text"
                    ]
                    content = " ".join(texts)
                if isinstance(content, str) and content.strip():
                    messages.append(f"[{role}]: {content[:500]}")
    except Exception:
        return ""

    # 只取最后 40 条，最多 8000 字符
    output = "\n".join(messages[-40:])
    return output[:8000]


def find_python() -> str:
    """找到可用的 python 命令"""
    for cmd in ("python3", "python"):
        try:
            result = subprocess.run(
                [cmd, "--version"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return cmd
        except FileNotFoundError:
            continue
    return "python3"


def analyze_with_mc(prompt: str) -> str:
    """调用 mc --code 分析对话，通过 stdin 传入避免 shell glob 展开问题"""
    try:
        result = subprocess.run(
            ["mc", "--code", "-p", "--input-format", "text"],
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return ""


def main():
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)

    transcript_path = data.get("transcript_path", "")
    cwd = data.get("cwd", "")
    reason = data.get("reason", "")

    # 跳过 clear/resume 触发的会话
    if reason in ("clear", "resume"):
        sys.exit(0)

    if not transcript_path or not os.path.exists(transcript_path):
        sys.exit(0)

    if not cwd:
        sys.exit(0)

    # lessons.md 存放在项目根目录下
    lessons_file = Path(cwd) / "lessons.md"

    # 不存在时自动创建模板，无需手动初始化
    if not lessons_file.exists():
        lessons_file.parent.mkdir(parents=True, exist_ok=True)
        lessons_file.write_text(
            f"# {Path(cwd).name} 项目教训记录\n"
            f"<!-- meta: last_reviewed: {date.today().strftime('%Y-%m-%d')} -->\n"
            f"\n"
            f"> 自动维护机制：会话结束时由子代理分析，识别值得固化的规则写入此文件。\n"
            f"> 格式：`[日期] [信号类型] 内容`\n"
            f"> 信号类型：纠正(C) | 模式确认(P) | 边界发现(B) | 工具用法(T) | 偏好表达(X)\n"
            f"\n"
            f"---\n"
            f"\n"
            f"## 规则列表\n"
            f"\n",
            encoding="utf-8"
        )

    transcript_text = extract_transcript(transcript_path)
    if not transcript_text:
        sys.exit(0)

    existing_lessons = lessons_file.read_text(encoding="utf-8")
    today = date.today().strftime("%Y-%m-%d")

    prompt = f"""你是一个分析 Claude 会话的助手。

请分析以下对话记录，识别值得固化为长期规则的内容。

**识别信号类型：**
- (C) 纠正：用户明确纠正了 Claude 的错误理解或行为
- (P) 模式确认：用户确认某种做法是正确的，应该持续
- (B) 边界发现：发现某种情况下不应该做的事
- (T) 工具用法：关于特定工具或命令的正确使用方式
- (X) 偏好表达：用户表达了明确的格式或风格偏好

**判断标准（满足任一即值得记录）：**
1. 用户明确纠正了 Claude 的行为
2. 用户说"以后都这样"、"记住"等确认性语句
3. 发现了之前未知的约束或边界
4. 涉及跨会话都适用的规则

**已有教训（避免重复）：**
{existing_lessons}

**对话记录：**
{transcript_text}

**输出格式（如果没有值得记录的内容，输出 NONE）：**
每条教训一行，格式：
- [{today}] [信号类型] 具体规则描述（简洁，一句话）

只输出新的、不重复的教训条目，不要输出任何解释或前缀。"""

    analysis = analyze_with_mc(prompt)

    if not analysis or analysis.strip().upper() == "NONE":
        sys.exit(0)

    # 将新教训追加到 lessons.md
    with open(lessons_file, "a", encoding="utf-8") as f:
        f.write(f"\n{analysis}\n")


if __name__ == "__main__":
    main()
