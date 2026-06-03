from itertools import combinations

from simpleai.search import CspProblem, backtrack


def _is_border(cell, rows, cols):
    row, col = cell
    return row == 0 or row == rows - 1 or col == 0 or col == cols - 1


def _neighbors(cell, rows, cols):
    row, col = cell
    candidates = ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
    return [
        (r, c)
        for r, c in candidates
        if 0 <= r < rows and 0 <= c < cols
    ]


def _adjacent(cell_a, cell_b):
    return abs(cell_a[0] - cell_b[0]) + abs(cell_a[1] - cell_b[1]) == 1


def _constraint_not_equal(_, values):
    return values[0] != values[1]


def _constraint_not_adjacent(_, values):
    return not _adjacent(values[0], values[1])


def _constraint_lab_adjacent_to_some_dep(_, values):
    lab_cell = values[0]
    dep_cells = values[1:]
    return any(_adjacent(lab_cell, dep_cell) for dep_cell in dep_cells)


def _constraint_hab_has_escape_factory(hab_index, craters_set, rows, cols):
    def _constraint_hab_has_escape(_, values):
        hab_cell = values[hab_index]
        occupied_cells = set(values)

        for neighbor in _neighbors(hab_cell, rows, cols):
            if neighbor in craters_set:
                continue
            if neighbor not in occupied_cells:
                return True

        return False

    return _constraint_hab_has_escape


def build_camp(camp_size, habs, generators, labs, deposits, airlocks, craters):
    """
    CSP model:
    - Variables: one variable per module instance (hab_i, gen_i, lab_i, dep_i, air_i).
    - Domains: coordinates where each module can be placed.
    - Constraints: all 8 rules requested by the assignment.
    """
    rows, cols = camp_size
    craters_set = set(craters)

    if rows <= 0 or cols <= 0:
        return None

    vars_by_type = {
        "hab": [f"hab_{i}" for i in range(habs)],
        "gen": [f"gen_{i}" for i in range(generators)],
        "lab": [f"lab_{i}" for i in range(labs)],
        "dep": [f"dep_{i}" for i in range(deposits)],
        "air": [f"air_{i}" for i in range(airlocks)],
    }

    variables = (
        vars_by_type["hab"]
        + vars_by_type["gen"]
        + vars_by_type["lab"]
        + vars_by_type["dep"]
        + vars_by_type["air"]
    )

    if not variables:
        return []

    # Rule 7 makes labs impossible without deposits.
    if labs > 0 and deposits == 0:
        return None

    all_cells = [(r, c) for r in range(rows) for c in range(cols)]
    usable_cells = [cell for cell in all_cells if cell not in craters_set]

    if len(variables) > len(usable_cells):
        return None

    border_cells = [cell for cell in usable_cells if _is_border(cell, rows, cols)]
    interior_cells = [cell for cell in usable_cells if not _is_border(cell, rows, cols)]

    if habs > len(interior_cells):
        return None
    if airlocks > len(border_cells):
        return None

    domains = {}
    for var in variables:
        if var.startswith("hab_"):
            domains[var] = interior_cells
        elif var.startswith("air_"):
            domains[var] = border_cells
        else:
            domains[var] = usable_cells

        if not domains[var]:
            return None

    constraints = []

    # 1) No overlap between modules.
    for var_a, var_b in combinations(variables, 2):
        constraints.append(((var_a, var_b), _constraint_not_equal))

    # 5) Generator cannot be adjacent to hab.
    for gen_var in vars_by_type["gen"]:
        for hab_var in vars_by_type["hab"]:
            constraints.append(((gen_var, hab_var), _constraint_not_adjacent))

    # 6) Generators cannot be adjacent to each other.
    for gen_a, gen_b in combinations(vars_by_type["gen"], 2):
        constraints.append(((gen_a, gen_b), _constraint_not_adjacent))

    # 7) Every lab adjacent to at least one deposit.
    if vars_by_type["lab"]:
        dep_scope = tuple(vars_by_type["dep"])
        for lab_var in vars_by_type["lab"]:
            constraints.append(((lab_var,) + dep_scope, _constraint_lab_adjacent_to_some_dep))

    # 8) Every hab needs at least one adjacent free (empty and non-crater) cell.
    all_scope = tuple(variables)
    for hab_var in vars_by_type["hab"]:
        hab_index = variables.index(hab_var)
        constraints.append(
            (all_scope, _constraint_hab_has_escape_factory(hab_index, craters_set, rows, cols))
        )

    problem = CspProblem(variables, domains, constraints)
    solution = backtrack(problem)

    if solution is None:
        return None

    ordered_vars = sorted(
        solution.keys(),
        key=lambda name: (name.split("_")[0], int(name.split("_")[1])),
    )

    return [
        (var_name.split("_")[0], solution[var_name][0], solution[var_name][1])
        for var_name in ordered_vars
    ]


__all__ = ["build_camp"]
