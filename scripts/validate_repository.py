#!/usr/bin/env python3
"""只读校验 Uni 插件清单、发布版本、仓内入口及已采用的发布工具。"""

import argparse
import json
import re
from pathlib import Path

from scripts.sync_release_tools import check_release_tools


def read_json(path):
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError(f'{path}: 必须是 JSON 对象')
    return value


def local_file(root, base, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError(f'必须使用仓内相对文件路径：{name!r}')
    path = (base / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError(f'仓内入口不存在或越出仓库：{name}')
    return path


def validate_repository(root, release_tag=None):
    root = Path(root).resolve()
    check_release_tools(root)
    plugin = read_json(root / 'plugin.json')
    if plugin.get('name') != 'uni-skills':
        raise ValueError('plugin.json 必须声明 uni-skills')
    version = plugin.get('version')
    if not isinstance(version, str) or not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', version):
        raise ValueError('version 必须是无前导零的 X.Y.Z')
    if release_tag is not None and release_tag != f'v{version}':
        raise ValueError('发布 tag 与 plugin.json version 不一致')
    interface = plugin
    for field in ('extensions', 'com.openai', 'interface'):
        interface = interface.get(field, {})
        if not isinstance(interface, dict):
            raise ValueError(f'插件 {field} 必须是对象')
    for field in ('composerIcon', 'logo', 'logoDark'):
        if field in interface:
            local_file(root, root, interface[field])
    for screenshot in interface.get('screenshots', []):
        local_file(root, root, screenshot)
    marketplace = read_json(root / '.agents/plugins/marketplace.json')
    entries = marketplace.get('plugins')
    if (marketplace.get('name') != plugin['name'] or not isinstance(entries, list) or len(entries) != 1
            or not isinstance(entries[0], dict) or entries[0].get('name') != plugin['name']
            or entries[0].get('source') != {'source': 'local', 'path': './'}):
        raise ValueError('本仓市场必须引用仓内 Uni 插件入口')
    directory = root / 'skills'
    skills = sorted(path for path in directory.iterdir() if path.is_dir())
    if not skills:
        raise ValueError('没有可分发技能')
    for skill in skills:
        for name in ('SKILL.md', 'agents/openai.yaml'):
            if not local_file(root, skill, name).read_text(encoding='utf-8').strip():
                raise ValueError(f'技能入口为空：{skill.name}/{name}')
    return len(skills)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--release-tag')
    args = parser.parse_args()
    try:
        count = validate_repository(args.root, release_tag=args.release_tag)
    except (OSError, ValueError) as error:
        parser.exit(1, f'仓库入口校验失败：{error}\n')
    print(f'Uni 插件清单、{count} 个技能入口与发布工具校验通过。')


if __name__ == '__main__':
    main()
