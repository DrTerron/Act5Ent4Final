from flask import Blueprint, render_template
from flask_restx import Api, fields, Resource
from utils.database import db
from models.db_models import estimacion
import pickle
import numpy

es = Blueprint('es',__name__)

api = Api(
    es, 
    version='1.0', title=' MAESTRIA EN CIENCIA DE DATOS ',
    description='API REST Modelo de Ciencia de Datos - Entregable 4',
)


"""@es.route('/')
def home():
    return render_template('index.html')
"""
# Crear namespaces para estructurar el API REST según los distintos
# recursos que exponga el API. Para este proyecto se usa sólo un namespace de nombre
# "predicciones". 
ns = api.namespace('predicciones', description='predicciones')

# =======================================================================================
# El siguiente objeto modela un Recurso REST con los datos de entrada para crear una 
# predicción.

observacion_repr = api.model('Observacion', {
    'sepal_length': fields.Float(description="Longitud del sépalo"),
    'sepal_width': fields.Float(description="Anchura del sépalo"),
    'petal_length': fields.Float(description="Longitud del pétalo"),
    'petal_width': fields.Float(description="Anchura del pétalo"),
})

# =======================================================================================
predictive_model = pickle.load(open('simple_model.pkl','rb'))

# La siguiente línea indica que esta clase va a manejar los recursos que se encuentran en
# el URI raíz (/), y que soporta los métodos GET y POST.
@ns.route('/', methods=['GET', 'POST'])
class PredictionListAPI(Resource):
    """ Manejador del listado de predicciones.
        GET devuelve la lista de predicciones históricas
        POST agrega una nueva predicción a la lista de predicciones
    """

    # -----------------------------------------------------------------------------------
    def get(self):
        """ Maneja la solicitud GET del listado de predicciones
        """
        # La función "marshall_prediction" convierte un objeto de la base de datos de tipo
        # Prediccion en su representación en JSON.
        # Prediction.query.all() obtiene un listado de todas las predicciones de la base
        # de datos. Internamente ejecuta un "SELECT * FROM predicciones".
        # Consulta el script models.py para conocer más de este mapeo.
        # Además, consulta la documentación de SQL Alchemy para conocer los métodos 
        # disponibles para consultar la base de datos desde los modelos de Python.
        # https://flask-sqlalchemy.palletsprojects.com/en/2.x/queries/#querying-records
        return [
            marshall_prediction(prediction) for prediction in estimacion.query.all()
        ], 200

    # -----------------------------------------------------------------------------------
    # La siguiente línea de código sirve para asegurar que el método POST recibe un
    # recurso representado por la observación descrita arriba (observacion_repr).
    @ns.expect(observacion_repr)
    def post(self):
        """ Procesa un nuevo recurso para que se agregue a la lista de predicciones
        """

        # La siguiente línea convierte una representación REST de una Prediccion en
        # un Objeto Prediccion mapeado en la base de datos mediante SQL Alchemy
        prediction = estimacion(representation=api.payload)

        # Crea una observación para alimentar el modelo predicitivo, usando los
        # datos de entrada del API.
        model_data = [numpy.array([
            prediction.sepal_length, prediction.sepal_width, 
            prediction.petal_length, prediction.petal_width, 
        ])]
        prediction.predicted_tipo = str(predictive_model.predict(model_data)[0])
        print(prediction.predicted_tipo)
        # ---------------------------------------------------------------------

        # Las siguientes dos líneas de código insertan la predicción a la base
        # de datos mediante la biblioteca SQL Alchemy.
        db.session.add(prediction)
        db.session.commit()

        # Formar la respuesta de la predicción del modelo
        response_url = api.url_for(PredictionAPI, Id=prediction.Id)
        response = {
            "tipo": prediction.predicted_tipo,  # la clase que predijo el modelo
            "url": f'{api.base_url[:-1]}{response_url}',  # el URL de esta predicción
            "api_id": prediction.Id  # El identificador de la base de datos
        }
        # La siguiente línea devuelve la respuesta a la solicitud POST con los datos
        # de la nueva predicción, acompañados del código HTTP 201: Created
        return response, 201


# =======================================================================================
# La siguiente línea de código maneja las solicitudes GET del listado de predicciones 
# acompañadas de un identificador de predicción, para obtener los datos de una particular
# Si el API permite modificar predicciones particulares, aquí se debería de manejar el
# método PUT o PATCH para una predicción en particular.
@ns.route('/<int:Id>', methods=['GET'])
class PredictionAPI(Resource):
    """ Manejador de una predicción particular
    """

    # -----------------------------------------------------------------------------------
    @ns.doc({'Id': 'Identificador de la predicción'})
    def get(self, Id):
        """ Procesa las solicitudes GET de una predicción particular
            :param prediction_id: El identificador de la predicción a buscar
        """

        # Usamos la clase Prediction que mapea la tabla en la base de datos para buscar
        # la predicción que tiene el identificador que se usó como parámetro de esta
        # solicitud. Si no existe entonces se devuelve un mensaje de error 404 No encontrado
        prediction = estimacion.query.filter_by(Id=Id).first()
        if not prediction:
            return 'Id {} no existe en la base de datos'.format(Id), 404
        else:
            # Se usa la función "marshall_prediction" para convertir la predicción de la
            # base de datos a un recurso REST
            return marshall_prediction(prediction), 200


# =======================================================================================
def marshall_prediction(prediction):
    """ Función utilería para transofmrar una Predicción de la base de datos a una 
        representación de un recurso REST.
        :param prediction: La predicción a transformar
    """
    response_url = api.url_for(PredictionAPI, Id=prediction.Id)
    model_data = {
        'sepal_length': prediction.sepal_length,
        'sepal_width': prediction.sepal_width,
        'petal_length': prediction.petal_length,
        'petal_width': prediction.petal_width,
        "class": str(prediction.predicted_tipo)
    }
    response = {
        "api_id": prediction.Id,
        "url": f'{api.base_url[:-1]}{response_url}',
        "created_date": prediction.created_date.isoformat(),
        "prediction": model_data
    }
    return response

# ---------------------------------------------------------------------------------------
def trunc(number, digits):
    """ Función utilería para truncar un número a un número de dígitos
    """
    import math
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper
    