import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Employee


# GET all employees or POST a new employee
@csrf_exempt
def employees(request):

    # Return all employees from the database
    if request.method == "GET":
        all_employees = list(
            Employee.objects.values().order_by("id")
        )
        return JsonResponse(all_employees, safe=False)

    # Create a new employee
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON"},
                status=400
            )

        # Check that all required fields are provided
        required_fields = [
            "name",
            "email",
            "department",
            "position",
            "salary"
        ]

        for field in required_fields:
            if field not in data:
                return JsonResponse(
                    {"error": f"Missing field: {field}"},
                    status=400
                )

        # Save the new employee to MySQL through Django ORM
        employee = Employee.objects.create(
            name=data["name"],
            email=data["email"],
            department=data["department"],
            position=data["position"],
            salary=data["salary"]
        )

        return JsonResponse({
            "id": employee.id,
            "name": employee.name,
            "email": employee.email,
            "department": employee.department,
            "position": employee.position,
            "salary": employee.salary
        }, status=201)

    return JsonResponse(
        {"error": "Method not allowed"},
        status=405
    )


# GET, PUT or DELETE one employee by ID
@csrf_exempt
def employee_detail(request, id):

    # Find the employee in the database
    try:
        employee = Employee.objects.get(id=id)
    except Employee.DoesNotExist:
        return JsonResponse(
            {"error": "Employee not found"},
            status=404
        )

    # Return one employee
    if request.method == "GET":
        return JsonResponse({
            "id": employee.id,
            "name": employee.name,
            "email": employee.email,
            "department": employee.department,
            "position": employee.position,
            "salary": employee.salary
        })

    # Update an existing employee
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON"},
                status=400
            )

        required_fields = [
            "name",
            "email",
            "department",
            "position",
            "salary"
        ]

        for field in required_fields:
            if field not in data:
                return JsonResponse(
                    {"error": f"Missing field: {field}"},
                    status=400
                )

        employee.name = data["name"]
        employee.email = data["email"]
        employee.department = data["department"]
        employee.position = data["position"]
        employee.salary = data["salary"]

        employee.save()

        return JsonResponse({
            "id": employee.id,
            "name": employee.name,
            "email": employee.email,
            "department": employee.department,
            "position": employee.position,
            "salary": employee.salary
        })

    # Delete an employee
    if request.method == "DELETE":
        employee.delete()
        return JsonResponse(
            {"message": "Employee deleted"}
        )

    return JsonResponse(
        {"error": "Method not allowed"},
        status=405
    )


# Health check for Docker/Kubernetes later
def health(request):
    return HttpResponse("healthy")