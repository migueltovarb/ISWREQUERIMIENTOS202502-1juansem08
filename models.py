"""
Modelos de ecuaciones diferenciales para la simulación.
"""
import numpy as np

class Modelo:
    """Clase base para los modelos de ecuaciones diferenciales."""
    
    def __init__(self, **params):
        self.params = params
        self.name = "Modelo Base"
    
    def calcular(self, t):
        """Calcula el valor del modelo en el tiempo t."""
        raise NotImplementedError("Método calcular() debe ser implementado por las subclases")
    
    def simular(self, t_max, dt=0.1):
        """Simula el modelo desde t=0 hasta t_max con paso dt."""
        t_values = np.arange(0, t_max + dt, dt)
        y_values = np.array([self.calcular(t) for t in t_values])
        return t_values, y_values
    
    def get_estadisticas(self, t_values, y_values):
        """
        Calcula estadísticas básicas de la simulación.
        
        Args:
            t_values: Array de valores de tiempo
            y_values: Array de valores de la variable de estado
            
        Returns:
            dict: Diccionario con las estadísticas calculadas
        """
        if len(y_values) == 0 or len(t_values) == 0:
            return {}
            
        y_values = np.asarray(y_values, dtype=float)
        t_values = np.asarray(t_values, dtype=float)
        
        # Estadísticas básicas
        stats = {
            'promedio': np.mean(y_values),
            'maximo': np.max(y_values),
            'minimo': np.min(y_values),
            'tasa_cambio': 0.0,
            'tiempo_equilibrio': t_values[-1] if len(t_values) > 0 else 0.0
        }
        
        # Calcular tasa de cambio promedio (solo si hay suficientes puntos)
        if len(y_values) > 1 and len(t_values) > 1:
            with np.errstate(divide='ignore', invalid='ignore'):
                delta_y = np.diff(y_values)
                delta_t = np.diff(t_values)
                valid_dt = delta_t > 0
                if np.any(valid_dt):
                    rates = delta_y[valid_dt] / delta_t[valid_dt]
                    stats['tasa_cambio'] = np.mean(rates[np.isfinite(rates)])
        
        # Calcular tiempo de equilibrio (cuando la variación es pequeña)
        if len(y_values) > 2:
            # Usar variación absoluta normalizada
            abs_changes = np.abs(np.diff(y_values))
            scale = np.maximum(np.abs(y_values[1:]), 1e-10)  # Evitar división por cero
            rel_changes = np.divide(abs_changes, scale, out=np.zeros_like(abs_changes), where=scale>0)
            
            # Umbral para considerar equilibrio (1% de cambio o cambio absoluto pequeño)
            is_steady = (rel_changes < 0.01) | (abs_changes < 1e-6)
            
            # Encontrar el primer punto donde se alcanza el equilibrio
            steady_points = np.where(is_steady)[0]
            if len(steady_points) > 0:
                # Tomar el primer punto de equilibrio y sumar 1 porque diff() reduce la longitud en 1
                first_steady = steady_points[0] + 1
                if first_steady < len(t_values):
                    stats['tiempo_equilibrio'] = t_values[first_steady]
        
        return stats
    
    def get_interpretacion(self, t_values, y_values):
        """Genera una interpretación de los resultados."""
        return ""


class CrecimientoExponencial(Modelo):
    """Modelo de crecimiento exponencial P(t) = P0 * e^(k*t)."""
    
    def __init__(self, P0, k):
        super().__init__(P0=P0, k=k)
        self.P0 = P0
        self.k = k
        self.name = "Crecimiento Exponencial"
    
    def calcular(self, t):
        return self.P0 * np.exp(self.k * t)
    
    def get_interpretacion(self, t_values, y_values):
        if self.k > 0:
            return f"El sistema muestra un crecimiento exponencial con tasa {self.k:.4f}."
        elif self.k < 0:
            return f"El sistema muestra un decaimiento exponencial con tasa {abs(self.k):.4f}."
        return "El sistema permanece constante en el tiempo."


class EnfriamientoNewton(Modelo):
    """
    Ley de enfriamiento de Newton.
    
    Parámetros:
    - T0: Temperatura inicial del objeto (°C)
    - Ta: Temperatura ambiente (°C)
    - k: Constante de enfriamiento (debe ser > 0)
    
    Fórmula: T(t) = Ta + (T0 - Ta) * e^(-k*t)
    """
    
    def __init__(self, T0, Ta, k):
        if k <= 0:
            raise ValueError("La constante de enfriamiento (k) debe ser mayor que 0")
        if T0 == Ta:
            raise ValueError("La temperatura inicial no puede ser igual a la temperatura ambiente")
            
        super().__init__(T0=T0, Ta=Ta, k=k)
        self.T0 = float(T0)
        self.Ta = float(Ta)
        self.k = float(k)
        self.name = "Ley de Enfriamiento"
    
    def calcular(self, t):
        if t < 0:
            return self.T0  # Asumimos temperatura constante antes de t=0
        return self.Ta + (self.T0 - self.Ta) * np.exp(-self.k * t)
    
    def get_interpretacion(self, t_values, y_values):
        stats = self.get_estadisticas(t_values, y_values)
        tiempo_estabilizacion = stats.get('tiempo_equilibrio', 0)
        return (
            f"El sistema se enfría de {self.T0:.1f}°C hacia la temperatura ambiente {self.Ta:.1f}°C. "
            f"Se estabiliza en aproximadamente {tiempo_estabilizacion:.1f} unidades de tiempo."
        )


class CircuitoRL(Modelo):
    """Modelo de circuito RL i(t) = (E/R) * (1 - e^(-R*t/L))."""
    
    def __init__(self, E, R, L):
        super().__init__(E=E, R=R, L=L)
        self.E = E
        self.R = R
        self.L = L
        self.name = "Circuito RL"
    
    def calcular(self, t):
        if self.R == 0 or self.L == 0:
            return 0
        return (self.E / self.R) * (1 - np.exp(-self.R * t / self.L))
    
    def get_interpretacion(self, t_values, y_values):
        if self.L > 0:
            tau = self.L / self.R if self.R != 0 else float('inf')
            return (
                f"El circuito RL tiene una constante de tiempo τ = {tau:.2f}. "
                f"La corriente máxima teórica es {self.E/self.R if self.R != 0 else float('inf'):.2f} A."
            )
        return ""


class Mezclas(Modelo):
    """
    Modelo de mezclas para un tanque perfectamente agitado con flujos de entrada y salida.
    
    Parámetros:
    - V0: Volumen inicial del tanque (L, debe ser > 0)
    - C0: Concentración inicial en el tanque (g/L, debe ser >= 0)
    - r_in: Caudal de entrada (L/min, debe ser >= 0)
    - C_in: Concentración de entrada (g/L, debe ser >= 0)
    - r_out: Caudal de salida (L/min, debe ser >= 0)
    
    Fórmula cuando r_in = r_out (volumen constante):
    C(t) = C_in + (C0 - C_in) * e^(-(r/V0)*t)
    
    Fórmula cuando r_in ≠ r_out (volumen variable):
    V(t) = V0 + (r_in - r_out) * t
    C(t) = [r_in*C_in - r_out*C(t)] / V(t) * Δt + C(t-1)
    """
    
    def __init__(self, V0, C0, r_in, C_in, r_out):
        if V0 <= 0:
            raise ValueError("El volumen inicial del tanque debe ser mayor que 0")
        if C0 < 0:
            raise ValueError("La concentración inicial no puede ser negativa")
        if r_in < 0 or r_out < 0:
            raise ValueError("Los caudales no pueden ser negativos")
        if C_in < 0:
            raise ValueError("La concentración de entrada no puede ser negativa")
            
        super().__init__(V0=float(V0), C0=float(C0), r_in=float(r_in), 
                        C_in=float(C_in), r_out=float(r_out))
        self.V0 = float(V0)      # Volumen inicial (L)
        self.C0 = float(C0)      # Concentración inicial (g/L)
        self.r_in = float(r_in)  # Caudal de entrada (L/min)
        self.C_in = float(C_in)  # Concentración de entrada (g/L)
        self.r_out = float(r_out) # Caudal de salida (L/min)
        self.name = "Modelo de Mezclas"
        
        # Verificar si el volumen es constante
        self.volumen_constante = abs(r_in - r_out) < 1e-10
    
    def calcular(self, t):
        """
        Calcula la cantidad de soluto A(t) en el tanque en el tiempo t.
        
        Para volumen constante (r_in = r_out):
        A(t) = A_ss + (A0 - A_ss) * exp(-(r_out/V0) * t)
        Donde A_ss = (r_in * C_in * V0) / r_out
        
        Para volumen variable (r_in ≠ r_out):
        Se resuelve numéricamente la ecuación diferencial.
        """
        if t <= 0:
            return self.C0 * self.V0  # Cantidad inicial A0 = C0 * V0
            
        if self.volumen_constante:
            # Caso 1: Volumen constante (r_in = r_out)
            if self.r_out == 0:  # Sin flujo de salida
                return self.C0 * self.V0
                
            # Cálculo del estado estacionario
            A_ss = (self.r_in * self.C_in * self.V0) / self.r_out if self.r_out != 0 else 0
            A0 = self.C0 * self.V0  # Cantidad inicial
            
            # Solución analítica exacta
            k = self.r_out / self.V0
            A_t = A_ss + (A0 - A_ss) * np.exp(-k * t)
            return max(0.0, A_t)
            
        else:
            # Caso 2: Volumen variable (r_in ≠ r_out)
            if self.r_in == 0 and self.r_out == 0:  # Sin flujo
                return self.C0 * self.V0
                
            # Solución numérica usando el método de Euler
            dt = min(0.1, t/1000)  # Paso de tiempo pequeño para mayor precisión
            current_t = 0
            current_A = self.C0 * self.V0  # Cantidad inicial
            current_V = self.V0
            
            while current_t < t:
                if current_V <= 0:  # Tanque vacío
                    return 0.0
                    
                # Tamaño del paso (no exceder t)
                dt_step = min(dt, t - current_t)
                
                # Calcular la derivada dA/dt = r_in*C_in - r_out*(A/V)
                if current_V > 0:
                    dA_dt = self.r_in * self.C_in - self.r_out * (current_A / current_V)
                    current_A += dA_dt * dt_step
                    current_V += (self.r_in - self.r_out) * dt_step
                    
                    # Asegurar que no haya cantidades negativas
                    current_A = max(0.0, current_A)
                    current_V = max(0.0, current_V)
                    
                current_t += dt_step
                
                # Si la cantidad es muy pequeña, considerarla cero
                if abs(current_A) < 1e-10:
                    current_A = 0.0
            
            return current_A
    
    def get_interpretacion(self, t_values, y_values):
        if len(y_values) == 0:
            return "No hay datos de simulación disponibles."
            
        final_amount = y_values[-1]
        final_vol = self.V0 + (self.r_in - self.r_out) * t_values[-1] if len(t_values) > 0 else self.V0
        final_conc = final_amount / final_vol if final_vol > 0 else 0
        
        if self.volumen_constante:
            # Para volumen constante (r_in = r_out)
            if self.r_out > 0:
                # Tiempo característico (tau = V0/r_out)
                tau = self.V0 / self.r_out
                
                # Estado estacionario teórico
                A_ss = (self.r_in * self.C_in * self.V0) / self.r_out
                C_ss = A_ss / self.V0
                
                return (
                    f"SISTEMA DE MEZCLAS (VOLUMEN CONSTANTE)\n"
                    f"• Volumen: {self.V0:.2f} L (constante)\n"
                    f"• Flujo de entrada: {self.r_in:.2f} L/min, Conc: {self.C_in:.4f} g/L\n"
                    f"• Flujo de salida: {self.r_out:.2f} L/min\n"
                    f"• Tiempo característico (τ): {tau:.2f} min\n\n"
                    f"CONDICIONES INICIALES\n"
                    f"• Cantidad inicial (A₀): {self.C0 * self.V0:.2f} g\n"
                    f"• Concentración inicial (C₀): {self.C0:.4f} g/L\n\n"
                    f"ESTADO ESTACIONARIO TEÓRICO\n"
                    f"• Cantidad (A_ss): {A_ss:.2f} g\n"
                    f"• Concentración (C_ss): {C_ss:.4f} g/L\n\n"
                    f"RESULTADOS FINALES (t = {t_values[-1]:.1f} min)\n"
                    f"• Cantidad final: {final_amount:.2f} g\n"
                    f"• Concentración final: {final_conc:.4f} g/L"
                )
            else:
                return "Sistema sin flujo de salida. La cantidad de soluto no cambia con el tiempo."
        else:
            # Para volumen variable (r_in ≠ r_out)
            return (
                f"SISTEMA DE MEZCLAS (VOLUMEN VARIABLE)\n"
                f"• Volumen inicial: {self.V0:.2f} L\n"
                f"• Flujo de entrada: {self.r_in:.2f} L/min, Conc: {self.C_in:.4f} g/L\n"
                f"• Flujo de salida: {self.r_out:.2f} L/min\n"
                f"• Tasa de cambio de volumen: {self.r_in - self.r_out:.2f} L/min\n\n"
                f"CONDICIONES INICIALES\n"
                f"• Cantidad inicial (A₀): {self.C0 * self.V0:.2f} g\n"
                f"• Concentración inicial (C₀): {self.C0:.4f} g/L\n\n"
                f"RESULTADOS FINALES (t = {t_values[-1]:.1f} min)\n"
                f"• Volumen final: {final_vol:.2f} L\n"
                f"• Cantidad final: {final_amount:.2f} g\n"
                f"• Concentración final: {final_conc:.4f} g/L"
            )
