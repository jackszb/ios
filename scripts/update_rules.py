#!/usr/bin/env python3
"""
下载规则源文件并使用 sing-box 编译为二进制 .srs 规则集。

用法:
    python3 update_rules.py

环境变量:
    SING_BOX_BIN   sing-box 可执行文件路径 (默认: "sing-box")
"""

import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

# 源文件 URL -> (中间 json 文件名, 输出的 .srs 文件名)
RULES = [
    (
        "https://raw.githubusercontent.com/jackszb/ip-merge/main/rules/ipv4.json",
        "ipv4.json",
        "geoip-cn.srs",
    ),
    (
        "https://raw.githubusercontent.com/jackszb/iphone-simple-rules/main/rules/direct.json",
        "direct.json",
        "geosite-cn.srs",
    ),
    (
        "https://raw.githubusercontent.com/jackszb/iphone-simple-rules/main/rules/proxy.json",
        "proxy.json",
        "geosite-!cn.srs",
    ),
    (
        "https://raw.githubusercontent.com/jackszb/ads/main/adblock_reject.json",
        "reject.json",
        "adblock.srs",
    ),
]

REPO_ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = REPO_ROOT / "rules"
TMP_DIR = REPO_ROOT / "tmp_rules"
SING_BOX_BIN = os.environ.get("SING_BOX_BIN", "sing-box")


def download(url: str, dest: Path) -> None:
    print(f"下载 {url} -> {dest}")
    req = urllib.request.Request(url, headers={"User-Agent": "update-rules-script"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status != 200:
            raise RuntimeError(f"下载失败 ({resp.status}): {url}")
        dest.write_bytes(resp.read())


def compile_rule(src_json: Path, dest_srs: Path) -> None:
    print(f"编译 {src_json.name} -> {dest_srs}")
    result = subprocess.run(
        [SING_BOX_BIN, "rule-set", "compile", "--output", str(dest_srs), str(src_json)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"sing-box 编译失败: {src_json}")


def main() -> None:
    if shutil.which(SING_BOX_BIN) is None:
        print(f"错误: 未找到 sing-box 可执行文件 ({SING_BOX_BIN})", file=sys.stderr)
        sys.exit(1)

    RULES_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    try:
        for url, json_name, srs_name in RULES:
            json_path = TMP_DIR / json_name
            srs_path = RULES_DIR / srs_name
            download(url, json_path)
            compile_rule(json_path, srs_path)
    finally:
        shutil.rmtree(TMP_DIR, ignore_errors=True)

    print("全部规则集更新完成。")


if __name__ == "__main__":
    main()
