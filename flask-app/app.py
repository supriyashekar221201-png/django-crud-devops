# Import Flask to create the web application and request to read incoming data
from flask import Flask, request

# Creating the Flask application
app = Flask(__name__)

# Store initial employee data in memory
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

next_id = 2            # Store the ID that will be assigned to the next employee

# Health endpoint used to check whether the application is running

@app.route("/health")
def health():
    return "healthy"

# GET all employees
@app.route("/employees", methods=["GET"])
def get_employees():
    return employees

# POST a new employee
@app.route("/employees", methods=["POST"])
def create_employee():
    global next_id              # Allow the function to update the global next_id variable

    data = request.get_json()                   # Read JSON data sent by the client

    # Define the fields that every employee must provide
    required = ["name", "email", "department", "position", "salary"]

    # Check whether any required field is missing
    for field in required:
        if field not in data:
            return {"error": f"Missing field: {field}"}, 400
       
    # Create a new employee using the received data
    new_employee = {
        "id": next_id,
        "name": data["name"],
        "email": data["email"],
        "department": data["department"],
        "position": data["position"],
        "salary": data["salary"]
    }

    # Add the new employee to the list
    employees.append(new_employee)
    
    # Increase the ID for the next employee
    next_id += 1

    # Return the created employee with HTTP 201
    return new_employee, 201

# GET one employee using its ID
@app.route("/employees/<int:id>", methods=["GET"])
def get_employee(id):
    for employee in employees:
        if employee["id"] == id:
            return employee
    # Return 404 if the employee does not exist
    return {"error": "Employee not found"}, 404

# PUT to update an existing employee
@app.route("/employees/<int:id>", methods=["PUT"])
def update_employee(id):
    data = request.get_json()

    for employee in employees:
        if employee["id"] == id:
         # Return the updated employee
            employee["name"] = data["name"]
            employee["email"] = data["email"]
            employee["department"] = data["department"]
            employee["position"] = data["position"]
            employee["salary"] = data["salary"]
            
            # Return the updated employee
            return employee
    
    # Return 404 if the employee does not exist
    return {"error": "Employee not found"}, 404

# DELETE an employee using its ID
@app.route("/employees/<int:id>", methods=["DELETE"])
def delete_employee(id):
        # Search for the employee with the requested ID
    for employee in employees:
        if employee["id"] == id:
            # Remove the employee from the list
            employees.remove(employee)
         # Confirm that the employee was deleted
            return {"message": "Employee deleted"}
 # Confirm that the employee was deleted
    return {"error": "Employee not found"}, 404
# Run the Flask application when this file is executed directly
if __name__ == "__main__":
    app.run()