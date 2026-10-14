#!/usr/bin/env python3
"""
人工后对比并回复_飞书版.py — 对比人工修正与脚本分类，然后批量回复
================================================================
用法:
  python3 人工后对比并回复_飞书版.py
  python3 人工后对比并回复_飞书版.py --user-id 123
  python3 人工后对比并回复_飞书版.py --user-id 123 --time "2026-05-27 12:34"

输出:
  1. 脚本处理和人工处理的差异、最大差异点、可改进点
  2. 话术回复是否完成
"""

import argparse
import importlib.util
import json
import os
import subprocess
import time
from collections import Counter


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_TOKEN = 'NdifbVZrTaHOJCs0I8Ec9CM8nzd'
TABLE_ID = 'tblwYweAyqS6397A'


def load_module(filename, name):
    path = os.path.join(SCRIPT_DIR, filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lark(*args):
    cmd = ['lark-cli'] + list(args) + ['--as', 'bot', '--format', 'json']
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError('读取飞书 Base 失败')
    return json.loads(result.stdout)


def first_value(value):
    if isinstance(value, list):
        return value[0] if value else ''
    return value or ''


def fetch_all_base_records():
    records = []
    record_ids = []
    field_names = []
    offset = 0

    while True:
        resp = lark('base', '+record-list',
                    '--base-token', BASE_TOKEN,
                    '--table-id', TABLE_ID,
                    '--limit', '200',
                    '--offset', str(offset))
        if not resp.get('ok'):
            raise RuntimeError('读取飞书 Base 失败')

        data = resp['data']
        if not field_names:
            field_names = data['fields']
        records.extend(data['data'])
        record_ids.extend(data['record_id_list'])

        if not data.get('has_more'):
            break
        offset += 200
        time.sleep(0.3)

    return records, record_ids, field_names


def text_field(rec, name_idx, field_name):
    idx = name_idx.get(field_name, -1)
    if idx < 0:
        return ''
    return str(first_value(rec[idx])).strip()


def compare_classification(classify_mod):
    records, _, field_names = fetch_all_base_records()
    name_idx = {n: i for i, n in enumerate(field_names)}
    diffs = []
    pair_counter = Counter()
    type_counter = Counter()
    owner_counter = Counter()

    for rec in records:
        content = text_field(rec, name_idx, '用户反馈原文')
        translation = text_field(rec, name_idx, '用户反馈中文')
        device = text_field(rec, name_idx, '设备类型')
        country = text_field(rec, name_idx, '国家')
        version = text_field(rec, name_idx, '版本号')

        script_pt, script_owner = classify_mod.classify(content, translation, device, country, version)
        final_pt = text_field(rec, name_idx, '问题类型')
        final_owner = text_field(rec, name_idx, '排查负责人')

        if script_pt != final_pt or script_owner != final_owner:
            pair_counter[(script_pt, script_owner, final_pt, final_owner)] += 1
            if script_pt != final_pt:
                type_counter[(script_pt, final_pt)] += 1
            if script_owner != final_owner:
                owner_counter[(script_owner, final_owner)] += 1
            diffs.append({
                'content': content[:120],
                'translation': translation[:120],
                'script': f'{script_pt}/{script_owner}',
                'final': f'{final_pt}/{final_owner}',
            })

    return records, diffs, pair_counter, type_counter, owner_counter


def print_diff_report(total, diffs, pair_counter, type_counter, owner_counter):
    print()
    print('=' * 60)
    print('脚本分类 vs 人工处理差异')
    print('=' * 60)
    print(f'总记录: {total}')
    print(f'差异: {len(diffs)} 条，占比 {(len(diffs) / total * 100 if total else 0):.1f}%')

    if not diffs:
        print('最大差异点: 暂无，脚本分类与当前人工结果一致')
        print('可改进点: 暂无明显方向')
        return

    print()
    print('最大差异点:')
    for (script_pt, script_owner, final_pt, final_owner), count in pair_counter.most_common(5):
        print(f'  - {script_pt}/{script_owner} -> {final_pt}/{final_owner}: {count} 条')

    print()
    print('问题类型差异 Top 5:')
    for (script_pt, final_pt), count in type_counter.most_common(5):
        print(f'  - {script_pt} -> {final_pt}: {count} 条')

    print()
    print('负责人差异 Top 5:')
    for (script_owner, final_owner), count in owner_counter.most_common(5):
        print(f'  - {script_owner} -> {final_owner}: {count} 条')

    top_pair = pair_counter.most_common(1)[0]
    script_pt, script_owner, final_pt, final_owner = top_pair[0]
    print()
    print('可改进点:')
    print(f'  优先看 "{script_pt}/{script_owner} -> {final_pt}/{final_owner}" 这组误差，数量最多，最值得沉淀为新规则。')
    print('  建议从下面样本里挑 10-20 条，补充关键词或调整优先级后再跑本脚本复查。')

    print()
    print('差异样本前 10 条:')
    for item in diffs[:10]:
        shown = item['translation'] or item['content']
        print(f'  - 脚本 {item["script"]} -> 人工 {item["final"]}: {shown}')


def clean_reply_text(text):
    if '\n生成作品' in text:
        text = text[:text.index('\n生成作品')]
    return text.strip()


def run_replies(reply_mod, user_id=None, target_time=None):
    import requests

    pending = reply_mod.fetch_pending_replies()
    if user_id:
        pending = [p for p in pending if user_id in p['user_id']]
        if target_time:
            pending = [p for p in pending if target_time[:16] in p['time'][:16]]
        print(f'筛选用户 {user_id}, 匹配 {len(pending)} 条')

    for item in pending:
        item['reply_text'] = clean_reply_text(item['reply_text'])

    pending = [p for p in pending if p['reply_text']]
    if not pending:
        return Counter({'没有待回复': 0}), 0

    cookies = reply_mod.get_cookies()
    session = requests.Session()
    session.cookies.update(cookies)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Origin': reply_mod.BASE_URL,
        'Referer': f'{reply_mod.BASE_URL}/',
    })

    stats = Counter()
    total = len(pending)

    for i, item in enumerate(pending):
        uid = item['user_id']
        time_match = item['time']
        reply_text = item['reply_text']
        print(f'  [{i+1:3d}/{total:3d}] {uid[:20]:20s} | {item["problem_type"]} | {time_match}', end='')

        report_id = reply_mod.find_report_id(session, uid, time_match)
        if report_id == 'ALREADY_REPLIED':
            print(' -> 已回复跳过')
            stats['已回复跳过'] += 1
            continue
        if not report_id:
            print(' -> 未找到反馈记录')
            stats['未找到'] += 1
            continue

        ok = reply_mod.reply_user(session, report_id, reply_text)
        if ok:
            print(' -> 已回复')
            stats['已回复'] += 1
        else:
            print(' -> 回复失败')
            stats['回复失败'] += 1
        time.sleep(0.5)

    return stats, total


def print_reply_report(stats, total):
    print()
    print('=' * 60)
    print('话术回复结果')
    print('=' * 60)

    if total == 0:
        print('话术回复: 没有待回复记录')
        return

    for key, value in sorted(stats.items(), key=lambda x: -x[1]):
        print(f'{key}: {value}')
    finished = stats.get('已回复', 0) + stats.get('已回复跳过', 0)
    failed = total - finished
    if failed == 0:
        print(f'话术回复: 已完成，{finished}/{total}')
    else:
        print(f'话术回复: 未全部完成，完成 {finished}/{total}，剩余/失败 {failed}')


def run(user_id=None, target_time=None):
    classify_mod = load_module('分类_飞书版.py', 'classify_lark')
    reply_mod = load_module('批量回复_飞书版.py', 'reply_lark')

    records, diffs, pair_counter, type_counter, owner_counter = compare_classification(classify_mod)
    print_diff_report(len(records), diffs, pair_counter, type_counter, owner_counter)

    print()
    print('开始自动回复...')
    stats, total = run_replies(reply_mod, user_id, target_time)
    print_reply_report(stats, total)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='对比人工修正与脚本分类，然后批量回复')
    parser.add_argument('--user-id', help='只回复指定用户ID（不传则回复全部）')
    parser.add_argument('--time', help='配合 --user-id 指定反馈时间（精确到分钟）')
    args = parser.parse_args()

    run(args.user_id, args.time)
