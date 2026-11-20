#!/usr/bin/env python3
"""只读校验 Uni 插件清单、发布版本、仓内入口及已采用的发布工具。"""

import argparse
import json
import re
from pathlib import Path
from collections.abc import Callable
from typing import TypeGuard

from scripts.skill_validation import check_skill, contained_path, is_object

from scripts.sync_release_tools import check_release_tools


load_json: Callable[[str], object] = json.loads


def is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def read_json(path: Path) -> dict[str, object]:
    value = load_json(path.read_text(encoding='utf-8'))
    if not is_object(value):
        raise ValueError(f'{path}: 必须是 JSON 对象')
    return value


def validate_repository(root: str | Path, release_tag: str | None = None) -> int:
    root = Path(root).resolve()
    _ = check_release_tools(root)
    plugin = read_json(root / 'plugin.json')
    if plugin.get('name') != 'uni-skills':
        raise ValueError('plugin.json 必须声明 uni-skills')
    version = plugin.get('version')
    if not isinstance(version, str) or not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', version):
        raise ValueError('version 必须是无前导零的 X.Y.Z')
    if release_tag is not None and release_tag != f'v{version}':
        raise ValueError('发布 tag 与 plugin.json version 不一致')
    interface: object = plugin
    for field in ('extensions', 'com.openai', 'interface'):
        if not is_object(interface):
            raise ValueError(f'插件 {field} 必须是对象')
        interface = interface.get(field, {})
        if not is_object(interface):
            raise ValueError(f'插件 {field} 必须是对象')
    if not is_object(interface):
        raise ValueError('插件 interface 必须是对象')
    for field in ('composerIcon', 'logo', 'logoDark'):
        if field in interface:
            _ = contained_path(root, root, interface[field])
    screenshots = interface.get('screenshots', [])
    if not is_list(screenshots):
        raise ValueError('插件 screenshots 必须是数组')
    for screenshot in screenshots:
        _ = contained_path(root, root, screenshot)
    marketplace = read_json(root / '.agents/plugins/marketplace.json')
    entries = marketplace.get('plugins')
    if (marketplace.get('name') != plugin['name'] or not is_list(entries) or len(entries) != 1
            or not is_object(entries[0]) or entries[0].get('name') != plugin['name']
            or entries[0].get('source') != {'source': 'local', 'path': './'}):
        raise ValueError('本仓市场必须引用仓内 Uni 插件入口')
    directory = root / 'skills'
    skills = sorted(path for path in directory.iterdir() if path.is_dir())
    if not skills:
        raise ValueError('没有可分发技能')
    for skill in skills:
        for name in ('SKILL.md', 'agents/openai.yaml'):
            if not contained_path(root, skill, name).read_text(encoding='utf-8').strip():
                raise ValueError(f'技能入口为空：{skill.name}/{name}')
        check_skill(skill)
    return len(skills)


class Arguments(argparse.Namespace):
    root: Path = Path(__file__).resolve().parents[1]
    release_tag: str | None = None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    _ = parser.add_argument('--release-tag')
    args = parser.parse_args(namespace=Arguments())
    try:
        count = validate_repository(args.root, release_tag=args.release_tag)
    except (OSError, ValueError) as error:
        parser.exit(1, f'仓库入口校验失败：{error}\n')
    print(f'Uni 插件清单、{count} 个技能入口与发布工具校验通过。')


if __name__ == '__main__':
    main()
