import numpy as np
import random
import joblib
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import os

NUM_MUESTRAS = 10000
NUM_TEMAS = 6
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "recommender_mlp.pkl")

def generar_datos_antibloqueo(n_muestras):
    X = []
    y = []
    
    # Dividimos en 3 grupos:
    # 20% Éxito total (Examen Global)
    # 20% Terminaron todo pero suspendieron (Fuerza a mirar las notas)
    # 60% Progreso normal y aleatorio
    grupo_exito = int(n_muestras * 0.20)
    grupo_fallo_final = int(n_muestras * 0.20)
    grupo_normal = n_muestras - grupo_exito - grupo_fallo_final
    
    # 1. Éxito Total (Examen Global)
    for _ in range(grupo_exito):
        indicadores = [1] * NUM_TEMAS
        notas = [round(random.uniform(6.0, 10.0), 2) for _ in range(NUM_TEMAS)]
        dias, inter, conc = random.randint(15, 40), random.randint(150, 400), random.randint(30, 80)
        X.append([dias, inter, conc] + indicadores + notas)
        y.append("hacer_examen_global")
        
    # 2. Terminaron todo, pero suspendieron (Contraejemplos)
    for _ in range(grupo_fallo_final):
        indicadores = [1] * NUM_TEMAS
        notas = [round(random.uniform(0.0, 10.0), 2) for _ in range(NUM_TEMAS)]
        
        # Forzamos que al menos una nota sea menor a 6.0 para que NO sea examen global
        idx_suspenso = random.randint(0, NUM_TEMAS - 1)
        notas[idx_suspenso] = round(random.uniform(0.0, 5.9), 2)
        
        dias, inter, conc = random.randint(15, 40), random.randint(150, 400), random.randint(30, 80)
        X.append([dias, inter, conc] + indicadores + notas)
        
        # Buscamos la primera nota suspendida para asignar el repaso
        min_tema_idx, min_nota = min(enumerate(notas), key=lambda x: x[1])
        y.append(f"repasar_tema_{min_tema_idx + 1}")

    # 3. Resto de casos aleatorios (Avanzar o repasar a mitad de curso)
    for _ in range(grupo_normal):
        # Elegimos cuántos temas al azar se han intentado (0 a 5, para no pisar los grupos de arriba)
        num_intentados = random.randint(0, NUM_TEMAS - 1)
        indicadores = [0] * NUM_TEMAS
        indices_activos = random.sample(range(NUM_TEMAS), num_intentados)
        for idx in indices_activos:
            indicadores[idx] = 1
            
        notas = [round(random.uniform(0.0, 10.0), 2) if ind == 1 else 0.0 for ind in indicadores]
        dias, inter, conc = random.randint(1, 15), random.randint(10, 150), random.randint(5, 30)
        
        target = "avanzar_siguiente_tema"
        if num_intentados > 0:
            temas_cursados = [(idx + 1, notas[idx]) for idx in range(NUM_TEMAS) if indicadores[idx] == 1]
            min_tema_idx, min_nota = min(temas_cursados, key=lambda x: x[1])
            if min_nota < 6.0:
                target = f"repasar_tema_{min_tema_idx}"
                
        X.append([dias, inter, conc] + indicadores + notas)
        y.append(target)
        
    # Mezclamos bien los datos
    datos_combinados = list(zip(X, y))
    random.shuffle(datos_combinados)
    X, y = zip(*datos_combinados)
        
    return np.array(X), np.array(y)

if __name__ == "__main__":
    print("Generando datos con contraejemplos...")
    X, y = generar_datos_antibloqueo(NUM_MUESTRAS)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Entrenando MLPClassifier (Este sí es el definitivo)...")
    clf = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=1500, random_state=42)
    clf.fit(X_train, y_train)
    
    print("Evaluando el modelo...")
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred, zero_division=0))
    
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        
    joblib.dump(clf, MODEL_PATH)
    print(f"Modelo guardado exitosamente en: {MODEL_PATH}")