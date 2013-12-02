from django.db import models

class User(models.Model):
    wechatnumber = models.CharField(max_length = 50)
    name = models.CharField(max_length = 50)
    password = models.CharField(max_length = 30)
    last_oper = models.IntegerField()

class Question(models.Model):
    askname = models.CharField(max_length = 50)
    content = models.CharField(max_length = 100)
    category = models.CharField(max_length = 30)
    state = models.IntegerField()
    answer = models.CharField(max_length = 100)
    answername = models.CharField(max_length = 50)
