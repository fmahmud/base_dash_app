from sqlalchemy.ext.declarative import declarative_base

__Base = declarative_base()


def get_base_class():
    return __Base


