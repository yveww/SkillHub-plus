#!/usr/bin/env python
"""
SkillHub+ Demo - AI Skill Issue Triage & Fork Management
从飞书多维表格读取 Issue → AI 分流 → 更新状态 → 模拟通知
"""
import json
import subprocess
import random
import time
import os
import sys
from pathlib import Path

os.chdir(Path(__file__).parent)

CONFIG = json.loads(Path("config.json").read_text(encoding="utf-8"))
BASE_TOKEN = CONFIG["base_token"]
TABLES = CONFIG["tables"]


def lark(*args):
    """执行 lark-cli base 命令，返回解析后的 JSON。"""
    cmd = ["lark-cli", "base"] + list(args) + ["--as", "user", "--format", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", shell=True)
    out = result.stdout.strip().lstrip("\ufeff")
    if not out:
        out = result.stderr.strip().lstrip("\ufeff")
    try:
        return json.loads(out)
    except Exception:
        return {"ok": False, "error": {"message": f"parse failed: {out[:300]}"}}


def create_record(table_key, fields_dict):
    """用 +record-batch-create 创建单条记录。"""
    payload = {"create_records": [fields_dict]}
    tmp = Path("_tmp_record.json")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    result = lark(
        "+record-batch-create",
        "--base-token", BASE_TOKEN,
        "--table-id", TABLES[table_key],
        "--json", "@./_tmp_record.json",
    )
    tmp.unlink(missing_ok=True)
    return result


def update_record(table_key, record_id, fields_dict):
    """用 +record-batch-update 更新单条记录。"""
    payload = {"update_records": {record_id: fields_dict}}
    tmp = Path("_tmp_update.json")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    result = lark(
        "+record-batch-update",
        "--base-token", BASE_TOKEN,
        "--table-id", TABLES[table_key],
        "--json", "@./_tmp_update.json",
    )
    tmp.unlink(missing_ok=True)
    return result


def list_all_records(table_key):
    """列出表中所有记录，返回 [{record_id, fields}, ...] 格式。"""
    result = lark(
        "+record-list",
        "--base-token", BASE_TOKEN,
        "--table-id", TABLES[table_key],
        "--page-size", "100",
    )
    if not result.get("ok"):
        return []
    data = result.get("data", {})
    rows = data.get("data", [])
    field_names = data.get("fields", [])
    record_ids = data.get("record_id_list", [])

    records = []
    for i, row in enumerate(rows):
        fields = {}
        for j, val in enumerate(row):
            if j < len(field_names):
                fields[field_names[j]] = val
        rid = record_ids[i] if i < len(record_ids) else ""
        records.append({"record_id": rid, "fields": fields})
    return records


def get_field(fields, key, default=""):
    """从 fields 中提取值，处理 list 包裹。"""
    v = fields.get(key, default)
    if isinstance(v, list) and v:
        return v[0] if isinstance(v[0], str) else str(v[0])
    if isinstance(v, str):
        return v
    return str(v) if v else default


def extract_created_id(result):
    """从 batch-create 响应中提取 record_id。"""
    data = result.get("data", {})
    ids = data.get("record_id_list", [])
    if ids and isinstance(ids, list):
        return ids[0]
    return "?"


# ============================================================
# 步骤 1: 插入示例 Issue
# ============================================================
def insert_sample_issues():
    print("\n📋 步骤 1: 插入示例 Issue\n")
    samples = [
        {
            "标题": "附件发送失败",
            "Skill名称": "lark-mail",
            "Skill版本": "v1.2.0",
            "报告人": "张三",
            "Agent类型": ["Doubao"],
            "Prompt摘要": "发送带附件邮件给张三",
            "问题描述": "附件显示发送成功，但收件人实际未收到",
            "严重程度": ["严重"],
            "状态": ["待分流"],
        },
        {
            "标题": "文档解析超时",
            "Skill名称": "lark-doc",
            "Skill版本": "v1.0.5",
            "报告人": "李四",
            "Agent类型": ["Trae"],
            "Prompt摘要": "读取一篇 100 页文档并总结",
            "问题描述": "解析到 50 页时超时，但文档未损坏",
            "严重程度": ["一般"],
            "状态": ["待分流"],
        },
        {
            "标题": "日历事件重复创建",
            "Skill名称": "lark-calendar",
            "Skill版本": "v2.0.1",
            "报告人": "王五",
            "Agent类型": ["飞书机器人"],
            "Prompt摘要": "创建下周站会日程",
            "问题描述": "同一日程被创建了两次，删除一次后另一次也消失",
            "严重程度": ["一般"],
            "状态": ["待分流"],
        },
    ]
    for s in samples:
        r = create_record("issues", s)
        ok = r.get("ok", False)
        rid = extract_created_id(r) if ok else "?"
        mark = "✓" if ok else "✗"
        print(f"  {mark} {s['标题']}  ({rid})")
        if not ok:
            print(f"      error: {r.get('error', {}).get('message', '')[:120]}")
    print(f"\n  共插入 {len(samples)} 个 Issue")


# ============================================================
# 步骤 2: AI 智能分流
# ============================================================
def ai_triage(issue):
    """模拟 AI 分流：复现 → 多 Agent 对比 → 根因定位 → 判定。"""
    fields = issue.get("fields", {})
    agent = get_field(fields, "Agent类型", "Trae")
    skill = get_field(fields, "Skill名称", "unknown")

    dice = random.random()
    all_agents = ["Trae", "Doubao", "飞书机器人"]

    if dice < 0.55:
        repro = "已复现"
        agent_map = {a: ("复现" if a == agent else "正常") for a in all_agents}
        compare = " / ".join(f"{a}: {r}" for a, r in agent_map.items())
        roots = [
            f"SKILL.md L32 缺少 {agent} Agent 类型判断，工具调用格式不匹配",
            f"references/usage.md 示例代码未覆盖 {agent} 调用路径",
            f"SKILL.md L45 条件分支不完整，{agent} 下未触发",
        ]
        root = random.choice(roots)
        verdict = "确认Bug"
        conf = random.randint(82, 95)
        status = "确认Bug"
        branch = f"fix/{skill.lower()}-{random.randint(100,999)}"
    elif dice < 0.85:
        repro = "未复现"
        agent_map = {a: "正常" for a in all_agents}
        compare = " / ".join(f"{a}: 正常" for a in all_agents)
        root = "用户 Prompt 缺少必要参数，Skill 正确返回了错误提示。标准 Prompt 下功能正常。"
        verdict = "非Bug"
        conf = random.randint(85, 95)
        status = "非Bug"
        branch = ""
    else:
        repro = "间歇复现"
        agent_map = {a: random.choice(["正常", "复现"]) for a in all_agents}
        compare = " / ".join(f"{a}: {r}" for a, r in agent_map.items())
        root = "相同条件复现 3 次，2 次成功 1 次失败，疑似 Agent 版本差异导致间歇性触发"
        verdict = "待确认"
        conf = random.randint(45, 65)
        status = "待确认"
        branch = ""

    return {
        "状态": [status],
        "AI判定": [verdict],
        "AI置信度": conf,
        "AI根因分析": root,
        "复现结果": [repro],
        "多Agent对比": compare,
        "修复分支": branch,
    }


def run_triage():
    print("\n🔍 步骤 2: AI 智能分流\n")
    records = list_all_records("issues")
    pending = [r for r in records if get_field(r.get("fields", {}), "状态") == "待分流"]
    print(f"  找到 {len(pending)} 个待分流 Issue")

    for issue in pending:
        rid = issue.get("record_id", "")
        f = issue.get("fields", {})
        title = get_field(f, "标题")
        agent = get_field(f, "Agent类型")
        desc = get_field(f, "问题描述")

        print(f"\n  ┌─ {title}")
        print(f"  │  Agent: {agent}")
        print(f"  │  描述: {desc}")
        print(f"  │  → 复现测试中...", end="", flush=True)
        time.sleep(0.5)
        print(" ✓", end="")
        time.sleep(0.3)
        print(" → 多 Agent 对比中...", end="", flush=True)
        time.sleep(0.5)
        print(" ✓", end="")
        time.sleep(0.3)
        print(" → 根因定位中...", end="", flush=True)
        time.sleep(0.5)
        print(" ✓")

        result = ai_triage(issue)
        r = update_record("issues", rid, result)
        ok = r.get("ok", False)

        if ok:
            v = result["AI判定"][0]
            c = result["AI置信度"]
            mark = "🐛" if v == "确认Bug" else ("ℹ️" if v == "非Bug" else "❓")
            print(f"  └─ {mark} 判定: {v} (置信度 {c}%)")
            if result.get("修复分支"):
                print(f"      修复分支: {result['修复分支']}")
        else:
            print(f"  └─ ✗ 更新失败: {r.get('error', {})}")

    print(f"\n  分流完成，共处理 {len(pending)} 个 Issue")


# ============================================================
# 步骤 3: 创建版本记录（确认 Bug 的修复版本）
# ============================================================
def create_version_records():
    print("\n📦 步骤 3: 为确认 Bug 创建版本记录\n")
    records = list_all_records("issues")
    bugs = [r for r in records if get_field(r.get("fields", {}), "AI判定") == "确认Bug"]
    if not bugs:
        print("  (无确认 Bug，跳过版本创建)")
        return
    for bug in bugs:
        f = bug.get("fields", {})
        skill = get_field(f, "Skill名称")
        branch = get_field(f, "修复分支")
        issue_id_raw = f.get("Issue ID", "")
        if isinstance(issue_id_raw, list) and issue_id_raw:
            issue_id = issue_id_raw[0] if isinstance(issue_id_raw[0], str) else str(issue_id_raw[0])
        elif isinstance(issue_id_raw, str):
            issue_id = issue_id_raw
        else:
            issue_id = str(issue_id_raw) if issue_id_raw else "ISSUE-?"

        version_fields = {
            "版本号": "v1.2.1-fix",
            "Skill名称": skill,
            "状态": ["已发布"],
            "CHANGELOG": f"修复 {issue_id}: {get_field(f, 'AI根因分析')[:60]}...",
            "修复Issue": issue_id,
        }
        r = create_record("versions", version_fields)
        ok = r.get("ok", False)
        mark = "✓" if ok else "✗"
        print(f"  {mark} {skill} v1.2.1-fix  (修复 {issue_id})")
        if not ok:
            print(f"      error: {r.get('error', {}).get('message', '')[:120]}")


# ============================================================
# 步骤 4: Fork & 上游 Diff 演示
# ============================================================
def demo_fork():
    print("\n🔄 步骤 4: Fork & 上游 Diff 演示\n")
    fork_fields = {
        "Fork名称": "lark-mail-custom",
        "原版Skill": "lark-mail",
        "原版版本": "v1.2.0",
        "Fork版本": "v1.2.0-custom",
        "自定义修改": "增加附件大小限制检查，修改 L47 附件处理逻辑",
        "上游版本": "v1.2.1",
        "Diff摘要": "上游 3 处变更: L32 新增 Agent 类型判断 / L45 优化附件处理 / references/mail.md L18 修复示例代码",
        "合并状态": ["待合并"],
    }
    r = create_record("forks", fork_fields)
    ok = r.get("ok", False)
    mark = "✓" if ok else "✗"
    print(f"  {mark} Fork 创建: lark-mail-custom (基于 lark-mail v1.2.0)")
    if ok:
        print(f"      上游已更新到 v1.2.1，检测到 3 处变更")
        print(f"      → 暂不合并 / 逐条审阅 / 全部合并")
    else:
        print(f"      error: {r.get('error', {}).get('message', '')[:120]}")


# ============================================================
# 步骤 5: IM 卡片通知开发者
# ============================================================
def get_my_open_id():
    """获取当前用户的 open_id。"""
    result = subprocess.run(
        ["lark-cli", "auth", "status"],
        capture_output=True, text=True, encoding="utf-8", shell=True,
    )
    out = result.stdout.strip().lstrip("\ufeff")
    if not out:
        out = result.stderr.strip().lstrip("\ufeff")
    try:
        data = json.loads(out)
        return data.get("identities", {}).get("user", {}).get("openId", "")
    except Exception:
        return ""


def build_interactive_card(triage_summary):
    """构建飞书 Interactive Card JSON，含分流结果和操作按钮。"""
    confirmed = triage_summary["confirmed"]
    template = "red" if confirmed > 0 else "green"

    elements = [
        {
            "tag": "markdown",
            "content": (
                f"**分流统计**  \n"
                f"确认 Bug: **{triage_summary['confirmed']}** | "
                f"非 Bug: **{triage_summary['not_bug']}** | "
                f"待确认: **{triage_summary['pending']}**  \n"
                f"共处理 **{triage_summary['total']}** 个 Issue"
            ),
        },
        {"tag": "hr"},
    ]

    for item in triage_summary["items"]:
        icon = {"确认Bug": "🐛", "非Bug": "ℹ️", "待确认": "❓"}.get(item["verdict"], "")
        lines = [
            f"{icon} **{item['title']}**",
            f"Skill: {item['skill']} | Agent: {item['agent']}",
            f"判定: **{item['verdict']}** (置信度 {item['confidence']}%)",
        ]
        if item.get("branch"):
            lines.append(f"修复分支: `{item['branch']}`")
        if item.get("root"):
            lines.append(f"根因: {item['root'][:80]}")
        elements.append({"tag": "markdown", "content": "  \n".join(lines)})

        if item["verdict"] == "确认Bug":
            issue_id = item.get("issue_id", "")
            elements.append({
                "tag": "column_set",
                "flex_mode": "none",
                "columns": [
                    {
                        "tag": "column",
                        "width": "weighted",
                        "weight": 1,
                        "elements": [{
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "确认 Bug"},
                            "type": "primary_filled",
                            "behaviors": [{"type": "callback", "value": {"action": "confirm_bug", "issue_id": issue_id}}],
                        }],
                    },
                    {
                        "tag": "column",
                        "width": "weighted",
                        "weight": 1,
                        "elements": [{
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "标记误报"},
                            "type": "danger",
                            "behaviors": [{"type": "callback", "value": {"action": "reject_bug", "issue_id": issue_id}}],
                        }],
                    },
                    {
                        "tag": "column",
                        "width": "weighted",
                        "weight": 1,
                        "elements": [{
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "转人工"},
                            "type": "default",
                            "behaviors": [{"type": "callback", "value": {"action": "escalate", "issue_id": issue_id}}],
                        }],
                    },
                ],
            })

        elements.append({"tag": "hr"})

    elements.append({
        "tag": "markdown",
        "content": f"[查看完整看板]({CONFIG['base_url']})  \nSkillHub+ · AI Skill Issue Triage"
    })

    card = {
        "schema": "2.0",
        "config": {"update_multi": True, "width_mode": "default"},
        "header": {
            "title": {"tag": "plain_text", "content": "SkillHub+ AI 分流报告"},
            "subtitle": {"tag": "plain_text", "content": f"确认Bug {confirmed} | 非Bug {triage_summary['not_bug']} | 待确认 {triage_summary['pending']}"},
            "template": template,
        },
        "body": {
            "direction": "vertical",
            "padding": "12px 12px 20px 12px",
            "elements": elements,
        },
    }
    return card


def send_im_notification(open_id, triage_summary):
    """发送 Interactive Card 到开发者飞书，含操作按钮。"""
    card = build_interactive_card(triage_summary)
    card_json = json.dumps(card, ensure_ascii=False)

    cmd = [
        "lark-cli", "im", "+messages-send",
        "--user-id", open_id,
        "--msg-type", "interactive",
        "--content", card_json,
        "--as", "bot", "--format", "json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", shell=True)
    out = result.stdout.strip().lstrip("\ufeff")
    if not out:
        out = result.stderr.strip().lstrip("\ufeff")
    try:
        r = json.loads(out)
        if not r.get("ok"):
            print(f"    error: {r.get('error', {}).get('message', '')[:150]}")
        return r.get("ok", False)
    except Exception:
        print(f"    parse failed: {out[:200]}")
        return False


def notify_developers():
    print("\n📨 步骤 5: IM 卡片通知开发者\n")
    records = list_all_records("issues")
    triaged = [r for r in records if get_field(r.get("fields", {}), "AI判定") in ("确认Bug", "非Bug", "待确认")]
    if not triaged:
        print("  (无已分流的 Issue，跳过通知)")
        return

    summary = {"total": len(triaged), "confirmed": 0, "not_bug": 0, "pending": 0, "items": []}
    for r in triaged:
        f = r.get("fields", {})
        verdict = get_field(f, "AI判定")
        if verdict == "确认Bug":
            summary["confirmed"] += 1
        elif verdict == "非Bug":
            summary["not_bug"] += 1
        else:
            summary["pending"] += 1
        summary["items"].append({
            "title": get_field(f, "标题"),
            "skill": get_field(f, "Skill名称"),
            "agent": get_field(f, "Agent类型"),
            "verdict": verdict,
            "confidence": get_field(f, "AI置信度", "0"),
            "branch": get_field(f, "修复分支"),
            "root": get_field(f, "AI根因分析"),
            "issue_id": get_field(f, "Issue ID"),
        })

    print(f"  准备通知: {summary['total']} 个 Issue 分流结果")
    print(f"    🐛 确认Bug {summary['confirmed']} | ℹ️ 非Bug {summary['not_bug']} | ❓ 待确认 {summary['pending']}")

    open_id = get_my_open_id()
    if not open_id:
        print("  ✗ 无法获取用户 open_id，跳过 IM 通知")
        return

    ok = send_im_notification(open_id, summary)
    if ok:
        print(f"  ✓ Interactive Card 已发送到飞书（含操作按钮）")
        simulate_card_callback(summary["items"])
    else:
        print(f"  ✗ IM 发送失败")


def simulate_card_callback(items):
    """模拟开发者在 IM 卡片上点击操作按钮后的回调处理。

    实际场景中，飞书会向已注册的回调 URL 推送 card.action.trigger 事件，
    服务端接收后执行对应操作。Demo 中用 Python 直接模拟这个过程。
    """
    print("\n🎮 步骤 6: 模拟卡片交互回调\n")
    confirmed_items = [it for it in items if it["verdict"] == "确认Bug"]
    if not confirmed_items:
        print("  (无确认 Bug 的 Issue，跳过回调演示)")
        return

    target = confirmed_items[0]
    issue_id = target.get("issue_id", "")
    title = target.get("title", "")
    branch = target.get("branch", "")

    print(f"  ┌─ 模拟开发者点击「确认 Bug」按钮")
    print(f"  │  Issue: {title}")
    print(f"  │  Issue ID: {issue_id}")
    print(f"  │  修复分支: {branch}")
    print(f"  │")
    print(f"  │  回调数据: {{\"action\": \"confirm_bug\", \"issue_id\": \"{issue_id}\"}}")
    print(f"  │")

    records = list_all_records("issues")
    rid = None
    for r in records:
        if get_field(r.get("fields", {}), "Issue ID") == issue_id:
            rid = r.get("record_id")
            break

    if rid:
        r = update_record("issues", rid, {"状态": ["已确认"]})
        if r.get("ok"):
            print(f"  └─ ✓ 状态已更新: 确认Bug → 已确认（看板同步刷新）")
        else:
            print(f"  └─ ✗ 更新失败: {r.get('error', {}).get('message', '')[:120]}")
    else:
        print(f"  └─ ✗ 未找到 Issue ID {issue_id} 对应的记录")

    print(f"\n  💡 实际部署时：")
    print(f"     1. 飞书推送 card.action.trigger 事件到回调 URL")
    print(f"     2. 服务端解析 action 类型（confirm_bug / reject_bug / escalate）")
    print(f"     3. 执行对应操作：更新 Issue 状态、通知报告人、创建修复任务等")
    print(f"     4. 返回新卡片 JSON 实现卡片刷新")


# ============================================================
# 主流程
# ============================================================
def main():
    print("=" * 60)
    print("  SkillHub+ Demo")
    print("  AI Skill Issue Triage & Fork Management")
    print("=" * 60)
    print(f"\n  Base: {CONFIG['base_url']}")

    insert_sample_issues()
    run_triage()
    create_version_records()
    demo_fork()
    notify_developers()

    print("\n" + "=" * 60)
    print("  ✅ Demo 完成！")
    print(f"  打开 Base 查看结果: {CONFIG['base_url']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
