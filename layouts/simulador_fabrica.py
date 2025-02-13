import simpy
import random

class ParametrosSimuladorFabrica:
  def __init__(self, parametros={}):
      self.estoque_inicial = parametros.get("estoque_inicial", 2)
      self.capacidade_estoque = parametros.get("capacidade_estoque", 5)
      self.qtd_fornecedores = parametros.get("qtd_fornecedores", 1)
      self.qtd_maquinas = parametros.get("qtd_maquinas", 1)
      self.tempo_producao_min = parametros.get("tempo_producao_min", 3)
      self.tempo_producao_max = parametros.get("tempo_producao_max", 6)
      self.tempo_fornecedor_min = parametros.get("tempo_fornecedor_min", 5)
      self.tempo_fornecedor_max = parametros.get("tempo_fornecedor_max", 10)
      self.tempo_simulacao = parametros.get("tempo_simulacao", 100)

class SimuladorFabrica:
    def init(self, parametros):
      self.parametros = ParametrosSimuladorFabrica(parametros)
      self.env = simpy.Environment()
      self.estoque = simpy.Container(self.env, self.parametros.capacidade_estoque, self.parametros.estoque_inicial)
      self.pedidos = simpy.Container(self.env)
      self.producao = simpy.Resource(self.env, capacity=self.parametros.qtd_maquinas)
      self.fornecedor = simpy.Resource(self.env, capacity=self.parametros.qtd_fornecedores)
      self.qtd_fornecimentos = 0

    def produzir(self):
      while True:
          if self.estoque.level == 0:
            print("Estoque vazio. Aguardando fornecimento.")

          yield self.estoque.get(1)
          with self.producao.request() as req:
             yield req
             print(f"Produção iniciada. Estoque atual: {self.estoque.level}")
             yield self.env.timeout(random.uniform(self.parametros.tempo_producao_min, self.parametros.tempo_producao_max))
             yield self.pedidos.put(1)
             print("Produção concluída.")

    def fornecer(self):
      while True:
        with self.fornecedor.request() as req:
          yield req
          print(f"Fornecimento iniciado. Fornecedeores ativos: {self.fornecedor.count}. Capacidade: {self.fornecedor.capacity}")
          yield self.env.timeout(random.uniform(self.parametros.tempo_fornecedor_min, self.parametros.tempo_fornecedor_max))
          self.qtd_fornecimentos += 1
          yield self.estoque.put(1)
          print(f"Fornecimento recebido. Estoque atual: {self.estoque.level}")

    def simular(self):
      self.env.process(self.produzir())
      self.env.process(self.fornecer())
      self.env.run(until=self.parametros.tempo_simulacao)

    def obter_resultados(self):
       return {
          "tempo_total": self.env.now,
          "producao_total": self.pedidos.level,
          "estoque_final": self.estoque.level,
          "fornecimento_total": self.qtd_fornecimentos,
       }

    def __str__(self):
      return f"Simulação com {self.parametros.qtd_maquinas} máquinas e {self.parametros.qtd_fornecedores} fornecedores."
