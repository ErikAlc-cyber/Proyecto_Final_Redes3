import connexion
from flask import render_template
from ma import ma

#Create the application instance
connex_app = connexion.App(__name__, specification_dir='./')

#read the swagger to configure the endpoints
connex_app.add_api("swagger.yml")
app = connex_app.app

@app.route("/")
def home():
    return render_template("home.html")

# The code block `if __name__ == "__main__":` is a common Python idiom that checks if the current
# script is being run as the main module.
if __name__ == "__main__":
    
    ma.init_app(app)
    app.run(port=8000, debug=True)