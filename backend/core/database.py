from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    # connect_args={"check_same_thread": False} # 仅在SQLite时需要
)

# 创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建一个Base类，我们的ORM模型将继承这个类
Base = declarative_base()