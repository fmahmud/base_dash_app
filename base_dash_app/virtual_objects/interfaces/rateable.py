from abc import ABC
from typing import List, Optional

import trueskill

from base_dash_app.virtual_objects.interfaces.representable import Representable
from trueskill import Rating, rate


class Rateable(Representable, ABC):
    def __init__(self, starting_trueskill: float = 25):
        self.trueskill: Rating = Rating(starting_trueskill)

    def set_rating(self, rating):
        self.rating = rating

    def get_rating(self):
        return self.rating

    def get_trueskill_mu(self):
        return self.trueskill.mu

    @staticmethod
    def update_trueskills(winning_team: Optional[List['Rateable']], losing_teams: List[List['Rateable']]):
        if winning_team is None:
            # draw
            new_ratings = rate(
                [tuple([player.trueskill for player in lt]) for lt in losing_teams],
                ranks=[0] * (len(losing_teams))
            )

            for i in range(len(new_ratings)):
                for j in range(len(new_ratings[i])):
                    losing_teams[i][j].trueskill = new_ratings[i][j]
        else:
            new_winning_team_data, *losing_teams_data = rate([tuple([w.trueskill for w in winning_team])]
                                                             + [tuple([loser.trueskill for loser in lt])
                                                                for lt in losing_teams])
            diff_map = {}
            for i in range(len(new_winning_team_data)):
                if winning_team[i] not in diff_map:
                    diff_map[winning_team[i]] = [0, 0]
                diff_map[winning_team[i]][0] += new_winning_team_data[i].mu - winning_team[i].trueskill.mu
                diff_map[winning_team[i]][1] += new_winning_team_data[i].sigma - winning_team[i].trueskill.sigma

            for i in range(len(losing_teams_data)):
                for j in range(len(losing_teams_data[i])):
                    if losing_teams[i][j] not in diff_map:
                        diff_map[losing_teams[i][j]] = [0, 0]

                    diff_map[losing_teams[i][j]][0] += losing_teams_data[i][j].mu - losing_teams[i][j].trueskill.mu
                    diff_map[losing_teams[i][j]][1] += losing_teams_data[i][j].sigma - losing_teams[i][j].trueskill.sigma

            for k, v in diff_map.items():
                k.trueskill = trueskill.Rating(mu=k.trueskill.mu + v[0], sigma=k.trueskill.sigma + v[1])
