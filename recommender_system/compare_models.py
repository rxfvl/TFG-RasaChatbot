import os
import csv
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, ConfusionMatrixDisplay

from train_mlp import generar_datos_antibloqueo
from db_utils import get_num_temas

NUM_MUESTRAS = 10000
RESULTS_DIR = "../results"
PLOTS_DIR = os.path.join(RESULTS_DIR, "plots")
CSV_PATH = os.path.join(RESULTS_DIR, "model_comparison.csv")

def plot_correlation_matrix(X, y, num_temas):
    print("Generando matriz de correlación del dataset sintético...")
    # Crear nombres de columnas basados en generar_datos_antibloqueo
    columns = ["dias_plataforma", "interacciones", "dias_consecutivos"]
    for i in range(1, num_temas + 1):
        columns.append(f"ind_tema_{i}")
    for i in range(1, num_temas + 1):
        columns.append(f"nota_tema_{i}")
        
    df = pd.DataFrame(X, columns=columns)
    
    # Añadimos el target codificado numéricamente para ver su correlación
    df['target'] = pd.Categorical(y).codes
    
    corr = df.corr()
    plt.figure(figsize=(14, 10))
    sns.heatmap(corr, annot=False, cmap='coolwarm', fmt=".2f")
    plt.title("Matriz de Correlación de Variables del Dataset Sintético")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "dataset_correlation_matrix.png"))
    plt.close()

def main():
    print("Conectando a BD para obtener número de temas...")
    num_temas = get_num_temas()
    print(f"Generando {NUM_MUESTRAS} muestras de datos...")
    X, y = generar_datos_antibloqueo(NUM_MUESTRAS, num_temas)
    
    if not os.path.exists(PLOTS_DIR):
        os.makedirs(PLOTS_DIR)
        
    # Analizar dataset
    plot_correlation_matrix(X, y, num_temas)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    models = {
        "Decision Tree": {
            "model": DecisionTreeClassifier(random_state=42),
            "params": {
                'criterion': ['gini', 'entropy'],
                'max_depth': [None, 10, 20]
            }
        },
        "Random Forest": {
            "model": RandomForestClassifier(random_state=42),
            "params": {
                'n_estimators': [50, 100],
                'max_depth': [None, 10, 20]
            }
        },
        "MLP (Red Neuronal)": {
            "model": MLPClassifier(max_iter=1500, random_state=42),
            "params": {
                'hidden_layer_sizes': [(32,), (64, 32)],
                'activation': ['relu', 'tanh'],
                'solver': ['adam']
            }
        }
    }
    
    results = []
    
    for name, config in models.items():
        print(f"\n--- Evaluando: {name} ---")
        grid = GridSearchCV(config["model"], config["params"], cv=3, n_jobs=-1, verbose=1)
        
        t0 = time.time()
        grid.fit(X_train, y_train)
        t_fit = time.time() - t0
        
        best_model = grid.best_estimator_
        print(f"Mejores parámetros: {grid.best_params_}")
        
        t0_pred = time.time()
        y_pred = best_model.predict(X_test)
        t_pred = time.time() - t0_pred
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        print(f"Accuracy: {acc:.4f} | F1-Score: {f1:.4f} | Tiempo Entr: {t_fit:.2f}s | Tiempo Inf: {t_pred:.4f}s")
        
        results.append({
            "Modelo": name,
            "Mejores Parametros": str(grid.best_params_),
            "Tiempo Entrenamiento (s)": round(t_fit, 3),
            "Tiempo Inferencia (s)": round(t_pred, 4),
            "Accuracy": round(acc, 4),
            "Precision": round(prec, 4),
            "Recall": round(rec, 4),
            "F1_Score": round(f1, 4)
        })
        
        # Generar Matriz de Confusión para este modelo
        labels = best_model.classes_
        cm = confusion_matrix(y_test, y_pred, labels=labels)
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
        fig, ax = plt.subplots(figsize=(12, 10))
        disp.plot(ax=ax, cmap='Blues', xticks_rotation=45)
        plt.title(f'Matriz de Confusión - {name}')
        plt.tight_layout()
        safe_name = name.replace(" ", "_").replace("(", "").replace(")", "").lower()
        plt.savefig(os.path.join(PLOTS_DIR, f"confusion_matrix_{safe_name}.png"))
        plt.close()
        
    # Guardar a CSV
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
        
    df = pd.DataFrame(results)
    df.to_csv(CSV_PATH, index=False)
    print(f"\nResultados exportados a {CSV_PATH}")
    
    # Generar graficas
    # Grafica: Accuracy
    plt.figure(figsize=(8, 5))
    bars = plt.bar(df["Modelo"], df["Accuracy"], color=['#4CAF50', '#2196F3', '#FF9800'])
    plt.title("Comparativa de Precisión (Accuracy) entre Modelos")
    plt.ylim(0, 1.1)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.02, f'{yval:.4f}', ha='center', va='bottom')
    plt.savefig(os.path.join(PLOTS_DIR, "comparativa_accuracy.png"))
    plt.close()
    
    # Grafica: Recall
    plt.figure(figsize=(8, 5))
    bars = plt.bar(df["Modelo"], df["Recall"], color=['#9C27B0', '#E91E63', '#00BCD4'])
    plt.title("Comparativa de Exhaustividad (Recall) entre Modelos")
    plt.ylim(0, 1.1)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.02, f'{yval:.4f}', ha='center', va='bottom')
    plt.savefig(os.path.join(PLOTS_DIR, "comparativa_recall.png"))
    plt.close()
    
    # Grafica: F1-Score
    plt.figure(figsize=(8, 5))
    bars = plt.bar(df["Modelo"], df["F1_Score"], color=['#673AB7', '#3F51B5', '#009688'])
    plt.title("Comparativa de F1-Score entre Modelos")
    plt.ylim(0, 1.1)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.02, f'{yval:.4f}', ha='center', va='bottom')
    plt.savefig(os.path.join(PLOTS_DIR, "comparativa_f1.png"))
    plt.close()
    
    # Grafica: Tiempo de Entrenamiento
    plt.figure(figsize=(8, 5))
    bars = plt.bar(df["Modelo"], df["Tiempo Entrenamiento (s)"], color=['#4CAF50', '#2196F3', '#FF9800'])
    plt.title("Comparativa de Tiempo de Entrenamiento (GridSearch Total)")
    plt.ylabel("Segundos")
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + (max(df["Tiempo Entrenamiento (s)"]) * 0.05), f'{yval:.2f}s', ha='center', va='bottom')
    plt.savefig(os.path.join(PLOTS_DIR, "comparativa_tiempo_fit.png"))
    plt.close()
    
    # Grafica: Tiempo de Inferencia
    plt.figure(figsize=(8, 5))
    bars = plt.bar(df["Modelo"], df["Tiempo Inferencia (s)"], color=['#4CAF50', '#2196F3', '#FF9800'])
    plt.title("Comparativa de Tiempo de Inferencia (Test Set)")
    plt.ylabel("Segundos")
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + (max(df["Tiempo Inferencia (s)"]) * 0.05), f'{yval:.4f}s', ha='center', va='bottom')
    plt.savefig(os.path.join(PLOTS_DIR, "comparativa_tiempo_predict.png"))
    plt.close()
    
    print(f"¡Gráficas adicionales generadas en {PLOTS_DIR}!")

if __name__ == "__main__":
    main()
