from __future__ import annotations

from math import ceil

from simpleai.search import SearchProblem, astar


Point = tuple[int, int]
State = tuple[
    Point,
    int,
    str | None,
    int,
    tuple[Point, ...],
    tuple[Point, ...],
]

DRILL_TERMICO = "termico"
DRILL_PERCUSION = "percusion"
SAMPLE_IGNEA = "ignea"
SAMPLE_SEDIMENTARIA = "sedimentaria"
MAX_BATTERY = 20


def _normalize_points(points):
    return tuple(sorted(set(points)))


def _manhattan(a: Point, b: Point) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _drill_for(sample_type: str) -> str:
    return DRILL_TERMICO if sample_type == SAMPLE_IGNEA else DRILL_PERCUSION


def _sample_type_at(position: Point, igneous: tuple[Point, ...], sediments: tuple[Point, ...]) -> str | None:
    if position in igneous:
        return SAMPLE_IGNEA
    if position in sediments:
        return SAMPLE_SEDIMENTARIA
    return None


class RoverProblem(SearchProblem):
    def __init__(
        self,
        rover_inicio: Point,
        bateria_inicial: int,
        zonas_sombra,
        muestras_igneas,
        muestras_sedimentarias,
    ):
        self.zonas_sombra = frozenset(zonas_sombra)
        self.rover_inicio = rover_inicio
        self.muestras_igneas_iniciales = _normalize_points(muestras_igneas)
        self.muestras_sedimentarias_iniciales = _normalize_points(muestras_sedimentarias)

        all_points = [rover_inicio, *self.muestras_igneas_iniciales, *self.muestras_sedimentarias_iniciales, *self.zonas_sombra]
        rows = [point[0] for point in all_points]
        cols = [point[1] for point in all_points]
        self.row_min = min(rows) - 2
        self.row_max = max(rows) + 2
        self.col_min = min(cols) - 2
        self.col_max = max(cols) + 2

        initial_state: State = (
            rover_inicio,
            bateria_inicial,
            None,
            0,
            self.muestras_igneas_iniciales,
            self.muestras_sedimentarias_iniciales,
        )
        super().__init__(initial_state)

    def _in_bounds(self, position: Point) -> bool:
        return (
            self.row_min <= position[0] <= self.row_max
            and self.col_min <= position[1] <= self.col_max
        )

    def _moves(self, position: Point):
        row, col = position
        deltas = [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
        ]
        for delta_row, delta_col in deltas:
            target = (row + delta_row, col + delta_col)
            if self._in_bounds(target):
                yield ("moverse", target)

            target_overdrive = (row + 2 * delta_row, col + 2 * delta_col)
            if self._in_bounds(target_overdrive):
                yield ("sobremarcha", target_overdrive)

    def actions(self, state: State):
        position, battery, drill, load, igneous, sediments = state
        actions = []

        if load and (load == 2 or (load == 1 and not igneous and not sediments)):
            actions.append(("depositar", None))

        sample_type = _sample_type_at(position, igneous, sediments)
        if sample_type == SAMPLE_IGNEA and drill == DRILL_TERMICO and load < 2 and battery > 3:
            actions.append(("recolectar", SAMPLE_IGNEA))
        elif sample_type == SAMPLE_SEDIMENTARIA and drill == DRILL_PERCUSION and load < 2 and battery > 3:
            actions.append(("recolectar", SAMPLE_SEDIMENTARIA))

        if battery < MAX_BATTERY and position not in self.zonas_sombra:
            actions.append(("recargar", None))

        if drill != DRILL_TERMICO and battery > 1:
            actions.append(("equipar", DRILL_TERMICO))
        if drill != DRILL_PERCUSION and battery > 1:
            actions.append(("equipar", DRILL_PERCUSION))

        remaining_positions = igneous + sediments
        move_actions = [
            action
            for action in self._moves(position)
            if (action[0] == "moverse" and battery > 1) or (action[0] == "sobremarcha" and battery > 4)
        ]

        if remaining_positions:
            target_positions = tuple(sorted(remaining_positions))

            def move_priority(action):
                _, target = action
                distance = min(_manhattan(target, other) for other in target_positions)
                return (distance, action[0] == "sobremarcha", target)

            actions.extend(sorted(move_actions, key=move_priority))
        else:
            actions.extend(move_actions)

        return actions

    def result(self, state: State, action):
        position, battery, drill, load, igneous, sediments = state
        action_type, target = action

        if action_type == "moverse" or action_type == "sobremarcha":
            return (target, battery, drill, load, igneous, sediments)

        if action_type == "equipar":
            return (position, battery, target, load, igneous, sediments)

        if action_type == "recolectar":
            if target == SAMPLE_IGNEA:
                remaining_igneous = tuple(sample for sample in igneous if sample != position)
                return (position, battery, drill, load + 1, remaining_igneous, sediments)
            remaining_sediments = tuple(sample for sample in sediments if sample != position)
            return (position, battery, drill, load + 1, igneous, remaining_sediments)

        if action_type == "depositar":
            return (position, battery, drill, 0, igneous, sediments)

        if action_type == "recargar":
            return (position, min(MAX_BATTERY, battery + 10), drill, load, igneous, sediments)

        return state

    def cost(self, state: State, action, state2):
        action_type, target = action
        if action_type == "moverse" or action_type == "sobremarcha":
            return 1
        if action_type == "equipar":
            return 3
        if action_type == "recolectar":
            return 2
        if action_type == "depositar":
            return state[3]
        if action_type == "recargar":
            return 4
        return 0

    def is_goal(self, state: State):
        _, _, _, load, igneous, sediments = state
        return load == 0 and not igneous and not sediments

    def heuristic(self, state: State):
        position, battery, drill, load, igneous, sediments = state
        remaining = len(igneous) + len(sediments)

        if remaining == 0 and load == 0:
            return 0

        total_to_deposit = remaining + load
        collect_time = 2 * remaining
        deposit_time = 2 * (total_to_deposit // 2) + (total_to_deposit % 2)

        move_time = 0
        movement_battery = 0
        if remaining:
            nearest = min(_manhattan(position, point) for point in (*igneous, *sediments))
            move_time = ceil(nearest / 2)
            movement_battery = nearest

        remaining_types = set()
        if igneous:
            remaining_types.add(SAMPLE_IGNEA)
        if sediments:
            remaining_types.add(SAMPLE_SEDIMENTARIA)

        equip_time = 0
        equip_battery = 0
        if remaining_types:
            if len(remaining_types) == 1:
                required_drill = _drill_for(next(iter(remaining_types)))
                if drill != required_drill:
                    equip_time = 3
                    equip_battery = 1
            else:
                equip_time = 3
                equip_battery = 1

        battery_needed = 3 * remaining + deposit_time + equip_battery + movement_battery
        recharge_time = 4 * ceil(max(0, battery_needed - battery) / 10)
        return collect_time + deposit_time + move_time + equip_time + recharge_time


def planear_rover(
    rover_inicio=(0, 0),
    bateria_inicial=20,
    zonas_sombra=(),
    muestras_igneas=(),
    muestras_sedimentarias=(),
):
    problem = RoverProblem(
        rover_inicio=rover_inicio,
        bateria_inicial=bateria_inicial,
        zonas_sombra=zonas_sombra,
        muestras_igneas=muestras_igneas,
        muestras_sedimentarias=muestras_sedimentarias,
    )
    node = astar(problem, graph_search=True)
    return [action for action, _ in node.path()[1:]]


__all__ = ["RoverProblem", "planear_rover"]