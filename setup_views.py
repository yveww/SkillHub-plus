#!/usr/bin/env python
"""
SkillHub+ - 配置看板视图、表单问题、视图字段
"""
import json
import subprocess
import os
from pathlib import Path

os.chdir(Path(__file__).parent)

CONFIG = json.loads(Path("config.json").read_text(encoding="utf-8"))
BASE_TOKEN = CONFIG["base_token"]
TABLES = CONFIG["tables"]
ISSUES_TABLE = TABLES["issues"]
KANBAN_VIEW = "vewMtrSVvy"
FORM_ID = "vewf9zgFg0"


def lark(*args, file_payload=None, file_param=None):
    """执行 lark-cli base 命令，用临时文件避免编码问题。"""
    cmd = ["lark-cli", "base"] + list(args) + ["--as", "user", "--format", "json"]
    if file_payload is not None and file_param:
        tmp = Path("_tmp_setup.json")
        tmp.write_text(json.dumps(file_payload, ensure_ascii=False), encoding="utf-8")
        cmd = ["lark-cli", "base"] + list(args) + [file_param, "@./_tmp_setup.json", "--as", "user", "--format", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        tmp.unlink(missing_ok=True)
    else:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    out = result.stdout.strip().lstrip("\ufeff")
    try:
        return json.loads(out)
    except Exception:
        return {"ok": False, "error": {"message": f"parse failed: {out[:300]}"}}


def verify_form_state():
    """验证表单当前状态：仅含用户可见问题，AI/系统字段不在表单中。

    安全说明：
    - 不使用 form-questions-delete（会连带删除底层表字段，导致数据丢失）
    - AI/系统字段（状态、AI判定、AI置信度等）不在表单中 = 正确状态
    - 用户通过表单提交时，这些字段由 AI 分流脚本自动填充
    """
    print("\n📋 验证表单问题状态...")
    result = lark(
        "+form-questions-list",
        "--base-token", BASE_TOKEN,
        "--table-id", ISSUES_TABLE,
        "--form-id", FORM_ID,
    )
    if not result.get("ok"):
        print("  ✗ 无法获取表单问题列表")
        return
    questions = result.get("data", {}).get("questions", [])
    user_titles = {"标题", "Skill名称", "Skill版本", "报告人", "Agent类型", "Prompt摘要", "问题描述", "严重程度"}
    ai_titles = {"状态", "AI判定", "AI置信度", "AI根因分析", "复现结果", "多Agent对比", "修复分支"}

    current_titles = {q.get("title", "") for q in questions}
    missing_user = user_titles - current_titles
    leaked_ai = ai_titles & current_titles

    if not missing_user and not leaked_ai:
        print(f"  ✓ 表单状态正确：{len(questions)} 个用户问题，无 AI/系统字段泄露")
    else:
        if missing_user:
            print(f"  ⚠️  缺少用户问题: {missing_user}")
        if leaked_ai:
            print(f"  ⚠️  AI/系统字段仍在表单中: {leaked_ai}")
            print("      建议：在飞书表单设计器中手动隐藏这些字段")
            print("      切勿使用 form-questions-delete（会删除底层表字段）")


def update_form_questions():
    """更新用户可见的表单问题，设置描述和必填。"""
    print("\n📝 更新表单问题描述和必填...")
    updates = [
        {"id": "fldh6A6aFC", "title": "标题", "description": "请简要描述遇到的问题（一句话）", "required": True},
        {"id": "fldr3hK6JZ", "title": "Skill名称", "description": "出问题的 Skill 名称，如 lark-mail、lark-doc", "required": True},
        {"id": "fld99jExXT", "title": "Skill版本", "description": "Skill 版本号，如 v1.2.0（不确定可留空）", "required": False},
        {"id": "fldnUpUiKI", "title": "报告人", "description": "你的姓名或飞书昵称", "required": True},
        {"id": "fldJWBQ7oV", "title": "Agent类型", "description": "你调用 Skill 时使用的 AI Agent", "required": True},
        {"id": "fldJ0iiQXq", "title": "Prompt摘要", "description": "你输入的 Prompt 摘要（帮助 AI 复现问题）", "required": False},
        {"id": "fldOWI1blK", "title": "问题描述", "description": "详细描述：复现步骤、预期行为、实际行为", "required": True},
        {"id": "fldKb3TrJs", "title": "严重程度", "description": "问题对你的影响程度", "required": True},
    ]
    payload = json.dumps(updates, ensure_ascii=False)
    cmd = [
        "lark-cli", "base", "+form-questions-update",
        "--base-token", BASE_TOKEN,
        "--table-id", ISSUES_TABLE,
        "--form-id", FORM_ID,
        "--questions", payload,
        "--as", "user", "--format", "json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    out = result.stdout.strip().lstrip("\ufeff")
    if not out:
        out = result.stderr.strip().lstrip("\ufeff")
    try:
        r = json.loads(out)
        ok = r.get("ok", False)
        print(f"  {'✓' if ok else '✗'} 更新 {len(updates)} 个表单问题")
        if not ok:
            print(f"    {r.get('error', {}).get('message', '')[:150]}")
    except Exception:
        print(f"  ✗ 解析失败: {out[:200]}")


def set_kanban_visible_fields():
    """设置看板视图可见字段。"""
    print("\n👁️  设置看板视图可见字段...")
    visible = {
        "visible_fields": [
            "Issue ID",
            "标题",
            "Skill名称",
            "Skill版本",
            "Agent类型",
            "严重程度",
            "状态",
            "AI判定",
            "AI置信度",
            "修复分支",
        ]
    }
    result = lark(
        "+view-set-visible-fields",
        "--base-token", BASE_TOKEN,
        "--table-id", ISSUES_TABLE,
        "--view-id", KANBAN_VIEW,
        file_payload=visible,
        file_param="--json",
    )
    ok = result.get("ok", False)
    print(f"  {'✓' if ok else '✗'} 看板可见字段设置")
    if not ok:
        print(f"    {result.get('error', {}).get('message', '')[:150]}")


def set_kanban_sort():
    """设置看板视图排序：按创建时间降序。"""
    print("\n🔄 设置看板视图排序...")
    sort_config = {"sort_config": [{"field": "创建时间", "desc": True}]}
    result = lark(
        "+view-set-sort",
        "--base-token", BASE_TOKEN,
        "--table-id", ISSUES_TABLE,
        "--view-id", KANBAN_VIEW,
        file_payload=sort_config,
        file_param="--json",
    )
    ok = result.get("ok", False)
    print(f"  {'✓' if ok else '✗'} 看板排序设置")
    if not ok:
        print(f"    {result.get('error', {}).get('message', '')[:150]}")


def update_config():
    """更新 config.json 加入视图和表单 ID。"""
    print("\n💾 更新 config.json...")
    CONFIG["views"]["issues_kanban"] = KANBAN_VIEW
    CONFIG["forms"] = {"issues_feedback": FORM_ID}
    Path("config.json").write_text(json.dumps(CONFIG, ensure_ascii=False, indent=4), encoding="utf-8")
    print("  ✓ config.json 已更新（看板视图 ID + 表单 ID）")


def main():
    print("=" * 60)
    print("  SkillHub+ 视图与表单配置")
    print("=" * 60)

    verify_form_state()
    update_form_questions()
    set_kanban_visible_fields()
    set_kanban_sort()
    update_config()

    print("\n" + "=" * 60)
    print("  ✅ 配置完成！")
    print(f"  看板视图: {KANBAN_VIEW}")
    print(f"  反馈表单: {FORM_ID}")
    print(f"  Base: {CONFIG['base_url']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
