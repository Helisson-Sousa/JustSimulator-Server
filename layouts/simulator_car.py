import simpy
import random
import numpy as np
from collections import deque

class ParametrosSimulatorCar:
  def __init__(self, parametros={}):
      self.tempo_simulacao = parametros.get("tempo_simulacao", 28800)
      self.media_injetora = parametros.get("media_injetora", 44.08)
      self.std_injetora = parametros.get("std_injetora", 0.87)
      self.media_flamagem = parametros.get("media_flamagem", 34.8)
      self.std_flamagem = parametros.get("std_flamagem", 0.97)
      self.media_colagem = parametros.get("media_colagem", 82.3)
      self.std_colagem = parametros.get("std_colagem", 1.1)
      self.tempo_setup_injetora = parametros.get("tempo_setup_injetora", 2.4)
      self.tempo_setup_flamagem = parametros.get("tempo_setup_flamagem", 3.84)
      self.tempo_setup_colagem = parametros.get("tempo_setup_colagem", 3.06)
      self.estoque_inicial = parametros.get("estoque_inicial", 100)
      self.estoque_seg_flamagem = parametros.get("estoque_seg_flamagem", 50)
      self.media_acabamento = parametros.get("media_acabamento", 50)

class SimulatorCar:
    def init(self, parametros):
      self.parametros = ParametrosSimulatorCar(parametros)
      self.env = simpy.Environment()
      self.fila_acabamento = deque()
      self.container1 = deque()
      self.container2 = deque()
      self.tempo_fluxo = {}
      self.contagem_processos = {"injetora": 0, "acabamento": 0, "flamagem": 0, "colagem": 0}
      self.uso_processos = {"injetora": 0, "acabamento": 0, "flamagem": 0, "colagem": 0}
      self.total_pecas = {"entrada": 0, "saida": 0}
      self.estatisticas_filas = {"acabamento": [], "flamagem": [], "colagem": [],
                                "tempo_espera_acabamento": [], "tempo_espera_flamagem": [], "tempo_espera_colagem": []}
      self.processo_acabamento = simpy.Resource(self.env, capacity=1)
      self.processo_flamagem = simpy.Resource(self.env, capacity=1)
      self.processo_colagem = simpy.Resource(self.env, capacity=1)

    def injetora(self):
        indice_peca = 1
        while True:
            self.total_pecas['entrada'] += 1
            self.tempo_fluxo[indice_peca] = {'entrada': self.env.now, 'saida': None}
            yield self.env.timeout(self.parametros.tempo_setup_injetora)
            tempo_injetora = max(0, random.normalvariate(self.parametros.media_injetora, self.parametros.std_injetora))
            self.uso_processos['injetora'] += tempo_injetora
            yield self.env.timeout(tempo_injetora)
            self.fila_acabamento.append((indice_peca, self.env.now))
            self.contagem_processos['injetora'] += 1
            indice_peca += 1

    def acabamento_inj(self):
        while True:
            yield self.env.timeout(0.1)
            self.estatisticas_filas['acabamento'].append(len(self.fila_acabamento))
            if not self.fila_acabamento:  # Verifica se a fila está vazia
                continue
            peca, chegada_fila = self.fila_acabamento.popleft()
            tempo_espera = self.env.now - chegada_fila
            self.estatisticas_filas['tempo_espera_acabamento'].append(tempo_espera)
            with self.processo_acabamento.request() as request:
                yield request
                tempo_acabamento = self.parametros.media_acabamento
                self.uso_processos['acabamento'] += tempo_acabamento
                yield self.env.timeout(tempo_acabamento)
                self.container1.append((peca, self.env.now))
                self.contagem_processos['acabamento'] += 1

    def processamento_flamagem(self):
        while True:
            yield self.env.timeout(0.1)
            self.estatisticas_filas['flamagem'].append(len(self.container1))
            if self.container1:
                peca, chegada_fila = self.container1.popleft()
                tempo_espera = self.env.now - chegada_fila
                self.estatisticas_filas['tempo_espera_flamagem'].append(tempo_espera)
                yield self.env.timeout(random.normalvariate(self.parametros.media_flamagem, self.parametros.std_flamagem))
                with self.processo_flamagem.request() as request:
                    yield request
                    yield self.env.timeout(self.parametros.tempo_setup_flamagem)

                    if self.estatisticas_filas["flamagem"]:  # Verificar se há valores na fila
                        fator_ajuste = max(1, 0.0075 * self.parametros.estoque_seg_flamagem)
                    else:
                        fator_ajuste = 1

                    tempo_flamagem = max(0, random.normalvariate(self.parametros.media_flamagem, self.parametros.std_flamagem)*fator_ajuste)
                    self.uso_processos['flamagem'] += tempo_flamagem
                    yield self.env.timeout(tempo_flamagem)
                    if len(self.container2) < max(1, self.parametros.estoque_seg_flamagem):
                        self.container2.append((peca, self.env.now))
                        self.contagem_processos['flamagem'] += 1

    def processamento_colagem(self):
        while True:
            yield self.env.timeout(0.1)
            self.estatisticas_filas['colagem'].append(len(self.container2))
            if self.container2:
                peca, chegada_fila = self.container2.popleft()
                tempo_espera = self.env.now - chegada_fila
                self.estatisticas_filas['tempo_espera_colagem'].append(tempo_espera)
                with self.processo_colagem.request() as request:
                    yield request
                    yield self.env.timeout(self.parametros.tempo_setup_colagem)
                    tempo_colagem = max(0, random.normalvariate(self.parametros.media_colagem, self.parametros.std_colagem))
                    self.uso_processos['colagem'] += tempo_colagem
                    yield self.env.timeout(tempo_colagem)
                    self.tempo_fluxo[peca]['saida'] = self.env.now
                    self.contagem_processos['colagem'] += 1
                    self.total_pecas['saida'] += 1

    def simular(self):
        self.env.process(self.injetora())
        self.env.process(self.acabamento_inj())
        self.env.process(self.processamento_flamagem())
        self.env.process(self.processamento_colagem())
        self.env.run(until=self.parametros.tempo_simulacao)

    def obter_resultados(self):
        # Calculando tempos totais
        tempos_totais = [(dados['saida'] - dados['entrada']) / 60 for dados in self.tempo_fluxo.values() if dados['saida'] is not None]
        tempo_medio_ciclo = sum(tempos_totais) / len(tempos_totais) if tempos_totais else 0

        print("tempos_saida", self.tempo_fluxo)

        # Calculando tempo total útil e ocioso por processo
        tempo_total_uso = {proc: self.uso_processos[proc] / 60 for proc in self.uso_processos}
        tempo_ocioso = {proc: (self.parametros.tempo_simulacao - uso) / 60 for proc, uso in self.uso_processos.items()}

        # Calculando a média de tempo nas filas
        media_fila = {proc: round(sum(self.estatisticas_filas[proc]) / len(self.estatisticas_filas[proc])) if self.estatisticas_filas[proc] else 0 for proc in ['acabamento', 'flamagem', 'colagem']}
        tempo_espera_medio = {proc: (sum(self.estatisticas_filas[f'tempo_espera_{proc}']) / len(self.estatisticas_filas[f'tempo_espera_{proc}'])) / 60 if self.estatisticas_filas[f'tempo_espera_{proc}'] else 0 for proc in ['acabamento', 'flamagem', 'colagem']}

        # Resultados
        return {
            "quantidade_entradas": self.total_pecas['entrada'],
            "quantidade_saidas": self.total_pecas['saida'],
            "tempo_medio_ciclo": tempo_medio_ciclo,
            "quantidade_processadas": self.contagem_processos,
            "tempo_util_ocioso": {proc: {"util": tempo_total_uso[proc], "ocioso": tempo_ocioso[proc]} for proc in self.uso_processos},
            "tempo_espera_filas": tempo_espera_medio,
            "tamanho_fila": media_fila
        }