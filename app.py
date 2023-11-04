from flask import render_template, Flask
import connexion

app = Flask(__name__)
app = connexion.App(__name__, specification_dir="./")
app.add_api("swagger.yml")

@app.route("/")
def home():
    return render_template("home.html")    

if __name__ == "__main__":
    
    try:
        app.run(host="0.0.0.0", port=8000)
    
    except KeyboardInterrupt:
        app.destroy()