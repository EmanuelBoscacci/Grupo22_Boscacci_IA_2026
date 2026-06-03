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
    