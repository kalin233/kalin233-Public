#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NADS 九件交付系统 - 交付物自检脚本
用法：python nads_check.py <交付目录>
自动检查：文件名编号、后缀纯净、版本号、整合包顺序等
"""
import os, sys, re, zipfile

def check_dir(d):
    files = sorted(os.listdir(d))
    errors, warns, oks = [], [], []

    # 1. 必须以「编号. 」开头
    numbered = [f for f in files if re.match(r'^\d+\.\s', f)]
    unnumbered = [f for f in files if not f.startswith('.') and not re.match(r'^\d+\.\s', f)]
    if unnumbered:
        errors.append(f"未编号文件: {unnumbered}")
    else:
        oks.append(f"编号完整: {len(numbered)} 个文件均以「编号. 」开头")

    # 2. 后缀后不加内容（.zip/.html 后不能有括号等）
    bad_ext = [f for f in files if re.search(r'\.(zip|html|exe|apk|rar)\s*[（(【]', f, re.I)]
    if bad_ext:
        errors.append(f"后缀后有多余内容: {bad_ext}")
    else:
        oks.append("后缀纯净：无括号/说明文字")

    # 3. 整合包必须是最后一个编号
    nums = sorted([int(re.match(r'^(\d+)\.', f).group(1)) for f in numbered if re.match(r'^(\d+)\.', f)])
    if nums:
        last = nums[-1]
        integ = [f for f in numbered if '整合包' in f]
        if integ:
            integ_num = int(re.match(r'^(\d+)\.', integ[0]).group(1))
            if integ_num != last:
                errors.append(f"整合包编号 {integ_num} ≠ 最后编号 {last}")
            else:
                oks.append(f"整合包编号正确：{integ_num}（=交付物总数）")
        else:
            warns.append("未找到整合包")

    # 4. 整合包内文件顺序
    zips = [f for f in numbered if f.endswith('.zip') and '整合包' in f]
    for z in zips:
        try:
            with zipfile.ZipFile(os.path.join(d, z)) as zf:
                names = zf.namelist()
                seq = [int(re.match(r'^(\d+)\.', n).group(1)) for n in names if re.match(r'^(\d+)\.', n)]
                if seq != sorted(seq):
                    errors.append(f"整合包 {z} 内文件未按编号排序")
                else:
                    oks.append(f"整合包 {z} 内文件顺序正确")
        except Exception as e:
            warns.append(f"无法读取 {z}: {e}")

    # 5. 含版本号的交付物必须带版本号
    need_ver = [f for f in numbered if any(k in f for k in ['总纲', '版本历史', '变更登记表', '交付书'])]
    no_ver = [f for f in need_ver if not re.search(r'v\d+\.\d+', f, re.I)]
    if no_ver:
        warns.append(f"以下文件未带版本号: {no_ver}")

    return errors, warns, oks

if __name__ == '__main__':
    d = sys.argv[1] if len(sys.argv) > 1 else '.'
    print(f"=== NADS 自检: {d} ===")
    e, w, o = check_dir(d)
    for x in o: print(f"  ✅ {x}")
    for x in w: print(f"  ⚠️  {x}")
    for x in e: print(f"  ❌ {x}")
    print(f"\n结果: {len(o)} 通过 / {len(w)} 警告 / {len(e)} 错误")
    sys.exit(1 if e else 0)