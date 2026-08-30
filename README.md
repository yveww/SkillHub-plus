# SkillHub+ — AI Skill 兼容性诊断平台

> 基于飞书 SkillHub 品牌延展，为 Skill 提供类 GitHub 的 Issue 反馈、AI 兼容性诊断、版本管理和 Fork 合并能力。

## 核心价值

企业自建 Skill 在市场发布后，在不同 Agent 环境、不同使用场景下效果差异巨大。SkillHub+ 提供：

1. **用户反馈窗口** — 飞书表单收集问题，零门槛提交
2. **AI 兼容性诊断** — 问题复现 → 多环境横测 → 适配定位 → 归因判定，站在 Skill 端看兼容性问题
3. **Issue 看板** — 飞书多维表格看板视图，状态流转一目了然
4. **版本管理** — 自动创建修复/适配版本记录，关联 Issue 与 CHANGELOG
5. **Fork & 合并** — 用户自定义 Fork，上游更新 Diff 对比，安全自动合并 + 冲突人工处理
6. **IM 交互卡片** — 诊断结果含适配建议推送到开发者飞书，卡片内直接操作

## 架构

```
用户反馈表单 ─→ Issues 表 (待分流)
                     │
                AI 智能分流
                ┌─────┼─────┐
            确认Bug  非Bug  待确认
                │
          创建修复分支 + 版本记录
                │
          IM 卡片通知开发者
                │
          Forks 表 (上游 Diff → 合并)
```

## 飞书多维表格结构

### Issues 表
| 字段 | 类型 | 说明 |
|------|------|------|
| Issue ID | 自动编号 | ISSUE-0001 |
| 标题 | 文本 | 问题标题 |
| Skill名称 | 文本 | 出问题的 Skill |
| Skill版本 | 文本 | 版本号 |
| 报告人 | 文本 | 反馈人 |
| Agent类型 | 单选 | Trae / Doubao / 飞书机器人 / 其他 |
| Prompt摘要 | 文本 | 用户 Prompt |
| 问题描述 | 文本 | 详细描述 |
| 严重程度 | 单选 | 轻微 / 一般 / 严重 |
| 状态 | 单选 | 待分流→确认Bug→修复中→已修复 |
| AI判定 | 单选 | 确认Bug / 非Bug / 待确认 |
| AI置信度 | 数字 | 0-100 |
| AI根因分析 | 文本 | 定位的根因 |
| 复现结果 | 单选 | 已复现 / 未复现 / 间歇复现 |
| 多Agent对比 | 文本 | 跨 Agent 对比结果 |
| 修复分支 | 文本 | AI 创建的修复分支名 |

### Versions 表
| 字段 | 类型 | 说明 |
|------|------|------|
| 版本号 | 文本 | 如 v1.2.1-fix |
| Skill名称 | 文本 | Skill 名称 |
| 状态 | 单选 | 草稿 / 已发布 |
| CHANGELOG | 文本 | 变更日志 |
| 修复Issue | 文本 | 关联的 Issue ID |
| 发布时间 | 日期时间 | 发布时间 |

### Forks 表
| 字段 | 类型 | 说明 |
|------|------|------|
| Fork名称 | 文本 | Fork 的名称 |
| 原版Skill | 文本 | 原版 Skill 名称 |
| 原版版本 | 文本 | Fork 时的原版版本 |
| Fork版本 | 文本 | Fork 自定义版本 |
| 自定义修改 | 文本 | 用户修改摘要 |
| 上游版本 | 文本 | 上游最新版本 |
| Diff摘要 | 文本 | 上游 Diff 变更摘要 |
| 合并状态 | 单选 | 待合并 / 已合并 / 暂不合并 |

## 文件说明

| 文件 | 作用 |
|------|------|
| `demo.py` | 主 Demo 脚本：插入 Issue → AI 分流 → 版本记录 → Fork → IM 通知 |
| `setup_views.py` | 配置看板视图、表单问题、可见字段 |
| `fork_merge.py` | Fork 合并演示：Diff 审阅 → 安全合并 → 冲突标记 |
| `config.json` | Base token、表 ID、视图 ID、表单 ID |
| `issues_fields.json` | Issues 表字段定义 |
| `versions_fields.json` | Versions 表字段定义 |
| `forks_fields.json` | Forks 表字段定义 |

## 快速开始

### 前置条件

1. **Python 3.8+**
2. **lark-cli** — 飞书命令行工具，用于通过 API 操作多维表格和发送 IM
   ```bash
   # 安装
   npm install -g @lark-sdk/lark-cli

   # 认证（首次使用需要登录飞书账号）
   lark-cli auth login
   ```
3. **飞书多维表格（Base）** — 需要一个飞书 Base 作为数据存储
   - 在飞书中新建一个多维表格
   - 复制 Base URL（形如 `https://你的域名.feishu.cn/base/xxxxxxxx`）
   - 运行 `setup_views.py` 会自动创建 Issues / Versions / Forks 三张表 + 看板视图 + 反馈表单

### 配置

将 `config.example.json` 复制为 `config.json`，替换为你自己的飞书 Base 信息：

```json
{
    "base_token": "YOUR_BASE_TOKEN",          // Base URL 中 /base/ 后面的部分
    "base_url": "https://xxx.feishu.cn/base/YOUR_BASE_TOKEN",
    "tables": {
        "issues": "YOUR_ISSUES_TABLE_ID",     // 运行 setup_views.py 后自动生成
        "versions": "YOUR_VERSIONS_TABLE_ID",
        "forks": "YOUR_FORKS_TABLE_ID"
    },
    "views": {
        "issues_default": "YOUR_VIEW_ID",     // 运行 setup_views.py 后自动生成
        "versions_default": "YOUR_VIEW_ID",
        "forks_default": "YOUR_VIEW_ID",
        "issues_kanban": "YOUR_VIEW_ID"
    },
    "forms": {
        "issues_feedback": "YOUR_FORM_ID"    // 运行 setup_views.py 后自动生成
    }
}
```

> **提示**：`tables`、`views`、`forms` 中的 ID 会在首次运行 `setup_views.py` 时自动创建并写入 `config.json`，你不需要手动填写这些值。只需先填入 `base_token` 和 `base_url` 即可。

### 运行

```bash
# 1. 确保已认证
lark-cli auth status

# 2. 初始化表格结构和视图（只需运行一次）
python setup_views.py

# 3. 运行主 Demo（6 步端到端流程）
python demo.py

# 4. 运行 Fork 合并演示（独立运行）
python fork_merge.py
```

## Demo 流程

### 步骤 1: 插入示例 Issue
向 Issues 表插入 3 个真实场景的问题：
- 附件发送失败 (lark-mail, Doubao)
- 文档解析超时 (lark-doc, Trae)
- 日历事件重复创建 (lark-calendar, 飞书机器人)

### 步骤 2: AI 兼容性诊断
对每个 Issue 执行：
1. **问题复现** — 在用户报告的环境中模拟相同 Prompt 运行
2. **多环境横测** — 在 Trae / Doubao / 飞书机器人 / 用户 aily 等多环境下跑同一用例
3. **适配定位** — 分析 SKILL.md，定位需要适配的代码段
4. **归因判定** — Skill Bug / 平台兼容 / 配置问题 / 上下文问题 / 使用问题

### 步骤 3: 创建版本记录
为每个 Skill Bug / 平台兼容问题自动创建适配版本记录，关联 Issue ID 和 CHANGELOG。

### 步骤 4: Fork & Diff 演示
创建 Fork 记录，展示上游版本变更和 Diff 摘要。

### 步骤 5: IM 交互卡片通知
将 AI 兼容性诊断报告以 Interactive Card 2.0 发送到开发者飞书，包含：
- 归因统计（Skill Bug / 平台兼容 / 使用问题 / 待确认）
- 每个 Issue 的归因分类、适配建议、修复分支

## Demo Base 链接

> 以下是我们演示用的飞书 Base 链接，你可以替换为你自己的：

```
https://your-domain.feishu.cn/base/YOUR_BASE_TOKEN
```

## 作者

**yveww** — 飞书 AI 绝活大会线上黑客松参赛项目
