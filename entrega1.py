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

        # 1. Variables de estado claras para simplificar los 'if'
        en_ignea = posicion in muestras_igneas
        en_sedimentaria = posicion in muestras_sedimentarias
        en_sombra = posicion in zonas_sombra
        
        mochila_llena = len(mochila) == 2
        mochila_vacia = len(mochila) == 0
        faltan_muestras = (len(muestras_igneas) + len(muestras_sedimentarias)) > 0

        # 2. Acciones de Movimiento
        if bateria > 1:
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                acciones.append(("moverse", (posicion[0] + dx, posicion[1] + dy)))
                
        if bateria > 4:
            for dx, dy in [(0, 2), (0, -2), (2, 0), (-2, 0)]:
                acciones.append(("sobremarcha", (posicion[0] + dx, posicion[1] + dy)))

        # 3. Acción de Recarga
        if bateria < 20 and not en_sombra:
            acciones.append(("recargar", None))

        # 4. Acciones en zona de Muestras Ígneas
        if en_ignea and bateria > 1:
            if taladro != "termico":
                acciones.append(("equipar", "termico"))
            elif bateria > 3 and not mochila_llena:
                acciones.append(("recolectar", "ignea"))

        # 5. Acciones en zona de Muestras Sedimentarias
        if en_sedimentaria and bateria > 1:
            if taladro != "percusion":
                acciones.append(("equipar", "percusion"))
            elif bateria > 3 and not mochila_llena:
                acciones.append(("recolectar", "sedimentaria"))

        # 6. Acción de Depositar
        if not mochila_vacia and bateria > 1:
            if mochila_llena or not faltan_muestras:
                acciones.append(("depositar", None))

        return acciones




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