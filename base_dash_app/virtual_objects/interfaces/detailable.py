from abc import ABC, abstractmethod
from typing import List


class Detailable(ABC):
    @abstractmethod
    def get_text_items(self) -> List['DetailTextItem']:
        pass

    @abstractmethod
    def get_detail_component(self):
        pass

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