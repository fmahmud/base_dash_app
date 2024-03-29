from abc import ABC, abstractmethod
from typing import List

from base_dash_app.components.details.detail_text_item import DetailTextItem


class Detailable(ABC):
    @abstractmethod
    def get_text_items(self) -> List['DetailTextItem']:
        pass

    @abstractmethod
    def get_detail_component(self):
        pass

    def has_details(self):
        return True

    # @abstractmethod
    # def get_text1(self):
    #     pass
    #
    # @abstractmethod
    # def get_text2(self):
    #     pass
    #
    # @abstractmethod
    # def get_text3(self):
    #     pass
    #
    # @abstractmethod
    # def get_text4(self):
    #     pass
    #
    # @abstractmethod
    # def get_text5(self):
    #     pass

    def get_progress(self):
        return 0.0

    def show_progress_bar(self):
        return False

    @abstractmethod
    def show_ratio_bar(self):
        pass

    @abstractmethod
    def get_successes(self):
        pass

    @abstractmethod
    def get_warnings(self):
        pass

    @abstractmethod
    def get_failures(self):
        pass

    @abstractmethod
    def get_in_progress(self):
        pass

    def get_num_rows(self):
        return 1

    def get_summary_div_id(self):
        pass

    def get_details_element_id(self):
        pass

    def get_wrapper_element_id(self):
        pass

    @abstractmethod
    def get_num_pending(self):
        pass

    @abstractmethod
    def get_height_override(self):
        return None