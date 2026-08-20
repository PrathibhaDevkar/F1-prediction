"""Rolling-form features: how a driver/team has actually been performing
recently, rather than just their static identity. This is the highest-
leverage addition for prediction quality — grid/team/driver/circuit alone
carry very little signal about *current* competitiveness or reliability.

Used identically at training time (via RaceHistory, built up race-by-race
in chronological order) and at inference time (predicting the next race
from the same fully-built history), so there's no train/serve skew.
"""
from collections import defaultdict

ROLLING_WINDOW = 5
DNF_WINDOW = 10
DEFAULT_AVG_FINISH = 10.5  # midpoint of a ~20-car grid — used when there's no history yet
DEFAULT_DNF_RATE = 0.15  # a reasonable league-average fallback

FINISHED_STATUSES = {"Finished", "Lapped"}


def is_dnf(status: str) -> bool:
    return status not in FINISHED_STATUSES


class RaceHistory:
    """Call features_before_this_race() to get a driver/team's rolling
    form BEFORE recording the race's outcome, then record_result() to
    fold that race in for the next one — this ordering is what prevents
    a race's own result from leaking into its own features.
    """

    def __init__(self):
        self._driver_finishes: dict[str, list[float]] = defaultdict(list)
        self._driver_dnfs: dict[str, list[int]] = defaultdict(list)
        self._team_finishes: dict[str, list[float]] = defaultdict(list)

    def driver_snapshot(self, driver: str) -> dict:
        d_hist = self._driver_finishes[driver][-ROLLING_WINDOW:]
        dnf_hist = self._driver_dnfs[driver][-DNF_WINDOW:]
        return {
            "driver_recent_avg_finish": sum(d_hist) / len(d_hist) if d_hist else DEFAULT_AVG_FINISH,
            "driver_dnf_rate": sum(dnf_hist) / len(dnf_hist) if dnf_hist else DEFAULT_DNF_RATE,
        }

    def team_snapshot(self, team: str) -> dict:
        t_hist = self._team_finishes[team][-ROLLING_WINDOW:]
        return {
            "team_recent_avg_finish": sum(t_hist) / len(t_hist) if t_hist else DEFAULT_AVG_FINISH,
        }

    def features_before_this_race(self, driver: str, team: str) -> dict:
        return {**self.driver_snapshot(driver), **self.team_snapshot(team)}

    def record_result(self, driver: str, team: str, finish: float, status: str):
        self._driver_finishes[driver].append(finish)
        self._team_finishes[team].append(finish)
        self._driver_dnfs[driver].append(1 if is_dnf(status) else 0)
