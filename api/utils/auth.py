"""
认证工具模块
使用 argon2id 进行密码哈希
使用 JWT 进行 Token 管理
"""
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from ..config import config

# 密码哈希器
ph = PasswordHasher()

# 固定使用 HS256 算法
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """哈希密码"""
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    try:
        ph.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False


def create_access_token(data: dict) -> str:
    """创建 JWT Token（永不过期）"""
    to_encode = data.copy()
    # 不设置 exp 字段，Token 永不过期
    encoded_jwt = jwt.encode(
        to_encode,
        config.auth.secret_key,
        algorithm=ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """解码 JWT Token"""
    try:
        payload = jwt.decode(
            token,
            config.auth.secret_key,
            algorithms=[ALGORITHM],
            options={"verify_exp": False}  # 不验证过期时间
        )
        return payload
    except JWTError:
        return None