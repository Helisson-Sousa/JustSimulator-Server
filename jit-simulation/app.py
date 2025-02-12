from flask import Flask, jsonify, request
from layouts.simulador_fabrica import SimuladorFabrica

def create_app():
  app = Flask(__name__)

  '''
  Executa uma simulação com os parâmetros fornecidos
  A aplicação já possui um simulador para cada layout, e o layout é fornecido no corpo da requisição
  O corpo da requisição deve ser um JSON com os parâmetros da simulação
  '''
  @app.route('/simular', methods=['POST'])
  def simular():
    data = request.get_json()
    layout_name = data.get('layout')
    parametros = data.get('parametros')

    simulator = get_simulator(layout_name)
    simulator.init(parametros)
    simulator.simular()
    resultado = simulator.obter_resultados()

    return jsonify(resultado), 200

  return app

def get_simulator(name):
  match name:
    case 'fabrica':
      return SimuladorFabrica()
    case _:
      raise ValueError('Layout não encontrado')
