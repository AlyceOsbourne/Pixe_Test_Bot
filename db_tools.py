import zlib
from typing import Any
import sqlalchemy.orm


class CompressedBLOB(sqlalchemy.TypeDecorator):
    impl = sqlalchemy.LargeBinary

    def __init__(self, compression_level, *args, **kwargs):
        self.compression_level = compression_level
        self.hash = None
        self.dtype = None
        super().__init__(*args, **kwargs)

    def process_bind_param(self, value: Any, dialect: sqlalchemy.engine.interfaces.Dialect) -> Any:
        self.hash = hash(value)
        self.dtype = type(value)
        return zlib.compress(value)

    def process_result_value(self, value: Any, dialect: sqlalchemy.engine.interfaces.Dialect) -> Any:
        return self.dtype(zlib.decompress(value))

    def copy(self):
        return CompressedBLOB(self.compression_level)

    def compare_values(self, x: Any, y: Any) -> bool:
        # if y is not instance of hash, then get the hash of the object
        if not isinstance(y, int):
            y = hash(y)
        return x == y

    def process_literal_param(self, value, dialect):
        return value

    @property
    def python_type(self):
        return self.dtype

    @python_type.setter
    def python_type(self, value):
        self.dtype = value
