from flask import Flask, request
app = Flask(__name__)

employees = [
    {
        "id": 1,
        "name": "John",
        "email": "john@gmail.com",
        "department": "IT",
        "position": "Developer",
        "salary": 50000
    }
]

@app.route("/health")
def health():
    return "healthy"

@app.route("/employees", methods=["GET"])
def get_employees():
    return employees

@app.route("/employees", methods=["POST"])
def create_employee():
    data = request.get_json()

    new_employee = {
        "id": len(employees) + 1,
        "name": data["name"],
        "email": data["email"],
        "department": data["department"],
        "position": data["position"],
        "salary": data["salary"]
    }

    employees.append(new_employee)

    return new_employee, 201

@app.route("/employees/<int:id>", methods=["GET"])
def get_employee(id):
    for employee in employees:
        if employee["id"] == id:
            return employee

    return {"error": "Employee not found"}, 404

@app.route("/employees/<int:id>", methods=["PUT"])
def update_employee(id):
    data = request.get_json()

    for employee in employees:
        if employee["id"] == id:
            employee["name"] = data["name"]
            employee["email"] = data["email"]
            employee["department"] = data["department"]
            employee["position"] = data["position"]
            employee["salary"] = data["salary"]

            return employee

    return {"error": "Employee not found"}, 404

@app.route("/employees/<int:id>", methods=["DELETE"])
def delete_employee(id):
    for employee in employees:
        if employee["id"] == id:
            employees.remove(employee)
            return {"message": "Employee deleted"}

    return {"error": "Employee not found"}, 404

if __name__ == "__main__":
    app.run()