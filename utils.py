"""
Funciones de utilidad para el simulador de ecuaciones diferenciales.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from tkinter import messagebox
import numpy as np

class ToolTip(object):
    """Clase para crear tooltips en los widgets."""
    def __init__(self, widget, text='widget info', wraplength=200, delay=500):
        self.widget = widget
        self.text = text
        self.wraplength = wraplength
        self.delay = delay
        self.tooltip = None
        self.tooltip_id = None
        self.widget.bind("<Enter>", self.schedule_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def schedule_tooltip(self, event=None):
        """Programa la aparición del tooltip después de un retraso."""
        self.cancel_scheduled_tooltip()
        self.tooltip_id = self.widget.after(self.delay, self.show_tooltip)
    
    def show_tooltip(self, event=None):
        """Muestra el tooltip."""
        self.cancel_scheduled_tooltip()
        
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        # Crear tooltip
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        # Configurar el estilo del tooltip
        style = ttk.Style()
        style.configure("Tooltip.TLabel", 
                       background="#ffffe0", 
                       relief="solid", 
                       borderwidth=1,
                       padding=5,
                       wraplength=self.wraplength)
        
        # Crear etiqueta con el texto
        label = ttk.Label(
            self.tooltip, 
            text=self.text,
            justify='left',
            style="Tooltip.TLabel"
        )
        label.pack()
        
        # Asegurarse de que el tooltip se cierre al salir del widget
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def hide_tooltip(self, event=None):
        """Oculta el tooltip."""
        self.cancel_scheduled_tooltip()
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
    
    def cancel_scheduled_tooltip(self):
        """Cancela la aparición programada del tooltip."""
        if self.tooltip_id:
            self.widget.after_cancel(self.tooltip_id)
            self.tooltip_id = None
import tkinter as tk
from tkinter import ttk
import pandas as pd
from matplotlib.figure import Figure
from .models import (
    CrecimientoExponencial, 
    EnfriamientoNewton, 
    CircuitoRL, 
    Mezclas
)

class SimuladorApp:
    """Clase principal de la aplicación de simulación."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Ecuaciones Diferenciales")
        self.root.geometry("1000x800")
        
        # Variables de control
        self.modelo_seleccionado = tk.StringVar(value="crecimiento")
        self.simulaciones = []  # Almacena las simulaciones para comparación
        
        self.crear_interfaz()
    
    def crear_interfaz(self):
        """Crea la interfaz de usuario principal."""
        # Configuración de estilo
        style = ttk.Style()
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10))
        style.configure('TNotebook', background='#f0f0f0')
        style.configure('TNotebook.Tab', font=('Arial', 10, 'bold'), padding=[10, 5])
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Panel de control izquierdo
        control_frame = ttk.LabelFrame(
            main_frame, 
            text="⚙️ PARÁMETROS", 
            padding="10",
            style='TFrame'
        )
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Panel de gráfica derecha
        graph_frame = ttk.Frame(main_frame)
        graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configurar el grid para que se expanda correctamente
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # --- Panel de control ---
        # Título de la sección de modelos
        ttk.Label(
            control_frame, 
            text="📊 MODELOS DISPONIBLES",
            font=('Arial', 10, 'bold')
        ).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Descripción de los modelos
        descripciones = {
            "crecimiento": "Población que crece sin límites (P(t) = P₀·eᵏᵗ)",
            "enfriamiento": "Enfriamiento de un objeto (T(t) = Tₐ + (T₀-Tₐ)·e⁻ᵏᵗ)",
            "circuito_rl": "Corriente en circuito RL (i(t) = (E/R)·(1-e⁻ᴿᵗ/ᴸ))",
            "mezclas": "Concentración en tanque de mezclas"
        }
        
        modelos = [
            ("📈 Crecimiento Exponencial", "crecimiento"),
            ("🌡️ Ley de Enfriamiento", "enfriamiento"),
            ("⚡ Circuito RL", "circuito_rl"),
            ("🧪 Modelo de Mezclas", "mezclas")
        ]
        
        for i, (text, value) in enumerate(modelos, 1):
            # Frame para cada opción
            frame = ttk.Frame(control_frame)
            frame.grid(row=i, column=0, sticky='ew', pady=2)
            
            # Botón de radio
            rb = ttk.Radiobutton(
                frame,
                text='',
                variable=self.modelo_seleccionado,
                value=value,
                command=self.actualizar_campos
            )
            rb.pack(side=tk.LEFT, padx=(0, 5))
            
            # Etiqueta con descripción
            ttk.Label(
                frame, 
                text=text,
                cursor='hand2',
                style='TLabel'
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Tooltip con descripción
            ToolTip(
                frame, 
                text=descripciones[value],
                wraplength=200,
                delay=100
            )
        
        # Frame para parámetros
        self.param_frame = ttk.Frame(control_frame)
        self.param_frame.grid(row=len(modelos)+1, column=0, sticky=tk.W, pady=10)
        
        # Botones de acción con mejor estilo
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=100, column=0, pady=(20, 10), sticky=tk.W+tk.E)
        
        # Estilo para botones
        style = ttk.Style()
        style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
        
        # Botón Simular
        btn_simular = ttk.Button(
            btn_frame, 
            text="▶️ Simular", 
            command=self.simular,
            style='Accent.TButton',
            width=15
        )
        btn_simular.pack(side=tk.TOP, fill=tk.X, pady=2)
        
        # Frame para botones secundarios
        btn_frame2 = ttk.Frame(btn_frame)
        btn_frame2.pack(fill=tk.X, pady=(5, 0))
        
        # Botón Comparar
        ttk.Button(
            btn_frame2, 
            text="🔄 Comparar", 
            command=self.comparar,
            width=12
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Botón Limpiar
        ttk.Button(
            btn_frame2, 
            text="🗑️ Limpiar", 
            command=self.limpiar,
            width=12
        ).pack(side=tk.RIGHT)
        
        # Inicializar campos de parámetros
        self.crear_campos_parametros()
        
        # --- Panel de gráfica ---
        # Frame para la gráfica con borde
        graph_container = ttk.LabelFrame(
            graph_frame, 
            text="📊 GRÁFICA DE SIMULACIÓN",
            padding=5
        )
        graph_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configurar la figura de matplotlib
        plt.style.use('seaborn-v0_8')
        
        self.fig = Figure(figsize=(8, 5), dpi=100, facecolor='#f8f9fa')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel('Tiempo (t)', fontsize=10, fontweight='bold')
        self.ax.set_ylabel('Valor', fontsize=10, fontweight='bold')
        self.ax.set_title('Resultado de la Simulación', fontsize=12, fontweight='bold', pad=15)
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.set_facecolor('#f8f9fa')
        
        # Configurar el canvas de matplotlib
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_container)
        self.canvas.draw()
        
        # Barra de herramientas de navegación
        toolbar = NavigationToolbar2Tk(self.canvas, graph_container, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Empaquetar el canvas
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Notebook para pestañas de resultados
        self.notebook = ttk.Notebook(graph_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Pestaña de tabla de resultados
        self.tab_resultados = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_resultados, text="📋 Datos")
        
        # Frame para la tabla
        self.tree_frame = ttk.Frame(self.tab_resultados)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Pestaña de estadísticas
        self.tab_estadisticas = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_estadisticas, text="📊 Estadísticas")
        
        # Frame para estadísticas
        self.stats_frame = ttk.Frame(self.tab_estadisticas)
        self.stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña de información
        self.tab_info = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_info, text="ℹ️ Información")
        
        # Frame para información del modelo
        self.info_frame = ttk.Frame(self.tab_info)
        self.info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Texto interpretativo en la pestaña de información
        self.interpretacion_text = tk.Text(
            self.info_frame, 
            height=8, 
            wrap=tk.WORD,
            padx=10,
            pady=10,
            font=('Arial', 10),
            bg='#f8f9fa',
            relief=tk.FLAT
        )
        self.interpretacion_text.pack(fill=tk.BOTH, expand=True)
        
        # Insertar información inicial
        info_inicial = """BIENVENIDO AL SIMULADOR DE ECUACIONES DIFERENCIALES

Seleccione un modelo en el panel izquierdo, ingrese los parámetros 
y haga clic en 'Simular' para ver los resultados.

Cada modelo representa un fenómeno diferente:

1. 📈 Crecimiento Exponencial: Modela el crecimiento sin límites de una población.
2. 🌡️ Ley de Enfriamiento: Muestra cómo un objeto pierde calor con el tiempo.
3. ⚡ Circuito RL: Simula la corriente en un circuito eléctrico con resistencia e inductancia.
4. 🧪 Modelo de Mezclas: Calcula la concentración en un tanque con entradas y salidas."""
        
        self.interpretacion_text.insert(tk.END, info_inicial)
        self.interpretacion_text.config(state=tk.DISABLED)
        
        # Añadir scrollbar al texto
        scrollbar = ttk.Scrollbar(
            self.interpretacion_text, 
            command=self.interpretacion_text.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.interpretacion_text.config(yscrollcommand=scrollbar.set)
    
    def crear_campos_parametros(self):
        """Crea los campos de entrada para los parámetros según el modelo seleccionado."""
        # Limpiar frame de parámetros
        for widget in self.param_frame.winfo_children():
            widget.destroy()
        
        modelo = self.modelo_seleccionado.get()
        
        if modelo == "crecimiento":
            self.crear_campos_crecimiento()
        elif modelo == "enfriamiento":
            self.crear_campos_enfriamiento()
        elif modelo == "circuito_rl":
            self.crear_campos_circuito_rl()
        elif modelo == "mezclas":
            self.crear_campos_mezclas()
    
    def crear_campos_crecimiento(self):
        """Crea campos para el modelo de crecimiento exponencial."""
        # P0: valor inicial
        ttk.Label(self.param_frame, text="P0 (valor inicial):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.entry_p0 = ttk.Entry(self.param_frame)
        self.entry_p0.grid(row=0, column=1, sticky=tk.W, pady=2)
        self.entry_p0.insert(0, "1.0")
        
        # k: constante de crecimiento
        ttk.Label(self.param_frame, text="k (tasa de crecimiento):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.entry_k = ttk.Entry(self.param_frame)
        self.entry_k.grid(row=1, column=1, sticky=tk.W, pady=2)
        self.entry_k.insert(0, "0.1")
        
        # t_max: tiempo máximo de simulación
        ttk.Label(self.param_frame, text="Tiempo máximo (t_max):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.entry_tmax = ttk.Entry(self.param_frame)
        self.entry_tmax.grid(row=2, column=1, sticky=tk.W, pady=2)
        self.entry_tmax.insert(0, "10")
    
    def crear_campos_enfriamiento(self):
        """Crea campos para el modelo de enfriamiento de Newton."""
        # T0: temperatura inicial
        ttk.Label(self.param_frame, text="T0 (temp. inicial °C):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.entry_t0 = ttk.Entry(self.param_frame)
        self.entry_t0.grid(row=0, column=1, sticky=tk.W, pady=2)
        self.entry_t0.insert(0, "90")
        
        # Ta: temperatura ambiente
        ttk.Label(self.param_frame, text="Ta (temp. ambiente °C):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.entry_ta = ttk.Entry(self.param_frame)
        self.entry_ta.grid(row=1, column=1, sticky=tk.W, pady=2)
        self.entry_ta.insert(0, "25")
        
        # k: constante de enfriamiento
        ttk.Label(self.param_frame, text="k (constante de enfriamiento):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.entry_k = ttk.Entry(self.param_frame)
        self.entry_k.grid(row=2, column=1, sticky=tk.W, pady=2)
        self.entry_k.insert(0, "0.1")
        
        # t_max: tiempo máximo de simulación
        ttk.Label(self.param_frame, text="Tiempo máximo (t_max):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.entry_tmax = ttk.Entry(self.param_frame)
        self.entry_tmax.grid(row=3, column=1, sticky=tk.W, pady=2)
        self.entry_tmax.insert(0, "30")
    
    def crear_campos_circuito_rl(self):
        """Crea campos para el modelo de circuito RL."""
        # E: voltaje
        ttk.Label(self.param_frame, text="E (voltaje, V):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.entry_e = ttk.Entry(self.param_frame)
        self.entry_e.grid(row=0, column=1, sticky=tk.W, pady=2)
        self.entry_e.insert(0, "12")
        
        # R: resistencia
        ttk.Label(self.param_frame, text="R (resistencia, Ω):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.entry_r = ttk.Entry(self.param_frame)
        self.entry_r.grid(row=1, column=1, sticky=tk.W, pady=2)
        self.entry_r.insert(0, "100")
        
        # L: inductancia
        ttk.Label(self.param_frame, text="L (inductancia, H):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.entry_l = ttk.Entry(self.param_frame)
        self.entry_l.grid(row=2, column=1, sticky=tk.W, pady=2)
        self.entry_l.insert(0, "1")
        
        # t_max: tiempo máximo de simulación
        ttk.Label(self.param_frame, text="Tiempo máximo (t_max):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.entry_tmax = ttk.Entry(self.param_frame)
        self.entry_tmax.grid(row=3, column=1, sticky=tk.W, pady=2)
        self.entry_tmax.insert(0, "0.1")
    
    def crear_campos_mezclas(self):
        """Crea campos para el modelo de mezclas."""
        # V0: Volumen inicial del tanque
        ttk.Label(self.param_frame, text="V0 (volumen inicial, L):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.entry_v0 = ttk.Entry(self.param_frame)
        self.entry_v0.grid(row=0, column=1, sticky=tk.W, pady=2)
        self.entry_v0.insert(0, "100")
        
        # C0: Concentración inicial
        ttk.Label(self.param_frame, text="C0 (conc. inicial, g/L):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.entry_c0 = ttk.Entry(self.param_frame)
        self.entry_c0.grid(row=1, column=1, sticky=tk.W, pady=2)
        self.entry_c0.insert(0, "0.5")
        
        # r_in: caudal de entrada
        ttk.Label(self.param_frame, text="r_in (caudal entrada, L/min):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.entry_r_in = ttk.Entry(self.param_frame)
        self.entry_r_in.grid(row=2, column=1, sticky=tk.W, pady=2)
        self.entry_r_in.insert(0, "2")
        
        # C_in: concentración de entrada
        ttk.Label(self.param_frame, text="C_in (conc. entrada, g/L):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.entry_c_in = ttk.Entry(self.param_frame)
        self.entry_c_in.grid(row=3, column=1, sticky=tk.W, pady=2)
        self.entry_c_in.insert(0, "0.1")
        
        # r_out: caudal de salida
        ttk.Label(self.param_frame, text="r_out (caudal salida, L/min):").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.entry_r_out = ttk.Entry(self.param_frame)
        self.entry_r_out.grid(row=4, column=1, sticky=tk.W, pady=2)
        self.entry_r_out.insert(0, "2")
        
        # t_max: tiempo máximo de simulación
        ttk.Label(self.param_frame, text="Tiempo máximo (min):").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.entry_tmax = ttk.Entry(self.param_frame)
        self.entry_tmax.grid(row=5, column=1, sticky=tk.W, pady=2)
        self.entry_tmax.insert(0, "60")
    
    def actualizar_campos(self):
        """Actualiza los campos de entrada según el modelo seleccionado."""
        self.crear_campos_parametros()
    
    def obtener_parametros(self):
        """Obtiene los parámetros ingresados por el usuario."""
        try:
            modelo = self.modelo_seleccionado.get()
            params = {}
            
            # Parámetros comunes
            t_max = float(self.entry_tmax.get())
            
            if modelo == "crecimiento":
                params = {
                    'P0': float(self.entry_p0.get()),
                    'k': float(self.entry_k.get()),
                    't_max': t_max
                }
            elif modelo == "enfriamiento":
                params = {
                    'T0': float(self.entry_t0.get()),
                    'Ta': float(self.entry_ta.get()),
                    'k': float(self.entry_k.get()),
                    't_max': t_max
                }
            elif modelo == "circuito_rl":
                params = {
                    'E': float(self.entry_e.get()),
                    'R': float(self.entry_r.get()),
                    'L': float(self.entry_l.get()),
                    't_max': t_max
                }
            elif modelo == "mezclas":
                params = {
                    'V0': float(self.entry_v0.get()),
                    'C0': float(self.entry_c0.get()),
                    'r_in': float(self.entry_r_in.get()),
                    'C_in': float(self.entry_c_in.get()),
                    'r_out': float(self.entry_r_out.get()),
                    't_max': float(self.entry_tmax.get())
                }
            
            return params
            
        except ValueError as e:
            tk.messagebox.showerror("Error", f"Error en los parámetros: {str(e)}")
            return None
    
    def crear_modelo(self, params):
        """Crea una instancia del modelo con los parámetros dados."""
        modelo = self.modelo_seleccionado.get()
        
        if modelo == "crecimiento":
            return CrecimientoExponencial(params['P0'], params['k'])
        elif modelo == "enfriamiento":
            return EnfriamientoNewton(params['T0'], params['Ta'], params['k'])
        elif modelo == "circuito_rl":
            return CircuitoRL(params['E'], params['R'], params['L'])
        elif modelo == "mezclas":
            return Mezclas(
                V0=params['V0'],
                C0=params['C0'],
                r_in=params['r_in'],
                C_in=params['C_in'],
                r_out=params['r_out']
            )
    
    def simular(self, comparar=False):
        """Realiza la simulación y muestra los resultados."""
        params = self.obtener_parametros()
        if not params:
            return
        
        try:
            # Crear y simular modelo
            modelo = self.crear_modelo(params)
            t_values = np.linspace(0, params['t_max'], 1000)
            y_values = np.array([modelo.calcular(t) for t in t_values])
            
            # Calcular estadísticas
            stats = modelo.get_estadisticas(t_values, y_values)
            interpretacion = modelo.get_interpretacion(t_values, y_values)
            
            # Agregar a la lista de simulaciones si estamos comparando
            if comparar:
                self.simulaciones.append((t_values, y_values, modelo.name, stats, interpretacion))
                if len(self.simulaciones) < 2:
                    return  # Esperar a tener al menos dos simulaciones
            else:
                self.simulaciones = [(t_values, y_values, modelo.name, stats, interpretacion)]
            
            # Actualizar interfaz
            self.actualizar_grafica()
            self.actualizar_tabla()
            self.actualizar_estadisticas()
            self.actualizar_interpretacion()
            
        except Exception as e:
            tk.messagebox.showerror("Error", f"Error en la simulación: {str(e)}")
    
    def comparar(self):
        """Realiza una simulación para comparar con la anterior."""
        if len(self.simulaciones) == 0:
            # Primera simulación
            self.simular(comparar=True)
        else:
            # Segunda simulación
            self.simular(comparar=True)
    
    def actualizar_grafica(self):
        """Actualiza la gráfica con los resultados de la simulación."""
        self.ax.clear()
        
        # Colores para múltiples simulaciones
        colors = ['b', 'r', 'g', 'm', 'c']
        
        for i, (t_values, y_values, label, _, _) in enumerate(self.simulaciones):
            color = colors[i % len(colors)]
            self.ax.plot(t_values, y_values, label=label, color=color)
        
        self.ax.set_xlabel('Tiempo (t)')
        self.ax.set_ylabel('Valor')
        self.ax.set_title('Resultado de la simulación')
        self.ax.grid(True)
        
        if len(self.simulaciones) > 1:
            self.ax.legend()
        
        self.canvas.draw()
    
    def actualizar_tabla(self):
        """Actualiza la tabla con los resultados de la simulación."""
        # Limpiar tabla existente
        for widget in self.tree_frame.winfo_children():
            widget.destroy()
        
        if not self.simulaciones:
            ttk.Label(
                self.tree_frame, 
                text="No hay datos para mostrar. Realice una simulación primero.",
                font=('Arial', 10, 'italic')
            ).pack(expand=True, pady=50)
            return
        
        # Usar solo la última simulación para la tabla
        t_values, y_values, nombre_modelo, stats, _ = self.simulaciones[-1]
        
        # Frame para controles de la tabla
        controls_frame = ttk.Frame(self.tree_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Etiqueta con el nombre del modelo
        ttk.Label(
            controls_frame, 
            text=f"Modelo: {nombre_modelo}",
            font=('Arial', 9, 'bold'),
            foreground='#2c3e50'
        ).pack(side=tk.LEFT)
        
        # Selector de número de filas a mostrar
        ttk.Label(controls_frame, text="Mostrar:").pack(side=tk.RIGHT, padx=(0, 5))
        
        num_rows = tk.StringVar(value="20")
        rows_menu = ttk.Combobox(
            controls_frame, 
            textvariable=num_rows, 
            values=["10", "20", "50", "100", "Todas"],
            width=8,
            state='readonly'
        )
        rows_menu.pack(side=tk.RIGHT)
        
        # Frame para la tabla y scrollbars
        table_container = ttk.Frame(self.tree_frame)
        table_container.pack(fill=tk.BOTH, expand=True)
        
        # Configurar columnas
        columns = ("Tiempo (t)", "Valor")
        tree = ttk.Treeview(
            table_container, 
            columns=columns, 
            show="headings", 
            selectmode='extended',
            style='Custom.Treeview'
        )
        
        # Configurar estilo de la tabla
        style = ttk.Style()
        style.configure('Treeview', 
                       rowheight=25,
                       font=('Arial', 9))
        style.configure('Treeview.Heading', 
                       font=('Arial', 9, 'bold'))
        style.map('Treeview', 
                 background=[('selected', '#3498db')],
                 foreground=[('selected', 'white')])
        
        # Configurar anchos de columnas
        col_widths = {'Tiempo (t)': 120, 'Valor': 180}
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=col_widths[col], anchor=tk.CENTER)
        
        # Función para actualizar la tabla cuando cambia el número de filas
        def update_table(*args):
            # Limpiar tabla
            for item in tree.get_children():
                tree.delete(item)
            
            # Determinar el paso según el número de filas seleccionado
            n = len(t_values)
            try:
                if num_rows.get() == "Todas":
                    step = 1
                else:
                    step = max(1, n // int(num_rows.get()))
            except:
                step = max(1, n // 20)
            
            # Agregar datos
            for i in range(0, n, step):
                tree.insert("", tk.END, 
                           values=(f"{t_values[i]:.2f}",  # Reducido a 2 decimales
                                 f"{y_values[i]:.2f}"))  # Reducido a 2 decimales
        
        # Configurar el evento de cambio en el selector de filas
        num_rows.trace('w', update_table)
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=tree.yview)
        x_scroll = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
        # Empaquetar widgets
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Botón para exportar a Excel
        btn_export = ttk.Button(
            self.tree_frame,
            text="💾 Exportar a Excel",
            command=lambda: self.exportar_a_excel(t_values, y_values, nombre_modelo)
        )
        btn_export.pack(pady=(10, 0))
        
        # Cargar datos iniciales
        update_table()
    
    def actualizar_estadisticas(self):
        """Actualiza el panel de estadísticas."""
        # Limpiar frame de estadísticas
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        
        if not self.simulaciones:
            ttk.Label(
                self.stats_frame, 
                text="No hay datos de simulación disponibles.",
                font=('Arial', 10, 'italic')
            ).pack(pady=20)
            return
        
        # Mostrar estadísticas de la última simulación
        *_, stats, _ = self.simulaciones[-1]
        
        # Crear un frame para organizar las estadísticas en columnas
        stats_container = ttk.Frame(self.stats_frame)
        stats_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título de la sección
        ttk.Label(
            stats_container, 
            text="📊 ESTADÍSTICAS DE LA SIMULACIÓN",
            font=('Arial', 11, 'bold'),
            foreground='#2c3e50'
        ).grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky=tk.W)
        
        # Definir las estadísticas a mostrar y sus descripciones
        estadisticas = [
            ('promedio', 'Promedio del valor'),
            ('maximo', 'Valor máximo alcanzado'),
            ('minimo', 'Valor mínimo alcanzado'),
            ('tasa_cambio', 'Tasa de cambio promedio'),
            ('tiempo_equilibrio', 'Tiempo hasta estabilización')
        ]
        
        # Mostrar cada estadística con su descripción
        for i, (key, descripcion) in enumerate(estadisticas, 1):
            if key in stats:
                # Frame para cada estadística
                stat_frame = ttk.Frame(stats_container)
                stat_frame.grid(row=i, column=0, columnspan=2, sticky='ew', pady=3)
                
                # Nombre de la estadística
                ttk.Label(
                    stat_frame, 
                    text=f"• {descripcion}:",
                    font=('Arial', 9, 'bold'),
                    width=30,
                    anchor='w'
                ).pack(side=tk.LEFT)
                
                # Valor de la estadística
                valor = stats[key]
                if key == 'tasa_cambio':
                    valor_text = f"{valor:.6f} u/t"
                elif key == 'tiempo_equilibrio':
                    valor_text = f"{valor:.2f} segundos" if valor < 100 else f"{valor/60:.1f} minutos"
                else:
                    valor_text = f"{valor:.4f}"
                
                ttk.Label(
                    stat_frame, 
                    text=valor_text,
                    font=('Consolas', 9),
                    foreground='#2980b9',
                    width=15,
                    anchor='w'
                ).pack(side=tk.LEFT)
        
        # Añadir información adicional según el modelo
        modelo_actual = self.modelo_seleccionado.get()
        info_adicional = ttk.Frame(stats_container)
        info_adicional.grid(row=len(estadisticas)+2, column=0, columnspan=2, pady=(20, 0), sticky='w')
        
        ttk.Label(
            info_adicional,
            text="💡 Interpretación:",
            font=('Arial', 9, 'bold'),
            foreground='#27ae60'
        ).pack(anchor='w')
        
        # Texto interpretativo
        interpretacion = self.obtener_interpretacion_modelo(modelo_actual, stats)
        ttk.Label(
            info_adicional,
            text=interpretacion,
            font=('Arial', 9),
            wraplength=400,
            justify=tk.LEFT
        ).pack(anchor='w', pady=(5, 0))
    
    def obtener_interpretacion_modelo(self, modelo, stats):
        """Genera una interpretación detallada según el modelo y estadísticas."""
        if not stats:
            return "No hay datos suficientes para generar una interpretación."
            
        interpretaciones = {
            'crecimiento': (
                f"El modelo muestra un crecimiento exponencial con una tasa de {stats.get('tasa_cambio', 0):.4f} "
                f"unidades por segundo. "
                f"El valor máximo alcanzado fue {stats.get('maximo', 0):.2f} "
                f"y el valor mínimo fue {stats.get('minimo', 0):.2f}."
            ),
            'enfriamiento': (
                f"El objeto se enfría desde {stats.get('T0', 0):.1f}°C hacia la temperatura ambiente de {stats.get('Ta', 0):.1f}°C. "
                f"El tiempo de estabilización fue de {stats.get('tiempo_equilibrio', 0):.1f} segundos. "
                f"La tasa de enfriamiento inicial fue de {abs(stats.get('tasa_cambio', 0)):.4f}°C/seg."
            ),
            'circuito_rl': (
                f"El circuito alcanza aproximadamente el {stats.get('porcentaje_estado_estable', 0):.1f}% de su corriente máxima "
                f"de {stats.get('corriente_maxima', 0):.4f}A. "
                f"La constante de tiempo (τ = L/R) es de {stats.get('constante_tiempo', 0):.4f} segundos. "
                f"El tiempo de establecimiento (5τ) es de {stats.get('tiempo_establecimiento', 0):.4f} segundos."
            ),
            'mezclas': (
                f"La concentración en el tanque tiende a {stats.get('concentracion_equilibrio', 0):.4f} g/L. "
                f"El tiempo para alcanzar el 95% del equilibrio es de {stats.get('tiempo_95_por_ciento', 0):.2f} segundos. "
                f"La tasa de cambio inicial es de {stats.get('tasa_cambio_inicial', 0):.6f} (g/L)/s."
            )
        }
        
        return interpretaciones.get(modelo, "Interpretación no disponible para este modelo.")
    
    def actualizar_interpretacion(self):
        """Actualiza el texto interpretativo en la pestaña de información."""
        if not self.simulaciones:
            return
        
        # Obtener datos de la última simulación
        *_, nombre_modelo, stats, interpretacion = self.simulaciones[-1]
        
        # Crear un texto más detallado
        texto_detallado = f"""{interpretacion}

ANÁLISIS DETALLADO:
"""
        # Añadir información específica del modelo
        if nombre_modelo == "Crecimiento Exponencial":
            texto_detallado += f"""
• La población crece exponencialmente con una tasa de {stats.get('tasa_crecimiento', 0):.4f}.
• Se duplica cada {np.log(2)/stats.get('tasa_crecimiento', 0.0001):.2f} unidades de tiempo.
• El crecimiento es ilimitado en este modelo teórico."""
        
        elif nombre_modelo == "Ley de Enfriamiento":
            texto_detallado += f"""
• La temperatura desciende desde {stats.get('T0', 0):.1f}°C hacia {stats.get('Ta', 0):.1f}°C.
• La diferencia de temperatura se reduce a la mitad cada {np.log(0.5)/-stats.get('k', 0.0001):.2f} segundos.
• La tasa de enfriamiento es proporcional a la diferencia de temperatura."""
        
        elif nombre_modelo == "Circuito RL":
            texto_detallado += f"""
• La corriente máxima teórica es {stats.get('corriente_maxima', 0):.4f}A.
• Constante de tiempo (τ = L/R): {stats.get('constante_tiempo', 0):.4f}s.
• Tiempo de establecimiento (5τ): {stats.get('tiempo_establecimiento', 0):.4f}s."""
        
        elif nombre_modelo == "Modelo de Mezclas":
            texto_detallado += f"""
• Concentración de entrada: {stats.get('concentracion_entrada', 0):.2f}g/L.
• Tiempo característico (V/r): {stats.get('tiempo_caracteristico', 0):.2f}s.
• Concentración de equilibrio: {stats.get('concentracion_equilibrio', 0):.4f}g/L."""
        
        # Añadir recomendaciones
        texto_detallado += """

RECOMENDACIONES:
• Utilice el botón 'Comparar' para analizar diferentes escenarios.
• Exporte los datos a Excel para un análisis más detallado.
• Ajuste los parámetros para observar cómo afectan al comportamiento del sistema."""
        
        # Actualizar el widget de texto
        self.interpretacion_text.config(state=tk.NORMAL)
        self.interpretacion_text.delete(1.0, tk.END)
        self.interpretacion_text.insert(tk.END, texto_detallado)
        self.interpretacion_text.config(state=tk.DISABLED)
    
    def exportar_a_excel(self, t_values, y_values, nombre_modelo):
        """Exporta los datos de la simulación a un archivo Excel."""
        try:
            import pandas as pd
            from datetime import datetime
            import os
            
            # Crear un DataFrame con los datos
            df = pd.DataFrame({
                'Tiempo (s)': t_values,
                'Valor': y_values
            })
            
            # Crear nombre de archivo con fecha y hora
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simulacion_{nombre_modelo.lower().replace(' ', '_')}_{timestamp}.xlsx"
            
            # Guardar en Excel
            df.to_excel(filename, index=False, sheet_name='Datos')
            
            # Mostrar mensaje de éxito
            tk.messagebox.showinfo(
                "Exportación exitosa",
                f"Los datos se han exportado correctamente a:\n{os.path.abspath(filename)}"
            )
            
            # Abrir el archivo automáticamente
            os.startfile(os.path.abspath(filename))
            
        except Exception as e:
            tk.messagebox.showerror(
                "Error al exportar",
                f"No se pudo exportar a Excel: {str(e)}"
            )
    
    def limpiar(self):
        """Limpia los campos y resultados."""
        self.simulaciones = []
        
        # Limpiar gráfica
        self.ax.clear()
        self.ax.set_xlabel('Tiempo (t)')
        self.ax.set_ylabel('Valor')
        self.ax.set_title('Simulación')
        self.ax.grid(True)
        self.canvas.draw()
        
        # Limpiar tabla
        for widget in self.tree_frame.winfo_children():
            widget.destroy()
        
        # Limpiar estadísticas
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        
        # Limpiar interpretación
        self.interpretacion_text.config(state=tk.NORMAL)
        self.interpretacion_text.delete(1.0, tk.END)
        self.interpretacion_text.insert(tk.END, "Realice una simulación para ver los resultados.")
        self.interpretacion_text.config(state=tk.DISABLED)


def main():
    """Función principal para ejecutar la aplicación."""
    root = tk.Tk()
    app = SimuladorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
