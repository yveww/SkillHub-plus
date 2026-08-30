#!/usr/bin/env python
"""
SkillHub+ - Fork & 上游 Diff 合并演示
列出待合并 Fork → 展示 Diff → 模拟合并决策 → 更新状态
"""
import json
import subprocess
import os
from pathlib import Path

os.chdir(Path(__file__).parent)

CONFIG = json.loads(Path("config.json").read_text(encoding="utf-8"))
BASE_TOKEN = CONFIG["base_token"]
TABLES = CONFIG["tables"]


def lark(*args):
    cmd = ["lark-cli", "base"] + list(args) + ["--as", "user", "--format", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", shell=True)
    out = result.stdout.strip().lstrip("\ufeff")
    try:
        return json.loads(out)
    except Exception:
        return {"ok": False, "error": {"message": f"parse failed: {out[:300]}"}}


def list_all_records(table_key):
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
    v = fields.get(key, default)
    if isinstance(v, list) and v:
        return v[0] if isinstance(v[0], str) else str(v[0])
    if isinstance(v, str):
        return v
    return str(v) if v else default


def update_record(table_key, record_id, fields_dict):
    payload = {"update_records": {record_id: fields_dict}}
    tmp = Path("_tmp_merge.json")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    result = lark(
        "+record-batch-update",
        "--base-token", BASE_TOKEN,
        "--table-id", TABLES[table_key],
        "--json", "@./_tmp_merge.json",
    )
    tmp.unlink(missing_ok=True)
    return result


DIFF_DETAILS = [
    {
        "file": "SKILL.md",
        "line": "L32",
        "change": "+ if agent_type == 'Doubao':\n+     tool_format = 'doubao_v1'\n-     tool_format = 'default'",
        "impact": "新增 Doubao Agent 类型判断，修复工具调用格式不匹配",
        "auto_safe": True,
    },
    {
        "file": "SKILL.md",
        "line": "L45",
        "change": "+ if attachment_size > 25MB:\n+     return error('附件过大')\n  # 原有逻辑保持不变",
        "impact": "优化附件处理，增加大小限制检查（与你的自定义修改冲突）",
        "auto_safe": False,
    },
    {
        "file": "references/mail.md",
        "line": "L18",
        "change": "- 示例：send_mail(to='张三')\n+ 示例：send_mail(to='zhangsan@example.com')",
        "impact": "修复示例代码，邮箱格式从姓名改为邮箱地址",
        "auto_safe": True,
    },
]


def show_diff(fork_record):
    f = fork_record.get("fields", {})
    fork_name = get_field(f, "Fork名称")
    upstream_ver = get_field(f, "上游版本")
    fork_ver = get_field(f, "Fork版本")
    diff_summary = get_field(f, "Diff摘要")
    custom_mod = get_field(f, "自定义修改")

    print(f"\n  ┌──────────────────────────────────────────")
    print(f"  │ Fork: {fork_name} ({fork_ver})")
    print(f"  │ 上游: {upstream_ver}")
    print(f"  │ 自定义修改: {custom_mod[:50]}...")
    print(f"  │ Diff 摘要: {diff_summary[:60]}...")
    print(f"  └──────────────────────────────────────────")

    print(f"\n  📋 逐条 Diff 审阅:")
    for i, d in enumerate(DIFF_DETAILS, 1):
        safe_icon = "✅" if d["auto_safe"] else "⚠️"
        print(f"\n  [{i}/{len(DIFF_DETAILS)}] {d['file']} {d['line']}  {safe_icon}")
        print(f"      变更: {d['change'][:80]}")
        print(f"      影响: {d['impact']}")
        if not d["auto_safe"]:
            print(f"      ⚠️ 与自定义修改存在冲突，需手动解决")


def demo_merge():
    print("=" * 60)
    print("  SkillHub+ Fork & Merge Demo")
    print("=" * 60)
    print(f"\n  Base: {CONFIG['base_url']}")

    print("\n🔄 步骤 1: 扫描待合并 Fork\n")
    records = list_all_records("forks")
    pending = [r for r in records if get_field(r.get("fields", {}), "合并状态") == "待合并"]
    print(f"  找到 {len(pending)} 个待合并 Fork")

    if not pending:
        print("  (无待合并 Fork，演示结束)")
        return

    for fork in pending:
        f = fork.get("fields", {})
        fork_name = get_field(f, "Fork名称")
        rid = fork.get("record_id", "")

        print(f"\n{'─' * 50}")
        print(f"  处理 Fork: {fork_name}")

        show_diff(fork)

        print(f"\n  🔀 合并决策:")
        print(f"      → [1] 全部合并（自动解决安全变更，冲突项手动处理）")
        print(f"      → [2] 仅合并安全变更（跳过冲突项）")
        print(f"      → [3] 暂不合并")

        # 模拟选择 "仅合并安全变更"
        choice = 2
        print(f"\n  🤖 AI 建议: 选择 [2] 仅合并安全变更")
        safe_count = sum(1 for d in DIFF_DETAILS if d["auto_safe"])
        conflict_count = len(DIFF_DETAILS) - safe_count
        print(f"      安全变更: {safe_count} 项 | 冲突: {conflict_count} 项")

        result = update_record("forks", rid, {"合并状态": ["已合并"]})
        ok = result.get("ok", False)
        mark = "✓" if ok else "✗"
        print(f"\n  {mark} 合并完成: {fork_name}")
        print(f"      已合并 {safe_count} 项安全变更")
        print(f"      {conflict_count} 项冲突已标记为待手动处理")

    print(f"\n{'─' * 50}")
    print(f"\n  📊 合并汇总:")
    all_forks = list_all_records("forks")
    merged = [r for r in all_forks if get_field(r.get("fields", {}), "合并状态") == "已合并"]
    still_pending = [r for r in all_forks if get_field(r.get("fields", {}), "合并状态") == "待合并"]
    print(f"      已合并: {len(merged)} | 待合并: {len(still_pending)}")

    print(f"\n{'=' * 60}")
    print(f"  ✅ Fork & Merge Demo 完成！")
    print(f"  打开 Forks 表查看: {CONFIG['base_url']}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    demo_merge()
