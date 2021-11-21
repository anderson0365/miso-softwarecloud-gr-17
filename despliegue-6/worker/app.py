from flaskr import create_app
from flask_restful import Api
from .views import ViewSignUp, ViewLogIn, ViewTasks, ViewTask, ViewFiles, ViewUser
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from .config import config


app = create_app(config)
app_context = app.app_context()
app_context.push()

cors = CORS(app)

api = Api(app)

api.add_resource(ViewSignUp,"/api/auth/signup")
api.add_resource(ViewLogIn,"/api/auth/login")
api.add_resource(ViewTasks,"/api/tasks")
api.add_resource(ViewTask,"/api/tasks/<int:id_task>")
api.add_resource(ViewFiles, "/api/files/<filename>")
api.add_resource(ViewUser, "/api/user")

jwt = JWTManager(app)

