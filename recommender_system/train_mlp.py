import numpy as np
import random
import joblib
import os
import csv
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report
from db_utils import get_num_temas

NUM_MUESTRAS = 10000
MODEL_DIR = "../models"
MODEL_PATH = os.path.join(MODEL_DIR, "recommender_mlp.pkl")
RESULTS_DIR = "../results"
RESULTS_PATH = os.path.join(RESULTS_DIR, "resultados_gridsearch.csv")

def generar_datos_antibloqueo(n_muestras, num_temas):
    X = []
    y = []
    
    grupo_exito = int(n_muestras * 0.20)
    grupo_fallo_final = int(n_muestras * 0.20)
    grupo_normal = n_muestras - grupo_exito - grupo_fallo_final
    
    # 1. Éxito Total (Examen Global)
    for _ in range(grupo_exito):
        indicadores = [1] * num_temas
        notas = [round(random.uniform(6.0, 10.0), 2) for _ in range(num_temas)]
        dias, inter, conc = random.randint(15, 40), random.randint(150, 400), random.randint(30, 80)
        X.append([dias, inter, conc] + indicadores + notas)
        y.append("hacer_examen_global")
        
    # 2. Terminaron todo, pero suspendieron (Contraejemplos)
    for _ in range(grupo_fallo_final):
        indicadores = [1] * num_temas
        notas = [round(random.uniform(0.0, 10.0), 2) for _ in range(num_temas)]
        
        idx_suspenso = random.randint(0, num_temas - 1)
        notas[idx_suspenso] = round(random.uniform(0.0, 5.9), 2)
        
        dias, inter, conc = random.randint(15, 40), random.randint(150, 400), random.randint(30, 80)
        X.append([dias, inter, conc] + indicadores + notas)
        
        min_tema_idx, min_nota = min(enumerate(notas), key=lambda x: x[1])
        y.append(f"repasar_tema_{min_tema_idx + 1}")

    # 3. Resto de casos aleatorios (Avanzar o repasar a mitad de curso)
    for _ in range(grupo_normal):
        num_intentados = random.randint(0, num_temas - 1)
        indicadores = [0] * num_temas
        indices_activos = random.sample(range(num_temas), num_intentados)
        for idx in indices_activos:
            indicadores[idx] = 1
            
        notas = [round(random.uniform(0.0, 10.0), 2) if ind == 1 else 0.0 for ind in indicadores]
        dias, inter, conc = random.randint(1, 15), random.randint(10, 150), random.randint(5, 30)
        
        target = "avanzar_siguiente_tema"
        if num_intentados > 0:
            temas_cursados = [(idx + 1, notas[idx]) for idx in range(num_temas) if indicadores[idx] == 1]
            min_tema_idx, min_nota = min(temas_cursados, key=lambda x: x[1])
            if min_nota < 6.0:
                target = f"repasar_tema_{min_tema_idx}"
                
        X.append([dias, inter, conc] + indicadores + notas)
        y.append(target)
        
    datos_combinados = list(zip(X, y))
    random.shuffle(datos_combinados)
    X, y = zip(*datos_combinados)
        
    return np.array(X), np.array(y)

if __name__ == "__main__":
    print("Conectando a BD para obtener número de temas...")
    num_temas = get_num_temas()
    print(f"Detectados {num_temas} temas en la base de datos.")
    
    print("Generando datos de entrenamiento con contraejemplos...")
    X, y = generar_datos_antibloqueo(NUM_MUESTRAS, num_temas)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Iniciando GridSearch de Hiperparámetros...")
    # Definir espacio de búsqueda
    param_grid = {
        'hidden_layer_sizes': [(32,), (32, 16), (64, 32)],
        'activation': ['relu', 'tanh'],
        'solver': ['adam', 'sgd'],
        'alpha': [0.0001, 0.01]
    }
    
    base_clf = MLPClassifier(max_iter=1500, random_state=42)
    
    # 3-fold cross validation para que no sea excesivamente lento
    grid_search = GridSearchCV(base_clf, param_grid, cv=3, n_jobs=-1, verbose=2)
    
    grid_search.fit(X_train, y_train)
    
    print("\n--- Resultados del GridSearch ---")
    print(f"Mejores Parámetros: {grid_search.best_params_}")
    print(f"Mejor Score (CV): {grid_search.best_score_:.4f}")
    
    # Evaluar modelo final
    best_clf = grid_search.best_estimator_
    print("\nEvaluando el modelo final con test set...")
    y_pred = best_clf.predict(X_test)
    print(classification_report(y_test, y_pred, zero_division=0))
    
    # Guardar modelo
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
    joblib.dump(best_clf, MODEL_PATH)
    print(f"Modelo guardado exitosamente en: {MODEL_PATH}")
    
    # Guardar resultados CV en CSV
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
        
    print(f"\nExportando detalles del GridSearchCV a {RESULTS_PATH}...")
    cv_results = grid_search.cv_results_
    
    with open(RESULTS_PATH, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Cabecera
        headers = ['rank_test_score', 'mean_test_score', 'std_test_score', 'mean_fit_time']
        param_keys = list(param_grid.keys())
        headers.extend(param_keys)
        writer.writerow(headers)
        
        # Filas
        for i in range(len(cv_results['params'])):
            row = [
                cv_results['rank_test_score'][i],
                cv_results['mean_test_score'][i],
                cv_results['std_test_score'][i],
                cv_results['mean_fit_time'][i]
            ]
            for key in param_keys:
                row.append(cv_results['params'][i][key])
            writer.writerow(row)
            
    print("¡Análisis de hiperparámetros y entrenamiento completados con éxito!")
