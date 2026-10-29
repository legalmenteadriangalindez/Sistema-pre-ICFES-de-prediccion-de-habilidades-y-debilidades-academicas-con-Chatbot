from Principal.models import * 

def get_records(record:dict):
    if record:
        print(f"es es mi registro---------------{type(record)}")
        level_name = record["general_level"]
        area = record["area"]
        strong_areas = record["strong_areas"]
        weak_areas = record["weak_areas"]
        frequent_mistakes = record["frequent_mistakes"]
        level,_ = NivelAprendizaje.objects.get_or_create(nombre=level_name.capitalize(),defaults={"descripcion":"Generado desde JSON"})
    else:
        area = []
        strong_areas = []
        weak_areas = []
        frequent_mistakes = []
        level,_ = NivelAprendizaje.objects.get_or_create(nombre="basico",defaults={"descripcion":"generado por defecto"})

    return level,area,strong_areas,weak_areas,frequent_mistakes


def set_RitmoAprendizaje(nombre:str,descripcion:str):
    learning_pace,_= RitmoAprendizaje.objects.get_or_create(
    nombre=nombre,
    defaults={"descripcion":descripcion}
    )
    return learning_pace

def set_EstiloAprendizaje(nombre:str,descripcion:str):
    style,_ = EstiloAprendizaje.objects.get_or_create(
    nombre=nombre,
    defaults={"descripcion":descripcion}
    
    )
    return style

def set_PerfilPedagogico(student,ritmo,style,level):
    profile,_ = PerfilPedagogico.objects.update_or_create(
            estudiante=student,  
            defaults={
                "ritmo": ritmo,
                "estilo": style,
                "nivel": level
            }
        )
    return profile

def set_AnalisisCognitivo(student,general_level,strong_areas,weak_areas,frequent_mistakes):
    analysis,_ = AnalisisCognitivo.objects.update_or_create(
            estudiante=student,
            defaults = {
            "nivel_general":general_level,
            "areas_fuertes":", ".join(strong_areas),
            "areas_debiles":", ".join(weak_areas),
            "dudas_frecuentes":", ".join(frequent_mistakes)
            }
    )
    return analysis

       
