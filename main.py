#!/usr/bin/env python3
"""
Simulador de Ecuaciones Diferenciales

Aplicación de escritorio para simular diferentes modelos de ecuaciones diferenciales
con una interfaz gráfica intuitiva.
"""

def main():
    """Función principal que inicia la aplicación."""
    import tkinter as tk
    from tkinter import ttk
    from simulador.utils import SimuladorApp
    
    # Configuración de la ventana principal
    root = tk.Tk()
    root.title("Simulador de Ecuaciones Diferenciales")
    
    # Estilo
    style = ttk.Style()
    style.theme_use('clam')
    
    # Iniciar aplicación
    app = SimuladorApp(root)
    
    # Centrar ventana en la pantalla
    window_width = 1000
    window_height = 800
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    # Iniciar bucle principal
    root.mainloop()

if __name__ == "__main__":
    main()
