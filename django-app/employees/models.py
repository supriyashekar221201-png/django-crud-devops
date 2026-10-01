from django.db import models


class Employee(models.Model):
    
    # Employee name
    name = models.CharField(max_length=100)

    # Employee email address
    email = models.EmailField()

    # Department where the employee works
    department = models.CharField(max_length=100)

    # Employee job position
    position = models.CharField(max_length=100)

    # Employee salary
    salary = models.IntegerField()