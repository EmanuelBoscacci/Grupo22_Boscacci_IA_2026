from simpleai.search import (
    SearchProblem,
    astar,
)
from simpleai.search.viewers import BaseViewer, WebViewer

class Rover(SearchProblem):
    def __init__(self, initial_state):
        super().__init__(initial_state)
    def actions(self, state):
        (
            posicion,
            bateria,
            zonas_sombra,
            muestras_igneas,
            muestras_sedimentarias,
            taladro,
            mochila,
        ) = state

        acciones = []

 
        en_ignea = posicion in muestras_igneas
        en_sedimentaria = posicion in muestras_sedimentarias
        en_sombra = posicion in zonas_sombra
        
        mochila_llena = len(mochila) == 2
        mochila_vacia = len(mochila) == 0
        faltan_muestras = (len(muestras_igneas) + len(muestras_sedimentarias)) > 0

 
        if bateria > 1:
            for pos_en_X, pos_en_Y in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                acciones.append(("moverse", (posicion[0] + pos_en_X, posicion[1] + pos_en_Y)))
                
        if bateria > 4:
            for pos_en_X, pos_en_Y in [(0, 2), (0, -2), (2, 0), (-2, 0)]:
                acciones.append(("sobremarcha", (posicion[0] + pos_en_X, posicion[1] + pos_en_Y)))

 
        if bateria < 20 and not en_sombra:
            acciones.append(("recargar", None))

        if en_ignea and bateria > 1:
            if taladro != "termico":
                acciones.append(("equipar", "termico"))
            elif bateria > 3 and not mochila_llena:
                acciones.append(("recolectar", "ignea"))

        if en_sedimentaria and bateria > 1:
            if taladro != "percusion":
                acciones.append(("equipar", "percusion"))
            elif bateria > 3 and not mochila_llena:
                acciones.append(("recolectar", "sedimentaria"))

        if not mochila_vacia and bateria > 1:
            if mochila_llena or not faltan_muestras:
                acciones.append(("depositar", None))

        return acciones
    
    def cost(self, state1, action, state2):
        tipo_accion = action[0]
        
        if tipo_accion in ("moverse", "sobremarcha"):
            return 1 
            
        elif tipo_accion == "recolectar":
            return 2
            
        elif tipo_accion == "equipar":
            return 3
            
        elif tipo_accion == "recargar":
            return 4
            
        elif tipo_accion == "depositar":

            muestras_almacenadas = state1[6]
            return len(muestras_almacenadas)   
        return 0
    
    def heuristic(self, state):
        (
            posicion,
            bateria,
            zonas_sombra,
            muestras_igneas,
            muestras_sedimentarias,
            taladro,
            mochila,
        ) = state

        muestras_restantes = muestras_igneas + muestras_sedimentarias
        
        if not muestras_restantes:
            return len(mochila)

        distancia_minima = min(
            abs(posicion[0] - m[0]) + abs(posicion[1] - m[1])
            for m in muestras_restantes
        )
        
        movimientos = int(max(distancia_minima / 2.0, 1.3 * distancia_minima - 0.4 * bateria))
        tiempo_base = 3 * len(muestras_restantes)
        tiempo_deposito = len(mochila)

        costo_taladro = 0
        if taladro is None: 
            costo_taladro = 3
        elif taladro == "termico" and muestras_sedimentarias:
            costo_taladro = 3
        elif taladro == "percusion" and muestras_igneas:
            costo_taladro = 3

        return movimientos + tiempo_base + tiempo_deposito + costo_taladro
        
    def result(self, state, action):
        (
            posicion,
            bateria,
            zonas_sombra,
            muestras_igneas,
            muestras_sedimentarias,
            taladro,
            mochila,
        ) = state

        tipo_accion, parametro = action
        
        muestras_igneas = list(muestras_igneas)
        muestras_sedimentarias = list(muestras_sedimentarias)
        mochila = list(mochila)

        if tipo_accion == "sobremarcha":
            bateria -= 4
            posicion = parametro
            
        elif tipo_accion == "moverse":
            bateria -= 1
            posicion = parametro
            
        elif tipo_accion == "recolectar":
            bateria -= 3
            mochila.append(parametro)
            if parametro == "ignea":
                muestras_igneas.remove(posicion)
            elif parametro == "sedimentaria":
                muestras_sedimentarias.remove(posicion)
                
        elif tipo_accion == "depositar":
            bateria -= 1
            mochila = []
            
        elif tipo_accion == "equipar":
            bateria -= 1
            taladro = parametro
            
        elif tipo_accion == "recargar":
            bateria = min(20, bateria + 10)

        return (
            posicion,
            bateria,
            zonas_sombra,
            tuple(muestras_igneas),
            tuple(muestras_sedimentarias),
            taladro,
            tuple(mochila),
        )
        
    def is_goal(self, state):
        return len(state[3]) == 0 and len(state[4]) == 0 and len(state[6]) == 0



def planear_rover(rover_inicio, bateria_inicial, zonas_sombra, muestras_igneas, muestras_sedimentarias):
    estado_inicial = (
        rover_inicio,
        bateria_inicial,
        tuple(zonas_sombra),
        tuple(muestras_igneas),
        tuple(muestras_sedimentarias),
        "ninguno", #Taladro
        tuple(), #Muestras almacenadas
    )

    problema = Rover(estado_inicial)

    #viewer = WebViewer() # BaseViewer() para consola. IMPORTANTE: DESACTIVAR AL ENTREGAR
    resultado = astar(problema, graph_search=True) #, viewer=viewer)
    acciones = [accion for accion, estado in resultado.path() if accion is not None] #(problema.actions(estado_inicial))
    
    return acciones