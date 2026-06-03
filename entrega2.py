from itertools import combinations
from simpleai.search import CspProblem, backtrack

def build_camp(camp_size, habs, generators, labs, deposits, airlocks, craters):
    filas, columnas = camp_size

    modulos_hab = [f"hab_{i}" for i in range(habs)]
    modulos_gen = [f"gen_{i}" for i in range(generators)]
    modulos_lab = [f"lab_{i}" for i in range(labs)]
    modulos_dep = [f"dep_{i}" for i in range(deposits)]
    modulos_air = [f"air_{i}" for i in range(airlocks)]

    variables = modulos_hab + modulos_gen + modulos_lab + modulos_dep + modulos_air

    if not variables:
        return []

    if labs > 0 and deposits == 0:
        return None

    domains = {}
    for var in variables:
        coordenadas_validas = []
        for f in range(filas):
            for c in range(columnas):
                posicion = (f, c)
                
                if posicion in craters:
                    continue
                    
                es_borde = (f == 0 or f == filas - 1 or c == 0 or c == columnas - 1)
                
                if var.startswith("hab") and es_borde:
                    continue
                    
                if var.startswith("air") and not es_borde:
                    continue
                    
                coordenadas_validas.append(posicion)
                
        domains[var] = coordenadas_validas

    constraints = []

    def son_adyacentes(pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1]) == 1

    def no_adyacentes(variables, values):
        return not son_adyacentes(values[0], values[1])

    def posiciones_distintas(variables, values):
        return values[0] != values[1]

    for mod_A, mod_B in combinations(variables, 2):
        constraints.append(((mod_A, mod_B), posiciones_distintas))

    for gen in modulos_gen:
        for hab in modulos_hab:
            constraints.append(((gen, hab), no_adyacentes))

    for gen_A, gen_B in combinations(modulos_gen, 2):
        constraints.append(((gen_A, gen_B), no_adyacentes))

    def lab_junto_deposito(variables, values):
        pos_lab = values[0]
        for pos_dep in values[1:]:
            if son_adyacentes(pos_lab, pos_dep):
                return True
        return False

    for lab in modulos_lab:
        if modulos_dep:
            constraints.append(((lab,) + tuple(modulos_dep), lab_junto_deposito))

    def hab_con_vecino_libre(variables, values):
        pos_hab = values[0]
        vecinos = [
            (pos_hab[0] - 1, pos_hab[1]), 
            (pos_hab[0] + 1, pos_hab[1]), 
            (pos_hab[0], pos_hab[1] - 1), 
            (pos_hab[0], pos_hab[1] + 1)
        ]
        
        for pos_vecina in vecinos:
            if pos_vecina not in craters and pos_vecina not in values:
                return True
        return False

    if modulos_hab:
        constraints.append((tuple(modulos_hab), hab_con_vecino_libre))

    problem = CspProblem(variables, domains, constraints)
    solucion_csp = backtrack(problem)

    if solucion_csp is None:
        return None

    resultado = []
    for variable, posicion in solucion_csp.items():
        tipo = variable.split("_")[0] 
        resultado.append((tipo, posicion[0], posicion[1]))

    return resultado