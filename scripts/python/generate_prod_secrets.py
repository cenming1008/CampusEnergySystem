"""
生成生产环境所需的高强度密钥/密码片段。
"""

from __future__ import annotations

import argparse
import secrets
import string


PASSWORD_ALPHABET = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"


def generate_password(length: int) -> str:
    if length < 16:
        raise ValueError("密码长度至少为 16")
    return "".join(secrets.choice(PASSWORD_ALPHABET) for _ in range(length))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成园区综合能源管理系统生产环境密钥片段")
    parser.add_argument("--password-length", type=int, default=24, help="生成密码长度，默认 24")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print("# 复制到 .env.prod 前请再次核对目标环境")
    print(f"DB_PASSWORD={generate_password(args.password_length)}")
    print(f"REDIS_PASSWORD={generate_password(args.password_length)}")
    print(f"GRAFANA_ADMIN_PASSWORD={generate_password(args.password_length)}")
    print(f"SECRET_KEY={secrets.token_urlsafe(48)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
