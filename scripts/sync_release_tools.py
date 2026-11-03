#!/usr/bin/env python3
"""从显式指定的本地 Unif 技能仓同步发布器及行为测试；--check 只读比较来源。"""

import argparse
import hashlib
import json
import re
from pathlib import Path


FILES = ('scripts/prepare_release.py', 'scripts/publish_release.py',
         'tests/test_prepare_release.py', 'tests/test_publish_release.py')
RECORD = 'scripts/release-tools.json'
SOURCE = 'unif-skill/unif-portal-dev-skills'


def managed_path(root, name):
    path = root
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f'仓库目录必须是普通目录：{root}')
    for part in Path(name).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError(f'受管路径不能是符号链接：{path}')
        if path.exists() and not (path.is_file() if path == root / name else path.is_dir()):
            raise ValueError(f'受管路径类型无效：{path}')
    return path


def check_release_tools(root):
    root = Path(root)
    record = json.loads(managed_path(root, RECORD).read_text(encoding='utf-8'))
    if (not isinstance(record, dict) or record.get('formatVersion') != 1
            or record.get('source') != SOURCE or not isinstance(record.get('files'), dict)
            or set(record['files']) != set(FILES)):
        raise ValueError('发布工具来源记录无效或受管文件集合不一致')
    for name in FILES:
        digest = record['files'][name]
        if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError(f'发布工具摘要无效：{name}')
        path = managed_path(root, name)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f'发布工具与采用来源不一致：{name}')
    return record


def sync_release_tools(source, target, *, check=False):
    source, target = Path(source), Path(target)
    contents = {name: managed_path(source, name).read_bytes() for name in FILES}
    paths = {name: managed_path(target, name) for name in FILES}
    record_path = managed_path(target, RECORD)
    expected = {
        'formatVersion': 1, 'source': SOURCE,
        'files': {name: hashlib.sha256(content).hexdigest() for name, content in contents.items()},
    }
    if record_path.exists():
        adopted = check_release_tools(target)
        if check:
            if adopted != expected:
                raise ValueError('发布工具与指定本地来源不同，请审查后同步')
            return
    elif check:
        raise ValueError('尚未采用发布工具来源')
    else:
        for name, path in paths.items():
            if path.exists() and path.read_bytes() != contents[name]:
                raise ValueError(f'拒绝覆盖未纳管的已有文件：{name}')
    for name, path in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents[name])
    record_path.write_text(json.dumps(expected, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    check_release_tools(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path, help='本地 Unif 技能源码仓目录')
    parser.add_argument('--target', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        sync_release_tools(args.source, args.target, check=args.check)
    except (OSError, ValueError) as error:
        parser.exit(1, f'发布工具同步失败：{error}\n')
    print('发布工具与指定来源一致。' if args.check else '已同步发布工具及来源摘要，请审查工作树。')


if __name__ == '__main__':
    main()
