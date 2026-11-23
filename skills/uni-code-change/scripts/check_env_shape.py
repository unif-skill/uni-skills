#!/usr/bin/env python3
"""只读比较完整 .env 配置的变量与布局；不解析、打印或修改配置值。"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

ASSIGNMENT = re.compile(r'^(\s*(?:export\s+)?)([A-Za-z_][A-Za-z0-9_]*)(\s*=\s*)(.*)$')


def quoted_end(text, quote):
    escaped = False
    for index, char in enumerate(text):
        if escaped:
            escaped = False
        elif char == '\\':
            escaped = True
        elif char == quote:
            return index
    return None


def read_shape(path):
    keys, layout, quote = [], [], None
    for number, line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        if quote is not None:
            end = quoted_end(line, quote)
            if end is not None:
                tail = line[end + 1:].strip()
                if tail and not tail.startswith('#'):
                    raise ValueError(f'{path.name}:{number}: 引号后存在非注释内容')
                quote = None
            continue
        if not line.strip():
            layout.append(('blank',))
        elif line.lstrip().startswith('#'):
            layout.append(('comment', line))
        else:
            match = ASSIGNMENT.match(line)
            if match is None:
                raise ValueError(f'{path.name}:{number}: 无法识别配置行')
            prefix, key, separator, value = match.groups()
            keys.append(key)
            layout.append(('key', prefix, key, separator))
            if value.startswith(('"', "'")):
                end = quoted_end(value[1:], value[0])
                if end is None:
                    quote = value[0]
                else:
                    tail = value[end + 2:].strip()
                    if tail and not tail.startswith('#'):
                        raise ValueError(f'{path.name}:{number}: 引号后存在非注释内容')
    if quote is not None:
        raise ValueError(f'{path.name}: 多行值的引号未闭合')
    duplicates = sorted(key for key, count in Counter(keys).items() if count > 1)
    return keys, layout, duplicates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('template', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--layout-from', type=Path, help='已确认的环境配置，用于比较分组注释、空行和赋值排版')
    args = parser.parse_args()
    try:
        expected, _, template_duplicates = read_shape(args.template)
        actual, layout, duplicates = read_shape(args.candidate)
        if template_duplicates:
            raise ValueError('模板包含重复变量，应先修正模板')
        layout_matches = None
        if args.layout_from:
            reference, expected_layout, reference_duplicates = read_shape(args.layout_from)
            if reference_duplicates or reference != expected:
                raise ValueError('布局参照的变量或顺序与模板不一致')
            layout_matches = layout == expected_layout
        result = {
            'missing': [key for key in expected if key not in actual],
            'extra': [key for key in actual if key not in expected],
            'duplicates': duplicates,
            'order_matches': actual == expected,
            'layout_matches': layout_matches,
        }
        result['ok'] = not (result['missing'] or result['extra'] or duplicates) and result['order_matches'] and layout_matches is not False
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result['ok'] else 1
    except (OSError, UnicodeError):
        print(json.dumps({'error': '无法读取配置文件'}, ensure_ascii=False))
        return 2
    except ValueError as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
