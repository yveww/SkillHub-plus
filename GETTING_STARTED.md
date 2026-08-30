# 上手指南

> 以下命令均可直接复制执行，从零到跑通 Demo 约 5 分钟。

## 1. 环境准备

**必需：**

| 依赖 | 版本要求 | 安装方式 |
|------|---------|---------|
| Python | 3.8+ | [python.org](https://python.org) 下载安装 |
| lark-cli | 最新版 | 飞书开放平台工具 |
| 飞书多维表格 | — | 在飞书中新建一个 Base |

**验证环境：**

```bash
python --version     # 应输出 3.8+
lark-cli --version    # 应输出版本号
```

## 2. 安装与认证

**Step 1：下载项目**

```bash
git clone https://github.com/yveww/SkillHub-plus.git
cd SkillHub-plus
```

**Step 2：lark-cli 认证（关键步骤）**

```bash
# 登录飞书账号（会打开浏览器授权）
lark-cli auth login

# 验证认证状态
lark-cli auth status
```

> 认证成功后会显示当前登录的飞书用户信息。如遇权限不足，执行 `lark-cli auth login --domain all` 重新授权。

**Step 3：创建飞书多维表格**

1. 在飞书中新建一个多维表格（Base）
2. 复制 Base URL，形如 `https://your-domain.feishu.cn/base/xxxxxxxx`
3. URL 中 `/base/` 后面的部分就是你的 `base_token`

**Step 4：验证多维表格可访问**

```bash
# 列出当前 Base 的表结构（确认权限正常）
lark-cli base +tables-list --base-token YOUR_BASE_TOKEN --as user --format json
```

> 首次运行会返回空（还没有表），运行 `setup_views.py` 后会自动创建。

## 3. 配置

将 `config.example.json` 复制为 `config.json`，填入你的 Base 信息：

```bash
cp config.example.json config.json
```

编辑 `config.json`，只需手动填写 `base_token` 和 `base_url`：

```json
{
    "base_token": "YOUR_BASE_TOKEN",
    "base_url": "https://your-domain.feishu.cn/base/YOUR_BASE_TOKEN",
    "tables": {
        "issues": "运行 setup_views.py 后自动生成",
        "versions": "运行 setup_views.py 后自动生成",
        "forks": "运行 setup_views.py 后自动生成"
    },
    "views": {
        "issues_default": "运行 setup_views.py 后自动生成",
        "versions_default": "运行 setup_views.py 后自动生成",
        "forks_default": "运行 setup_views.py 后自动生成",
        "issues_kanban": "运行 setup_views.py 后自动生成"
    },
    "forms": {
        "issues_feedback": "运行 setup_views.py 后自动生成"
    }
}
```

> **提示**：`tables`、`views`、`forms` 中的 ID 会在首次运行 `setup_views.py` 时自动创建并写入 `config.json`，你不需要手动填写。

**初始化表结构和视图（只需运行一次）：**

```bash
python setup_views.py
```

预期输出：

```
✓ 看板视图已就绪
✓ 表单问题已验证
  ✓ 表单状态正确：8 个用户问题，无 AI/系统字段泄露
```

## 4. 运行 Demo

**一键运行完整 6 步流程：**

```bash
python demo.py
```

脚本会自动执行：

| 步骤 | 动作 | 预期输出 |
|------|------|---------|
| ① 插入 Issue | 向 Issues 表插入 3 个真实场景问题 | `✓ 已插入 3 个示例 Issue` |
| ② AI 诊断 | 复现 → 多环境横测 → 适配定位 → 归因判定 | `✓ AI 兼容性诊断完成：确认Bug 1 / 非Bug 1 / 待确认 1` |
| ③ 版本记录 | 为确认 Bug 创建修复版本 | `✓ 已创建版本记录 v1.2.1-fix` |
| ④ Fork 演示 | 创建 Fork + 上游 Diff | `✓ Fork 记录已创建` |
| ⑤ IM 通知 | 发送 Interactive Card 到飞书 | `✓ Interactive Card 已发送到飞书` |
| ⑥ 卡片回调 | 模拟开发者点击按钮，状态更新 | `✓ 状态已更新: 确认Bug → 已确认` |

**运行 Fork 合并演示（独立脚本）：**

```bash
python fork_merge.py
```

## 5. 在线查看数据

打开飞书多维表格，即可看到完整 Demo 数据：

| 表 | 内容 | 重点看 |
|----|------|--------|
| Issues | 3 个示例 Issue | AI 判定列、置信度、根因分析 |
| Versions | 1 条修复版本 | CHANGELOG、关联 Issue |
| Forks | 1 条 Fork 记录 | Diff 摘要、合并状态 |

切换到 **看板视图**可按状态分组查看 Issue 流转。

## 6. 演示文稿

浏览器打开 `docs/presentation.html`，10 页深色主题幻灯片：
- 第 5-7 页含**可交互 UI 展示**（点击按钮体验 IM 卡片三态流转、开发者操作卡片、Issue 看板）
- 左右键 / 滚轮翻页

## 7. 测试报告

浏览器打开 `docs/test-report/index.html`，包含各模块验证结果、风险分析矩阵和测试用例分布。

## 8. 常见问题

| 问题 | 解决方案 |
|------|---------|
| `lark-cli: command not found` | 未安装 lark-cli，参考飞书开放平台文档安装 |
| `auth: not logged in` | 执行 `lark-cli auth login` 重新登录 |
| `base: permission denied` | 确认飞书账号有该 Base 的访问权限，或执行 `lark-cli auth login --domain all` |
| `record-batch-create: parse failed` | 检查 config.json 中的 token 和 table_id 是否正确 |
| IM 卡片未收到 | 确认 lark-cli 有 IM 发送权限，且目标用户在应用可见范围内 |
| `FileNotFoundError: [WinError 2]` | Windows 上 lark-cli 是 .cmd 文件，脚本已加 `shell=True` 处理 |
| PowerShell JSON 报错 | 已通过文件引用方式处理，如仍报错请用 cmd 或 Git Bash 运行 |
