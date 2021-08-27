from abc import ABC, abstractmethod


class Listable(ABC):
    @abstractmethod
    def get_header(self) -> (str, dict):
        pass

    @abstractmethod
    def get_text(self) -> (str, dict):
        pass

    @abstractmethod
    def get_extras(self):
        pass


class RuntimeListable(Listable):
    def __init__(self, *, header, header_style=None, text=None, text_style=None, extras=None):
        self.header = header
        self.header_style = header_style
        self.text = text
        self.text_style = text_style
        self.extras = extras

    def get_header(self) -> (str, dict):
        return self.header, self.header_style

    def get_text(self) -> (str, dict):
        return self.text, self.text_style

    def get_extras(self):
        return self.extras