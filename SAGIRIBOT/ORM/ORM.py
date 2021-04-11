import yaml
from os import environ
from loguru import logger

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

yaml.warnings({'YAMLLoadWarning': False})
environ['NLS_LANG'] = 'AMERICAN_AMERICA.AL32UTF8'

# DB_LINK = 'oracle://test:123456@localhost:1521/xe'
# DB_LINK = "mysql+aiomysql://root:pass@localhost:3306/test"
# DB_LINK = "sqlite:///data.db"


def get_config(config: str):
    with open('config.yaml', 'r', encoding='utf-8') as f:  # 从json读配置
        configs = yaml.load(f.read())
    if config in configs.keys():
        return configs[config]
    else:
        logger.error(f"getConfig Error: {config}")


DB_LINK = get_config("DBLink")


class Engine:
    def __init__(self, db_link):
        self.engine = create_engine(
            db_link,
            encoding='utf8',
            # max_overflow=0,
            # pool_size=5,
            # pool_timeout=30,
            # pool_recycle=-1
        )

    def execute(self, sql, **kwargs):
        """含commit操作，返回<class 'sqlalchemy.engine.result.ResultProxy'>"""
        return self.engine.execute(sql, **kwargs)

    def fetchall(self, sql):
        return self.execute(sql).fetchall()

    def fetchone(self, sql, n=999999):
        # self.warning(sql)
        result = self.execute(sql)
        for _ in range(n):
            one = result.fetchone()
            if one:
                yield one

    def fetchone_dt(self, sql, n=999999):
        # self.warning(sql)
        result = self.execute(sql)
        columns = result.keys()
        length = len(columns)
        for _ in range(n):
            one = result.fetchone()
            if one:
                yield {columns[i]: one[i] for i in range(length)}

    @staticmethod
    def warning(x):
        print('\033[033m{}\033[0m'.format(x))

    @staticmethod
    def error(x):
        print('\033[031m{}\033[0m'.format(x))


class ORM(Engine):
    """对象关系映射（Object Relational Mapping）"""

    def __init__(self, conn):
        super().__init__(conn)
        Session = sessionmaker(bind=self.engine)  # 创建ORM基类
        self.session = Session()  # 创建ORM对象
        self.Base = declarative_base(self.engine)
        self.create_all()

    def __del__(self):
        self.session.close()

    def create_all(self):
        """创建所有表"""
        self.Base.metadata.create_all(bind=self.engine)

    def drop_all(self):
        """创建所有表"""
        self.Base.metadata.drop_all(bind=self.engine)

    def add(self, table, dt):
        """插入"""
        self.session.add(table(**dt))  # 添加到ORM对象
        self.session.commit()  # 提交

    def update(self, table, condition, dt):
        """有则更新，没则插入"""
        q = self.session.query(table).filter_by(**condition)
        if q.all():
            q.update(dt)
            self.session.commit()
        else:
            self.add(table, dt)

    def delete(self, table, condition):
        q = self.session.query(table).filter_by(**condition)
        if q.all():
            q.delete()
            self.session.commit()


orm = ORM(DB_LINK)
from .Tables import *
# orm.drop_all()
orm.create_all()
