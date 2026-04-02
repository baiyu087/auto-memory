# auto-memory

Claude Code 插件，自动从会话中提取经验教训，并帮助你将重要规则固化到 `CLAUDE.md`。

## 工作原理

```
会话结束   → 分析对话记录 → 追加到 lessons.md
会话开始   → 读取 lessons.md → 注入上下文
每隔 7 天  → 提醒运行 /promote-lessons
/promote-lessons → 复审教训 → 写入 CLAUDE.md
```

## 功能特性

- **自动捕获**：会话结束时分析对话记录，提取值得保留的教训（纠正、模式确认、边界发现、工具用法、偏好表达）
- **自动注入**：会话开始时将项目教训注入系统提示词，让 Claude 跨会话记住规则
- **定期提醒**：每 7 天提醒一次复审积累的教训
- **晋升规则**：`/promote-lessons` 技能支持逐条复审，选择性写入用户级或项目级 `CLAUDE.md`

## 环境要求

- Python 3.x（`python3` 或 `python` 在 PATH 中可用）
- Claude Code CLI 可用。默认使用 `mc --code` 命令，如需调整请修改 `hooks/session-end-analyze.py` 中的 `analyze_with_mc()` 函数，将其替换为你自己的 CC 启动命令（如 `claude`）

## 安装

```bash
/plugin marketplace add baiyu087/auto-memory
/plugin install auto-memory@auto-memory
```

## 存储位置

教训文件存放在项目根目录：
```
<项目根目录>/lessons.md
```

首次会话结束时**自动创建**，无需手动初始化。

## 教训类型

| 类型 | 说明 |
|------|------|
| (C) 纠正 | 用户明确纠正了 Claude 的行为 |
| (P) 模式确认 | 用户确认某种做法应该持续 |
| (B) 边界发现 | 发现 Claude 不应该做的事 |
| (T) 工具用法 | 工具或命令的正确使用方式 |
| (X) 偏好表达 | 用户表达了格式或风格偏好 |

## 技能

### `/promote-lessons`

复审 `lessons.md` 中的所有教训，选择性写入 `CLAUDE.md`：
- 一次展示所有教训，标注建议级别（用户级 / 项目级）
- 支持逐条指定：`U` 用户级、`P` 项目级、`S` 跳过、`D` 删除
- 写入前自动去重，避免与现有规则重复
- 完成后更新 `last_reviewed` 日期

## License

MIT
