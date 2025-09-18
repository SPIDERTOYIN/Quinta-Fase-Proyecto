from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from models import db, Usuario, Empleado, Asistencia, Sucursal

app = Flask(__name__)
app.secret_key = "clave_super_secreta"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///asistencia.db"
db.init_app(app)

with app.app_context():
    db.create_all()
    
# ----------- LOGIN -------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = Usuario.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["rol"] = user.rol
            return redirect(url_for("dashboard"))
        return "Credenciales incorrectas"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ----------- DASHBOARD -------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = Usuario.query.get(session["user_id"])
    if user.rol == "dueno":
        sucursales = Sucursal.query.all()
    else:
        sucursales = [user.sucursal]

    return render_template("dashboard.html", usuario=user, sucursales=sucursales)

# ----------- API PARA ESP32 -------------
@app.route("/api/asistencia", methods=["POST"])
def api_asistencia():
    data = request.json
    empleado = Empleado.query.filter_by(
        huella_id=data["huella_id"],
        sucursal_id=data["sucursal_id"]
    ).first()

    if not empleado:
        return jsonify({"status": "error", "msg": "Empleado no encontrado"}), 404

    asistencia = Asistencia(empleado=empleado)
    db.session.add(asistencia)
    db.session.commit()

    return jsonify({"status": "ok", "empleado": empleado.nombre})

# ----------- VISTA SUCURSAL -------------
@app.route("/sucursal/<int:id>")
def ver_sucursal(id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = Usuario.query.get(session["user_id"])
    sucursal = Sucursal.query.get(id)

    if user.rol == "admin" and user.sucursal_id != sucursal.id:
        return "Acceso denegado"

    return render_template("sucursal.html", sucursal=sucursal)

if __name__ == "__main__":
    app.run(debug=True)
