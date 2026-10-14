#!/usr/bin/env python3
"""
人工前处理_飞书版.py — 导入反馈、自动分类、查订阅，并输出人工检查前汇总
====================================================================
用法:
  python3 人工前处理_飞书版.py
  python3 人工前处理_飞书版.py --start 2026-05-20 --end 2026-05-27

输出:
  1. 数据是否导入，时间范围（到秒），多少条
  2. 登错账号/退订/退款分别多少条，占比多少
  3. 需要人工检查处理的多少条，占比多少
  4. 话术是否填充完成
"""

import argparse
import importlib.util
import json
import os
import plistlib
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timedelta


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_TOKEN = 'NdifbVZrTaHOJCs0I8Ec9CM8nzd'
TABLE_ID = 'tblwYweAyqS6397A'
RIGHTS_TYPES = ['登错账号', '退订问题', '退款问题']
LAUNCHD_LABEL = 'com.dreamface.feedback.preprocess'


def load_module(filename, name):
    path = os.path.join(SCRIPT_DIR, filename)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lark(*args, read=True):
    cmd = ['lark-cli'] + list(args) + ['--as', 'bot']
    if read:
        cmd += ['--format', 'json']
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        if read:
            return None
        return {'ok': False, 'error': result.stderr}
    return json.loads(result.stdout)


def pct(part, total):
    if not total:
        return '0.0%'
    return f'{part / total * 100:.1f}%'


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
        if not resp or not resp.get('ok'):
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


def records_by_keys(keys):
    records, record_ids, field_names = fetch_all_base_records()
    name_idx = {n: i for i, n in enumerate(field_names)}
    matched = []

    for rec, rid in zip(records, record_ids):
        uid = str(first_value(rec[name_idx.get('用户信息', -1)])).strip()
        first_time = str(first_value(rec[name_idx.get('首联日期', -1)]))[:16]
        if (uid, first_time) in keys:
            matched.append((rid, rec, name_idx))

    return matched


def text_field(rec, name_idx, field_name):
    idx = name_idx.get(field_name, -1)
    if idx < 0:
        return ''
    return str(first_value(rec[idx])).strip()


def needs_manual_check(rec, name_idx):
    reply = text_field(rec, name_idx, '备注/话术')
    desc = text_field(rec, name_idx, '描述')
    return (not reply) or ('需人工核实' in desc)


def import_feedback(download_mod, start_date, end_date):
    dl_path = download_mod.download_feedback(start_date, end_date)
    records = download_mod.clean_excel(dl_path)

    if not records:
        return [], 0, 0

    existing = download_mod.get_existing_keys()
    new_records = []
    duplicate_count = 0

    for rec in records:
        key = (rec['用户信息'], rec['首联日期'][:16])
        if key in existing:
            duplicate_count += 1
        else:
            new_records.append(rec)

    if new_records:
        download_mod.batch_create_records(new_records)

    return new_records, len(records), duplicate_count


def summarize_imported(new_records):
    if not new_records:
        return set(), '', '', 0

    keys = {(r['用户信息'], r['首联日期'][:16]) for r in new_records}
    times = sorted(str(r.get('首联日期', ''))[:19] for r in new_records if r.get('首联日期'))
    start_time = times[0] if times else ''
    end_time = times[-1] if times else ''
    return keys, start_time, end_time, len(new_records)


def print_summary(new_records, imported_records):
    keys, start_time, end_time, imported_count = summarize_imported(new_records)
    print()
    print('=' * 60)
    print('人工介入前处理结果')
    print('=' * 60)

    if imported_count == 0:
        print('1. 数据导入: 否，本次没有新数据导入')
        print('2. 权益类统计: 无新数据')
        print('3. 需要人工检查处理: 0 条，占比 0.0%')
        print('4. 话术填充: 无新数据')
        return

    pt_counter = Counter()
    manual_count = 0
    reply_count = 0

    for _, rec, name_idx in imported_records:
        pt = text_field(rec, name_idx, '问题类型')
        pt_counter[pt] += 1
        if needs_manual_check(rec, name_idx):
            manual_count += 1
        if text_field(rec, name_idx, '备注/话术'):
            reply_count += 1

    print(f'1. 数据导入: 是，时间范围 {start_time} ~ {end_time}，导入 {imported_count} 条')
    print('2. 权益类统计:')
    for pt in RIGHTS_TYPES:
        count = pt_counter.get(pt, 0)
        print(f'   - {pt}: {count} 条，占比 {pct(count, imported_count)}')
    print(f'3. 需要人工检查处理: {manual_count} 条，占比 {pct(manual_count, imported_count)}')
    if reply_count == imported_count:
        print(f'4. 话术填充: 已全部填充，{reply_count}/{imported_count}')
    else:
        print(f'4. 话术填充: 未全部填充，已填 {reply_count}/{imported_count}，未填 {imported_count - reply_count}')


def launchd_plist_path():
    return os.path.expanduser(f'~/Library/LaunchAgents/{LAUNCHD_LABEL}.plist')


def install_launchd(hour=9, minute=0):
    """Install a macOS launchd job that runs this script every day."""
    script_path = os.path.abspath(__file__)
    launch_agents = os.path.expanduser('~/Library/LaunchAgents')
    log_dir = os.path.expanduser('~/Library/Logs')
    plist_path = launchd_plist_path()
    os.makedirs(launch_agents, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    plist = {
        'Label': LAUNCHD_LABEL,
        'ProgramArguments': [sys.executable, script_path],
        'WorkingDirectory': SCRIPT_DIR,
        'StartCalendarInterval': {'Hour': int(hour), 'Minute': int(minute)},
        'StandardOutPath': os.path.join(log_dir, 'dreamface_feedback_preprocess.out.log'),
        'StandardErrorPath': os.path.join(log_dir, 'dreamface_feedback_preprocess.err.log'),
        'EnvironmentVariables': {
            'PATH': '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin',
        },
    }

    with open(plist_path, 'wb') as f:
        plistlib.dump(plist, f)

    subprocess.run(['launchctl', 'unload', plist_path],
                   capture_output=True, text=True)
    result = subprocess.run(['launchctl', 'load', plist_path],
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f'定时任务配置已写入: {plist_path}')
        print(f'但 launchctl load 失败: {result.stderr.strip()}')
        print('可以重启电脑，或手动执行: launchctl load ~/Library/LaunchAgents/com.dreamface.feedback.preprocess.plist')
        return

    print(f'已安装每天 {int(hour):02d}:{int(minute):02d} 自动运行任务')
    print(f'配置文件: {plist_path}')
    print(f'日志: {os.path.join(log_dir, "dreamface_feedback_preprocess.out.log")}')


def uninstall_launchd():
    plist_path = launchd_plist_path()
    subprocess.run(['launchctl', 'unload', plist_path],
                   capture_output=True, text=True)
    if os.path.exists(plist_path):
        os.remove(plist_path)
        print(f'已删除定时任务: {plist_path}')
    else:
        print('未找到已安装的定时任务')


def run(start_date, end_date):
    download_mod = load_module('下载反馈并导入飞书.py', 'download_feedback_to_lark')
    classify_mod = load_module('分类_飞书版.py', 'classify_lark')
    query_mod = load_module('查订阅_飞书版.py', 'query_subscription_lark')

    print(f'开始导入反馈: {start_date} ~ {end_date}')
    new_records, downloaded_count, duplicate_count = import_feedback(download_mod, start_date, end_date)
    print(f'下载 {downloaded_count} 条，新增 {len(new_records)} 条，重复 {duplicate_count} 条')

    if new_records:
        keys, _, _, _ = summarize_imported(new_records)

        print()
        print('开始自动分类...')
        classify_mod.run()

        print()
        print('开始查订阅并填充话术...')
        query_mod.run()

        imported_records = records_by_keys(keys)
    else:
        imported_records = []

    print_summary(new_records, imported_records)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='导入反馈、分类、查订阅，并输出人工检查前汇总')
    parser.add_argument('--start', help='开始日期 YYYY-MM-DD (默认: 昨天)')
    parser.add_argument('--end', help='结束日期 YYYY-MM-DD (默认: 今天)')
    parser.add_argument('--install-launchd', action='store_true',
                        help='安装 macOS 定时任务：每天自动运行本脚本')
    parser.add_argument('--uninstall-launchd', action='store_true',
                        help='卸载本脚本安装的 macOS 定时任务')
    parser.add_argument('--hour', type=int, default=9,
                        help='配合 --install-launchd 使用，默认 9 点')
    parser.add_argument('--minute', type=int, default=0,
                        help='配合 --install-launchd 使用，默认 0 分')
    args = parser.parse_args()

    if args.install_launchd:
        install_launchd(args.hour, args.minute)
        sys.exit(0)

    if args.uninstall_launchd:
        uninstall_launchd()
        sys.exit(0)

    today = datetime.now()
    yesterday = today - timedelta(days=1)

    run(args.start or yesterday.strftime('%Y-%m-%d'),
        args.end or today.strftime('%Y-%m-%d'))
