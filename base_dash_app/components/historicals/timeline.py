from typing import List

import dash_core_components as dcc

from base_dash_app.components.base_component import BaseComponent
from base_dash_app.virtual_objects.interfaces.resultable_event import ResultableEvent


class Timeline(BaseComponent):
    """
        Experimental: under construction!
    """
    def render(self, *, events: List[ResultableEvent]):
        if len(events) == 0:
            return None

        start_date = events[0].date
        end_date = events[-1].date
        end_index = (end_date - start_date).days
        marks_temp = {}
        for re in events[1:-1]:
            day_index = (re.date - start_date).days
            if day_index not in marks_temp:
                marks_temp[day_index] = 0

            marks_temp[day_index] += 1

        marks = {

        }
        for k, v in marks_temp.items():
            marks[k] = {'label': '%i' % v}

        marks[0] = {'label': start_date.strftime("%d/%m/%Y")}
        marks[end_index] = {'label': end_date.strftime("%d/%m/%Y")}

        slider = dcc.Slider(
            min=0, max=end_index,
            tooltip={'placement': 'bottom'}, value=0,
            marks=marks
        )

        return slider
