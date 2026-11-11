#!/usr/bin/env python3
"""从已签名、公证的应用生成固定版本 ZIP 和 Cask；不发布未通过检查的产物。"""
import argparse
import hashlib
import json
import pathlib
import plistlib
import re
import subprocess
import sys
import urllib.parse

PRODUCTS = {
    'voido': ('Voido', 'void-vision/voido', 'https://voido.ai/', 'Calendar, tasks, projects and AI workspace'),
    'void-island': ('Void Island', 'void-vision/void-island', 'https://voidisland.app/', 'AI sessions, Git and keep awake in the notch'),
}
TEAM = '8CQ9FMKK34'


def run(*command):
    result = subprocess.run(command, capture_output=True, text=True, timeout=90)
    if result.returncode:
        raise ValueError(result.stderr.strip() or result.stdout.strip() or '检查失败')
    return result.stdout + result.stderr


def render_cask(args, app, digest):
    name, _, homepage, desc = PRODUCTS[args.product]
    token = f'{args.product}@{args.channel}'
    other = f'{args.product}@' + ('beta' if args.channel == 'alpha' else 'alpha')
    quote = lambda value: json.dumps(value, ensure_ascii=False)
    return '\n'.join([
        f'cask {quote(token)} do',
        f'  version {quote(args.version)}',
        f'  sha256 {quote(digest)}',
        '',
        f'  url {quote(args.url)}',
        f'  name {quote(name)}',
        f'  desc {quote(desc)}',
        f'  homepage {quote(homepage)}',
        '',
        '  livecheck do',
        '    skip "Channel versions are published after release verification"',
        '  end',
        '',
        f'  conflicts_with cask: [{quote(args.product)}, {quote(other)}]',
        f'  depends_on arch: :{args.arch}',
        f'  depends_on macos: :{args.min_macos}',
        '',
        f'  app {quote(app.name)}',
        'end',
        '',
    ])


def prepare(args):
    app = args.app.resolve()
    if app.suffix != '.app' or not app.is_dir():
        raise ValueError('请提供已完成签名公证的 .app 目录')
    name, repo, homepage, desc = PRODUCTS[args.product]
    info = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
    base_id = 'ai.voidvision.calendar' if args.product == 'voido' else 'ai.voidvision.island'
    if info.get('CFBundleIdentifier') not in [base_id, base_id + '.' + args.channel]:
        raise ValueError('应用标识与产品或通道不匹配')
    if info.get('CFBundleShortVersionString') != args.version:
        raise ValueError('版本必须与应用 Info.plist 一致')
    version_match = re.fullmatch(r'\d+(?:\.\d+){1,3}-(alpha|beta)(?:[.-][0-9A-Za-z-]+)*', args.version)
    if not version_match or version_match.group(1) != args.channel:
        raise ValueError('alpha 与 beta 使用明确的预发布版本，不能把另一个通道冒充为 alpha')
    parsed = urllib.parse.urlparse(args.url)
    prefix = f'https://github.com/{repo}/releases/download/'
    if not args.url.startswith(prefix + 'v' + args.version + '/') or not parsed.path.endswith('.zip'):
        raise ValueError(f'下载地址必须是 {repo} 的固定版本 Release ZIP')
    run('/usr/bin/codesign', '--verify', '--strict', '--deep', str(app))
    signature = run('/usr/bin/codesign', '-d', '--verbose=4', str(app))
    if f'TeamIdentifier={TEAM}' not in signature or 'Authority=Developer ID Application:' not in signature:
        raise ValueError('应用尚未用 VOID VISION 的 Developer ID 签名；不会生成可安装 Cask')
    run('/usr/sbin/spctl', '--assess', '--type', 'execute', '--verbose=2', str(app))
    executable = app / 'Contents/MacOS' / info['CFBundleExecutable']
    actual_arches = run('/usr/bin/lipo', '-archs', str(executable)).split()
    if args.arch not in actual_arches:
        raise ValueError('声明的架构不在实际应用中')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    archive = output / urllib.parse.unquote(pathlib.PurePosixPath(parsed.path).name)
    if archive.exists():
        raise ValueError('输出 ZIP 已存在；请使用新的输出目录')
    run('/usr/bin/ditto', '-c', '-k', '--sequesterRsrc', '--keepParent', str(app), str(archive))
    with archive.open('rb') as file:
        digest = hashlib.file_digest(file, 'sha256').hexdigest()
    cask = render_cask(args, app, digest)
    token = f'{args.product}@{args.channel}'
    root = pathlib.Path(__file__).resolve().parent.parent
    target = root / 'Casks' / f'{token}.rb'
    target.write_text(cask)
    manifest = {'product': args.product, 'channel': args.channel, 'version': args.version, 'url': args.url, 'sha256': digest, 'archive': str(archive), 'cask': str(target)}
    (output / 'release.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--product', choices=PRODUCTS, required=True)
    parser.add_argument('--channel', choices=['alpha', 'beta'], required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--app', type=pathlib.Path, required=True)
    parser.add_argument('--url', required=True)
    parser.add_argument('--arch', choices=['arm64', 'x86_64'], required=True)
    parser.add_argument('--min-macos', choices=['monterey', 'ventura', 'sonoma', 'sequoia', 'tahoe'], required=True)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    try:
        prepare(parser.parse_args())
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(f'未生成 Cask：{error}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
