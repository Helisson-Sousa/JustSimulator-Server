from flask import Flask, jsonify, request
from layouts.simulator_shoe import SimulatorShoe
from layouts.simulator_car import SimulatorCar

def create_app():
  app = Flask(__name__)

  # Rota raiz para teste
  @app.route('/')
  def home():
      return "Bem-vindo à Simulação Just-In-Time!"

  '''
  Executa uma simulação com os parâmetros fornecidos
  A aplicação já possui um simulador para cada layout, e o layout é fornecido no corpo da requisição
  O corpo da requisição deve ser um JSON com os parâmetros da simulação
  '''
  @app.route('/simular', methods=['POST'])
  def simular():
    data = request.get_json()
    print("Dados recebidos:", data)

    
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
    case 'shoe':
      return SimulatorShoe()
    case 'car':
      return SimulatorCar()
    case _:
      raise ValueError('Layout não encontrado')
     
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)