from abc import ABC, abstractmethod
import dash_html_components as html


class Nameable(ABC):
    @abstractmethod
    def get_name(self):
        pass

    def get_color(self):
        return None

    def get_name_component(self):
        return html.Span(self.get_name(), style={"color": "#%s" % self.get_color()})
