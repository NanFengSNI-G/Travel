import os
from pathlib import Path
from dotenv import load_dotenv
from dynaconf import Dynaconf

load_dotenv()

_BASE_DIR = Path(__file__).parent.parent.parent  # app/core/config.py -> 项目根目录

settings_files = [
    _BASE_DIR / 'config' / 'development.yml'
]

settings = Dynaconf(
    envvar_prefix="EMP_CONF",
    settings_files=settings_files,
    env_switcher="EMP_ENV",
    lowercase_read=False,
    base_dir=_BASE_DIR,
)

# 从环境变量读取敏感配置
if os.environ.get("MySQL_PASSWORD"):
    settings.DATABASE.PASSWORD = os.environ["MySQL_PASSWORD"]

DASHSCOPE_API_KEY = os.environ.get("API_KEY")