#!/usr/bin/env python3
"""从显式指定的本地 Unif 技能仓同步发布器及行为测试；--check 只读比较来源。"""

import argparse
from collections.abc import Callable
import hashlib
import json
import re
from pathlib import Path
from typing import TypeGuard, TypedDict


FILES = ('scripts/prepare_release.py', 'scripts/publish_release.py',
         'tests/test_prepare_release.py', 'tests/test_publish_release.py')
RECORD = 'scripts/release-tools.json'
SOURCE = 'unif-skill/unif-portal-dev-skills'
load_json: Callable[[str], object] = json.loads


class AdoptionRecord(TypedDict):
    formatVersion: int
    source: str
    files: dict[str, str]


def is_mapping(value: object) -> TypeGuard[dict[object, object]]:
    return isinstance(value, dict)


def is_record(value: object) -> TypeGuard[AdoptionRecord]:
    if not is_mapping(value) or value.get('formatVersion') != 1 or value.get('source') != SOURCE:
        return False
    files = value.get('files')
    return (is_mapping(files) and set(files) == set(FILES)
            and all(isinstance(name, str) and isinstance(digest, str) for name, digest in files.items()))


def managed_path(root: Path, name: str) -> Path:
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


def check_release_tools(root: str | Path) -> AdoptionRecord:
    root = Path(root)
    record = load_json(managed_path(root, RECORD).read_text(encoding='utf-8'))
    if not is_record(record):
        raise ValueError('发布工具来源记录无效或受管文件集合不一致')
    for name in FILES:
        digest = record['files'][name]
        if not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError(f'发布工具摘要无效：{name}')
        path = managed_path(root, name)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f'发布工具与采用来源不一致：{name}')
    return record


def sync_release_tools(source: str | Path, target: str | Path, *, check: bool = False) -> None:
    source, target = Path(source), Path(target)
    contents = {name: managed_path(source, name).read_bytes() for name in FILES}
    paths = {name: managed_path(target, name) for name in FILES}
    record_path = managed_path(target, RECORD)
    expected: AdoptionRecord = {
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
        _ = path.write_bytes(contents[name])
    _ = record_path.write_text(json.dumps(expected, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    _ = check_release_tools(target)


class Arguments(argparse.Namespace):
    source: Path = Path()
    target: Path = Path(__file__).resolve().parents[1]
    check: bool = False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument('--source', required=True, type=Path, help='本地 Unif 技能源码仓目录')
    _ = parser.add_argument('--target', type=Path, default=Path(__file__).resolve().parents[1])
    _ = parser.add_argument('--check', action='store_true')
    args = parser.parse_args(namespace=Arguments())
    try:
        sync_release_tools(args.source, args.target, check=args.check)
    except (OSError, ValueError) as error:
        parser.exit(1, f'发布工具同步失败：{error}\n')
    print('发布工具与指定来源一致。' if args.check else '已同步发布工具及来源摘要，请审查工作树。')


if __name__ == '__main__':
    main()
