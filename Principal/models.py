from django.db import models

from django.contrib.auth.models import User

# Create your models here.

class QuizState(models.Model):
    
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="quiz_sessions")
    materia = models.CharField(max_length=255)

    preguntas = models.JSONField(default=list)
    tematicas_recomendadas = models.JSONField(default=list)
    historial = models.JSONField(default=list)
    
    status = models.CharField(
        max_length=20,
        default="pending",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)