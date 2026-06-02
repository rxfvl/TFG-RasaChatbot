import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import joblib
import os
from train_mlp import generar_datos_antibloqueo
from db_utils import get_num_temas

RESULTS_CSV = "../results/resultados_gridsearch.csv"
MODEL_PATH = "../models/recommender_mlp.pkl"
PLOTS_DIR = "../results/plots"

def plot_gridsearch_results():
    print("Generando gráficas comparativas del GridSearch...")
    df = pd.read_csv(RESULTS_CSV)
    
    # Gráfica 1: Puntuación Media por Solver
    plt.figure(figsize=(8, 5))
    df.boxplot(column='mean_test_score', by='solver', grid=False)
    plt.title('Rendimiento según el Optimizador (Solver)')
    plt.suptitle('') # Quitar el subtítulo automático de pandas
    plt.xlabel('Optimizador')
    plt.ylabel('Puntuación Media (Accuracy)')
    plt.savefig(os.path.join(PLOTS_DIR, 'score_vs_solver.png'))
    plt.close()

    # Gráfica 2: Tiempo de Entrenamiento vs Solver
    plt.figure(figsize=(8, 5))
    df.boxplot(column='mean_fit_time', by='solver', grid=False)
    plt.title('Tiempo de Entrenamiento según el Optimizador')
    plt.suptitle('')
    plt.xlabel('Optimizador')
    plt.ylabel('Tiempo Medio de Entrenamiento (s)')
    plt.savefig(os.path.join(PLOTS_DIR, 'time_vs_solver.png'))
    plt.close()
    
    # Gráfica 3: Rendimiento por Función de Activación
    plt.figure(figsize=(8, 5))
    df.boxplot(column='mean_test_score', by='activation', grid=False)
    plt.title('Rendimiento según Función de Activación')
    plt.suptitle('')
    plt.xlabel('Activación')
    plt.ylabel('Puntuación Media (Accuracy)')
    plt.savefig(os.path.join(PLOTS_DIR, 'score_vs_activation.png'))
    plt.close()
    
    print("Gráficas comparativas generadas en: ", PLOTS_DIR)

def plot_confusion_matrix():
    print("Generando matriz de confusión...")
    # Cargar modelo
    clf = joblib.load(MODEL_PATH)
    
    # Obtener num temas para la generacion
    num_temas = get_num_temas()
    
    # Generar un set de datos de prueba para la matriz
    # Se genera una muestra pequeña (ej 2000)
    X, y = generar_datos_antibloqueo(2000, num_temas)
    
    y_pred = clf.predict(X)
    
    # Etiquetas ordenadas para que queden bien en el plot
    labels = clf.classes_
    
    cm = confusion_matrix(y, y_pred, labels=labels)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    
    fig, ax = plt.subplots(figsize=(12, 10))
    disp.plot(ax=ax, cmap='Blues', xticks_rotation=45)
    plt.title('Matriz de Confusión del Recomendador (MLP)')
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, 'confusion_matrix.png'))
    plt.close()
    print("Matriz de confusión generada en: ", PLOTS_DIR)

if __name__ == "__main__":
    if not os.path.exists(PLOTS_DIR):
        os.makedirs(PLOTS_DIR)
        
    plot_gridsearch_results()
    plot_confusion_matrix()
    print("¡Todas las gráficas han sido exportadas!")
