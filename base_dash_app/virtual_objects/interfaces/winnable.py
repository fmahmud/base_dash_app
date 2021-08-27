import datetime
from abc import ABC
from typing import List, Type, Callable, Optional, Dict, Tuple

import trueskill

from base_dash_app.virtual_objects.interfaces.dimension import Dimension
from base_dash_app.virtual_objects.interfaces.resultable_event import ResultableEvent
from base_dash_app.virtual_objects.interfaces.listable import Listable
from base_dash_app.virtual_objects.interfaces.representable import Representable


class BaseWinnablesDimension(Dimension, ABC):
    pass


class CompetitorDimension(BaseWinnablesDimension, Listable, ABC):
    pass


class CompetingTeamDimension(BaseWinnablesDimension, ABC):
    pass


class WinnableDimension(BaseWinnablesDimension, ABC):
    pass


class Competitor(Representable, ABC):
    def __init__(self, data: List[CompetitorDimension], team: 'CompetingTeam'):
        self.data: List[CompetitorDimension] = sorted(data)
        self.team = team

    def __lt__(self, other):
        if type(other) != Competitor:
            return True
        return self.data[0].__lt__(other.data[0])

    def get_name_components(self):
        return [d.get_name_component() for d in self.data]

    def get_name_for_dim(self, dim: Type[CompetitorDimension]):
        for d in self.data:
            if type(d) == dim:
                return d.get_name()

    def get_color_for_dim(self, dim: Type[CompetitorDimension]):
        for d in self.data:
            if type(d) == dim:
                return d.get_color()

    def get_repr(self):
        temp = []
        for cd in self.data:
            temp.append(*cd.get_repr())

        return tuple(temp)

    @staticmethod
    def get_repr_for_dims_and_values(data: List[CompetitorDimension], dims: List[Type[CompetitorDimension]]):
        """
           Returns a representation of only the dimensions that are of concern.
           e.g. passed dims = [CompetitivePlayer], response = ("Player1")
           e.g.2 passed dims = [CompetitivePlayer, CompetitiveArmy], response = ("Player1", "Army2")
           :param data:
           :param dims:
           :return:
        """
        temp = []
        for cd in sorted(data):
            if type(cd) in dims:
                temp.append(*cd.get_repr())

        return tuple(temp)

    def get_repr_for_dims(self, dims: List[Type[CompetitorDimension]]):
        return Competitor.get_repr_for_dims_and_values(self.data, dims)

    def has_all_values(self, values: List[CompetitorDimension]):
        return all(value in self.data for value in values)

    def has_any_value(self, values: List[CompetitorDimension]):
        return any(value in self.data for value in values)


class CompetingTeam(Representable, ABC):
    def __init__(self, result: int, competitors: List[Competitor],
                 winnable: 'Winnable', *, extra_data: List[CompetingTeamDimension] = None):
        self.result: int = result
        self.competitors = sorted(competitors)
        self.winnable = winnable
        self.extra_data = sorted(extra_data) if extra_data is not None else []

    def get_competitors(self) -> List[Competitor]:
        return self.competitors

    def get_repr(self):
        return tuple([self.result]) \
               + tuple([c.get_repr() for c in self.competitors]) \
               + tuple([datum.get_repr() for datum in self.extra_data])

    @staticmethod
    def get_repr_for_dims_and_values(competitor_data: List[List[CompetitorDimension]],
                                     extra_data=None, result=None,
                                     include_result=False,
                                     competitor_dims: List[Type[CompetitorDimension]] = None,
                                     team_dims: List[Type[CompetingTeamDimension]] = None):
        representation = []
        if include_result:
            representation += [result]

        if competitor_dims is not None:
            temp = []
            for c in competitor_data:
                temp += list(Competitor.get_repr_for_dims_and_values(c, competitor_dims))
            representation += tuple(temp)

        if team_dims is not None:
            representation += [datum.get_repr() for datum in extra_data if type(datum) in sorted(team_dims)]

        if len(representation) == 0:
            raise Exception("No dimensions provided!")

        return tuple(representation)

    def get_repr_for_dims(self, *, include_result=False, competitor_dims: List[Type[CompetitorDimension]] = None,
                          team_dims: List[Type[CompetingTeamDimension]] = None):
        return CompetingTeam.get_repr_for_dims_and_values(
            [c.data for c in sorted(self.competitors)], self.extra_data, self.result,
            include_result, competitor_dims, team_dims
        )

    def has_competitor_with_all_values(self, values: List[CompetitorDimension]):
        return any(c.has_all_values(values) for c in self.competitors)

    def has_competitor_with_any_values(self, values: List[CompetitorDimension]):
        return any(c.has_any_value(values) for c in self.competitors)

    def has_multiple_competitors_with_all_specific_values(self, values_for_each_competitor: List[List[CompetitorDimension]]):
        return all(self.has_competitor_with_all_values(values) for values in values_for_each_competitor)


class Winnable(ResultableEvent, Representable, ABC):
    def __init__(self, winning_team: CompetingTeam,
                 losing_teams: List[CompetingTeam], date: datetime.datetime,
                 *, extra_data: List[WinnableDimension] = None):
        super().__init__(date)
        self.date = date
        self.winning_team: CompetingTeam = winning_team
        self.losing_teams: List[CompetingTeam] = losing_teams
        self.all_teams: List[CompetingTeam] = [] + [winning_team] + losing_teams
        self.extra_data = extra_data
        self.rating_cache: Dict[Tuple, trueskill.Rating] = {}

    def __lt__(self, other):
        return self.date < other.date

    def get_result(self, *, perspective: Callable[['Winnable'], Optional[int]] = None):
        if perspective is not None:
            return perspective(self)
        else:
            raise Exception("Get result needs perspective function in Winnables.")

    def get_all_teams(self) -> List[CompetingTeam]:
        return self.all_teams

    def get_winning_team(self) -> CompetingTeam:
        return self.winning_team

    def get_losing_teams(self) -> List[CompetingTeam]:
        return self.losing_teams

    def get_competitors(self) -> List[Competitor]:
        result = []
        for ct in self.all_teams:
            result += ct.get_competitors()

        return result

    def get_losers(self) -> List[Competitor]:
        result = []
        for ct in self.losing_teams:
            result += ct.get_competitors()

        return result

    def get_winners(self) -> List[Competitor]:
        return self.winning_team.get_competitors()

    def get_repr(self):
        return tuple([self.date]) \
               + tuple([ct.get_repr() for ct in self.all_teams]) \
               + tuple([datum.get_repr() for datum in self.extra_data])

    def has_competitor_with_all_values(self, values: List[CompetitorDimension]):
        return self.has_team_with_all_competitor_values(values)

    def has_team_with_all_competitor_values(self, values: List[CompetitorDimension]):
        return any(ct.has_competitor_with_all_values(values) for ct in self.all_teams)

    def has_team_with_any_competitor_value(self, values: List[CompetitorDimension]):
        return any(ct.has_competitor_with_any_values(values) for ct in self.all_teams)

    def has_team_with_multiple_competitors_with_all_specific_values(
            self, values_for_each_competitor: List[List[CompetitorDimension]]):

        return any(
            ct.has_multiple_competitors_with_all_specific_values(values_for_each_competitor)
            for ct in self.all_teams
       )

    def get_repr_for_dims(self, *, winnable_dims: List[WinnableDimension] = None,
                          team_dims: List[CompetingTeamDimension] = None,
                          competitor_dims: List[CompetitorDimension] = None,
                          include_date=False, include_result=False):
        representation = tuple()

        if include_date:
            representation += tuple([self.date])

        if winnable_dims is not None:
            representation += tuple([datum.get_repr() for datum in self.extra_data if type(datum) in winnable_dims])

        if team_dims is not None:
            representation += tuple([team.get_repr_for_dims(team_dims=team_dims, include_result=include_result)
                                     for team in self.all_teams])

        if competitor_dims is not None:
            representation += tuple([competitor.get_repr_for_dims(competitor_dims)
                                     for competitor in self.get_competitors()])

        return representation
