import simpy
import random
import numpy as np

class ParametrosSimulatorShoe:
    def __init__(self, parametros={}):
        self.tempo_simulacao = parametros.get("tempo_simulacao", 490)
        self.media_corte = parametros.get("media_corte", 4.4)
        self.std_corte = parametros.get("std_corte", 0.2)
        self.media_costura = parametros.get("media_costura", 4.5)
        self.std_costura = parametros.get("std_costura", 0.3)
        self.tempo_setup_corte = parametros.get("tempo_setup_corte", 0.3)
        self.tempo_setup_costura = parametros.get("tempo_setup_costura", 0.2)
        self.estoque_inicial = parametros.get("estoque_inicial", 95)
        self.estoque_seg_costura = parametros.get("estoque_seg_costura", 50)

class SimulatorShoe:
    def init(self, parametros):
        self.parametros = ParametrosSimulatorShoe(parametros)
        self.env = simpy.Environment()
        self.maq_corte = simpy.Resource(self.env, capacity=1)
        self.maq_costura = simpy.Resource(self.env, capacity=1)
        self.estoque_cortado = 0
        self.estoque_total = self.parametros.estoque_inicial
        self.tempo_entrada = []
        self.tempo_saida = []
        self.tempo_util = {"corte": 0, "costura": 0}
        self.processadas = {"corte": 0, "costura": 0}
        self.tempo_espera_fila = {"corte": [], "costura": []}
        self.tamanho_fila = {"corte": [], "costura": []}

    def processo_corte(self, sapato):
        chegada_fila = self.env.now
        with self.maq_corte.request() as req:
            yield req
            espera = self.env.now - chegada_fila
            self.tempo_espera_fila["corte"].append(espera)
            self.tamanho_fila["corte"].append(len(self.maq_corte.queue))
            yield self.env.timeout(self.parametros.tempo_setup_corte)

            if self.tempo_espera_fila["corte"]:  # Verificar se há valores na fila
                fator_ajuste = max(1, 0.0075 * self.estoque_total)  # Fator multiplicador para o tempo de processamento
            else:
                fator_ajuste = 1

            tempo_proc = max(0, np.random.normal(self.parametros.media_corte, self.parametros.std_corte)*fator_ajuste)
            self.tempo_util["corte"] += tempo_proc
            yield self.env.timeout(tempo_proc)
            self.processadas["corte"] += 1
            self.estoque_cortado += 1
        self.env.process(self.processo_costura(sapato))

    def processo_costura(self, sapato):
        chegada_fila = self.env.now
        with self.maq_costura.request() as req:
            yield req
            espera = self.env.now - chegada_fila
            self.tempo_espera_fila["costura"].append(espera)
            self.tamanho_fila["costura"].append(len(self.maq_costura.queue))
            yield self.env.timeout(self.parametros.tempo_setup_costura)

            if self.tempo_espera_fila["costura"]:  # Verificar se há valores na fila
                fator_ajuste = max(1, 0.0075 * self.parametros.estoque_seg_costura)  # Fator multiplicador para o tempo de processamento
            else:
                fator_ajuste = 1

            tempo_proc = max(0, np.random.normal(self.parametros.media_costura, self.parametros.std_costura)*fator_ajuste)

            self.tempo_util["costura"] += tempo_proc
            yield self.env.timeout(tempo_proc)
            self.processadas["costura"] += 1
            self.tempo_saida.append(self.env.now)
            self.estoque_cortado -= 1

    def chegada_sapatos(self):
        intervalo_chegada = (480 / self.parametros.estoque_inicial)
        while self.estoque_total > 0:
            self.tempo_entrada.append(self.env.now)
            self.env.process(self.processo_corte(len(self.tempo_entrada)))
            self.estoque_total -= 1
            yield self.env.timeout(intervalo_chegada)

    def simular(self):
        self.env.process(self.chegada_sapatos())
        self.env.run(until=self.parametros.tempo_simulacao)

    def obter_resultados(self):
        entradas = len(self.tempo_entrada)
        saidas = len(self.tempo_saida)
        tempo_medio_sistema = np.mean(np.array(self.tempo_saida) - np.array(self.tempo_entrada[:saidas])) if saidas > 0 else 0
        tempo_ocioso_corte = self.parametros.tempo_simulacao - self.tempo_util["corte"]
        tempo_ocioso_costura = self.parametros.tempo_simulacao - self.tempo_util["costura"]
        tempo_medio_fila_corte = 0 if np.mean(self.tempo_espera_fila["corte"]) < 0.1 else round(np.mean(self.tempo_espera_fila["corte"]))
        tempo_medio_fila_costura = 0 if np.mean(self.tempo_espera_fila["costura"]) < 0.1 else round(np.mean(self.tempo_espera_fila["costura"]))
        tamanho_medio_fila_corte = np.round(np.mean(self.tamanho_fila["corte"])) if self.tamanho_fila["corte"] else 0
        tamanho_medio_fila_costura = np.round(np.mean(self.tamanho_fila["costura"])) if self.tamanho_fila["costura"] else 0
        return {
            "entradas": entradas,
            "saidas": saidas,
            "tempo_medio_sistema": tempo_medio_sistema,
            "processadas": self.processadas,
            "tempo_util": self.tempo_util,
            "tempo_ocioso": {"corte": tempo_ocioso_corte, "costura": tempo_ocioso_costura},
            "tempo_medio_fila": {"corte": tempo_medio_fila_corte, "costura": tempo_medio_fila_costura},
            "tamanho_medio_fila": {"corte": tamanho_medio_fila_corte, "costura": tamanho_medio_fila_costura},
            "estoque_final": {"cortado": self.estoque_cortado}
        }