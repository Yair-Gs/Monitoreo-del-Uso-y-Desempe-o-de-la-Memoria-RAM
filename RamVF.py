import tkinter as tk
from tkinter import ttk
import psutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import threading
import time
from matplotlib.gridspec import GridSpec
import queue
import logging
from typing import Dict, List


class MonitorSistema:
    def __init__(self, raiz):
        # Configurar logging
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Cola para actualizaciones seguras de UI
        self.cola_actualizacion = queue.Queue()

        # Configuración inicial
        self.raiz = raiz
        self.raiz.title("Monitoreo de la Ram del Sistema")
        self.raiz.configure(bg='#0d1117')

        # Forzar un tamaño mínimo de ventana
        self.raiz.minsize(1200, 800)

        # Variables de estado
        self.ejecutando = True
        self.puntos_datos: List[float] = [0] * 60  # Inicializar con 60 puntos en 0
        self.max_puntos_datos = 60

        # Configuración de estilos y UI
        self.configurar_estilos()
        self.configurar_ui()

        # Iniciar hilos de actualización
        self.iniciar_hilos_actualizacion()

        # Configurar cierre de ventana
        self.raiz.protocol("WM_DELETE_WINDOW", self.al_cerrar)

        # Iniciar bucle de actualización de UI
        self.actualizar_ui()

    def configurar_estilos(self):
        estilo = ttk.Style()
        estilo.theme_use('clam')

        # Paleta de colores moderna
        self.colores = {
            'fondo_oscuro': '#0d1117',
            'fondo_medio': '#1a1a1a',
            'fondo_claro': '#333333',
            'acento': '#00BFFF',
            'texto_primario': '#FFFFFF',
            'texto_secundario': '#FFFFFF',
            'exito': '#00FF00',
            'advertencia': '#FFFF00',
            'error': '#FF0000'
        }

        # Configuraciones de estilo
        estilos = {
            "Main.TFrame": {"background": self.colores['fondo_oscuro']},
            "Card.TFrame": {"background": self.colores['fondo_medio']},
            "Header.TLabel": {"background": self.colores['fondo_medio'],
                              "foreground": self.colores['texto_primario'],
                              "font": ('Segoe UI', 24, 'bold')},
            "Title.TLabel": {"background": self.colores['fondo_medio'],
                             "foreground": self.colores['texto_primario'],
                             "font": ('Segoe UI', 14, 'bold')},
            "Info.TLabel": {"background": self.colores['fondo_medio'],
                            "foreground": self.colores['texto_primario'],
                            "font": ('Segoe UI', 10)},
            "Value.TLabel": {"background": self.colores['fondo_medio'],
                             "foreground": self.colores['texto_secundario'],
                             "font": ('Consolas', 10)},
            "Treeview": {
                "configure": {
                    "background": self.colores['fondo_medio'],
                    "fieldbackground": self.colores['fondo_medio'],
                    "foreground": self.colores['texto_primario'],
                    "borderwidth": 0,
                    "font": ('Segoe UI', 9)
                },
                "map": {
                    "background": [("selected", self.colores['acento'])],
                    "foreground": [("selected", self.colores['fondo_oscuro'])]
                }
            },
            "Treeview.Heading": {
                "configure": {
                    "background": self.colores['fondo_claro'],
                    "foreground": self.colores['texto_primario'],
                    "relief": "flat",
                    "borderwidth": 0,
                    "font": ('Segoe UI', 10, 'bold')
                }
            },
            "TNotebook": {"configure": {"background": self.colores['fondo_medio']}},
            "TNotebook.Tab": {
                "configure": {"background": self.colores['fondo_claro'], "foreground": self.colores['texto_primario'],
                              "padding": [5, 2]},
                "map": {"background": [("selected", self.colores['acento'])],
                        "foreground": [("selected", self.colores['fondo_oscuro'])]}
            }
        }

        # Aplicar estilos
        for nombre_estilo, config_estilo in estilos.items():
            estilo.configure(nombre_estilo, **config_estilo)

    def configurar_ui(self):
        # Contenedor principal con tamaño fijo
        self.contenedor_principal = ttk.Frame(self.raiz, style="Main.TFrame")
        self.contenedor_principal.pack(fill='both', expand=True, padx=20, pady=20)

        # Configuración de grid con pesos fijos
        self.contenedor_principal.grid_columnconfigure(0, weight=2)  # Columna izquierda más ancha
        self.contenedor_principal.grid_columnconfigure(1, weight=3)  # Columna derecha más ancha
        for i in range(3):
            self.contenedor_principal.grid_rowconfigure(i, weight=1)

        # Crear secciones con tamaños fijos
        self.crear_encabezado()
        self.crear_seccion_metricas()
        self.crear_seccion_graficos()
        self.crear_seccion_procesos()

    def crear_encabezado(self):
        marco_encabezado = ttk.Frame(self.contenedor_principal, style="Card.TFrame")
        marco_encabezado.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)

        # Contenedor interno con padding fijo
        marco_interno = ttk.Frame(marco_encabezado, style="Card.TFrame")
        marco_interno.pack(fill='both', padx=15, pady=15)

        # Título con ancho fijo
        titulo = ttk.Label(marco_interno,
                           text="Monitoreo de la Ram del Sistema",
                           style="Header.TLabel",
                           width=30)  # Ancho fijo
        titulo.pack(side='left')

        # Marca de tiempo con ancho fijo
        self.marca_tiempo = ttk.Label(marco_interno,
                                      style="Value.TLabel",
                                      width=25)  # Ancho fijo
        self.marca_tiempo.pack(side='right')

    def crear_seccion_metricas(self):
        marco_metricas = ttk.Frame(self.contenedor_principal, style="Card.TFrame")
        marco_metricas.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)

        # Sección RAM
        marco_ram = self.crear_tarjeta_metrica(marco_metricas, "Uso de Memoria")
        self.etiquetas_ram = {}

        metricas = [
            ("RAM Total", "0 GB", 15),
            ("RAM Usada", "0 GB", 15),
            ("Disponible", "0 GB", 15),
            ("Uso", "0%", 8)
        ]

        for etiqueta, valor_predeterminado, ancho in metricas:
            self.etiquetas_ram[etiqueta] = self.crear_fila_metrica(marco_ram, etiqueta, valor_predeterminado, ancho)

    def crear_tarjeta_metrica(self, padre, titulo):
        marco = ttk.Frame(padre, style="Card.TFrame")
        marco.pack(fill='x', padx=10, pady=5)

        ttk.Label(marco, text=titulo, style="Title.TLabel").pack(anchor='w', pady=(10, 5), padx=10)

        return marco

    def crear_fila_metrica(self, padre, etiqueta, valor_predeterminado, ancho_valor):
        marco = ttk.Frame(padre, style="Card.TFrame")
        marco.pack(fill='x', padx=10, pady=2)

        ttk.Label(marco, text=etiqueta, style="Info.TLabel").pack(side='left')
        etiqueta_valor = ttk.Label(marco, text=valor_predeterminado, style="Value.TLabel", width=ancho_valor)
        etiqueta_valor.pack(side='right')

        return etiqueta_valor

    def crear_seccion_graficos(self):
        marco_graficos = ttk.Frame(self.contenedor_principal, style="Card.TFrame")
        marco_graficos.grid(row=1, column=1, rowspan=2, sticky='nsew', padx=5, pady=5)

        # Configurar figura con tamaño fijo
        self.figura = Figure(figsize=(8, 6), dpi=100, facecolor=self.colores['fondo_medio'])
        gs = GridSpec(2, 1, height_ratios=[1.2, 2], hspace=0.3)  # Aumentar el tamaño del gráfico circular

        # Gráfico circular con tamaño fijo
        self.ax_circular = self.figura.add_subplot(gs[0])
        self.configurar_grafico_circular()

        # Gráfico de línea con tamaño fijo
        self.ax_linea = self.figura.add_subplot(gs[1])
        self.configurar_grafico_linea()

        # Canvas con tamaño fijo
        self.canvas = FigureCanvasTkAgg(self.figura, marco_graficos)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=15, pady=15)

    def crear_seccion_procesos(self):
        marco_procesos = ttk.Frame(self.contenedor_principal, style="Card.TFrame")
        marco_procesos.grid(row=2, column=0, sticky='nsew', padx=5, pady=5)

        ttk.Label(marco_procesos, text="Procesos en Ejecución", style="Title.TLabel").pack(anchor='w', padx=15, pady=10)

        # Notebook para separar aplicaciones y procesos en segundo plano
        self.notebook_procesos = ttk.Notebook(marco_procesos, style="TNotebook")
        self.notebook_procesos.pack(fill='both', expand=True, padx=10, pady=5)

        # Pestaña para aplicaciones
        self.marco_app = ttk.Frame(self.notebook_procesos, style="Card.TFrame")
        self.notebook_procesos.add(self.marco_app, text="Aplicaciones")

        # Configurar treeviews para cada pestaña
        self.configurar_treeview_procesos(self.marco_app, "arbol_app")

    def configurar_treeview_procesos(self, padre, nombre_arbol):
        columnas = ("Nombre", "RAM (MB)")  # Eliminar columna "CPU %"
        arbol = ttk.Treeview(padre, columns=columnas, show="headings", style="Treeview")
        arbol.heading("Nombre", text="Nombre", anchor=tk.W)
        arbol.heading("RAM (MB)", text="RAM (MB)", anchor=tk.E)
        arbol.column("Nombre", width=200, anchor=tk.W)
        arbol.column("RAM (MB)", width=80, anchor=tk.E)

        # Configurar el estilo de las filas alternadas
        arbol.tag_configure('impar', background=self.colores['texto_primario'])
        arbol.tag_configure('par', background=self.colores['texto_primario'])

        # Agregar bordes a las celdas
        estilo = ttk.Style()
        estilo.configure("Treeview", rowheight=25)
        estilo.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
        estilo.configure("Treeview.Heading", relief="flat", borderwidth=1)

        barra_desplazamiento = ttk.Scrollbar(padre, orient="vertical", command=arbol.yview)
        arbol.configure(yscrollcommand=barra_desplazamiento.set)

        arbol.pack(side="left", fill="both", expand=True)
        barra_desplazamiento.pack(side="right", fill="y")

        setattr(self, nombre_arbol, arbol)

    def configurar_grafico_circular(self):
        self.ax_circular.clear()
        self.ax_circular.set_facecolor(self.colores['fondo_medio'])
        self.circular = self.ax_circular.pie([0, 100], colors=[self.colores['acento'], self.colores['fondo_claro']],
                                             startangle=90, counterclock=False, autopct='%1.1f%%',
                                             textprops={'color': self.colores['texto_primario']})
        self.ax_circular.set_title("Uso de RAM", color=self.colores['texto_primario'])

    def configurar_grafico_linea(self):
        self.ax_linea.set_facecolor(self.colores['fondo_medio'])
        self.ax_linea.tick_params(colors=self.colores['texto_secundario'])
        self.ax_linea.grid(True, color=self.colores['fondo_claro'], linestyle='--', alpha=0.5)

        for spine in self.ax_linea.spines.values():
            spine.set_color(self.colores['fondo_claro'])

        self.ax_linea.set_title("Uso de RAM a lo largo del tiempo", color=self.colores['texto_primario'])
        self.ax_linea.set_xlabel("Tiempo (Segundos)", color=self.colores['texto_secundario'])
        self.ax_linea.set_ylabel("Uso de RAM (%)", color=self.colores['texto_secundario'])

        # Gráfico de línea con 60 puntos iniciales
        self.linea, = self.ax_linea.plot(self.puntos_datos, color=self.colores['exito'], linewidth=2)

        

    def iniciar_hilos_actualizacion(self):
        # Hilos de actualización para métricas y gráficos
        self.hilo_ram = threading.Thread(target=self.actualizar_metricas_ram)
        self.hilo_ram.daemon = True
        self.hilo_ram.start()

        self.hilo_graficos = threading.Thread(target=self.actualizar_graficos)
        self.hilo_graficos.daemon = True
        self.hilo_graficos.start()

        self.hilo_procesos = threading.Thread(target=self.actualizar_procesos)
        self.hilo_procesos.daemon = True
        self.hilo_procesos.start()

    def actualizar_metricas_ram(self):
        while self.ejecutando:
            try:
                memoria = psutil.virtual_memory()
                memoria_total = memoria.total / (1024 ** 3)  # GB
                memoria_usada = memoria.used / (1024 ** 3)  # GB
                memoria_disponible = memoria.available / (1024 ** 3)  # GB
                porcentaje_memoria = memoria.percent

                self.cola_actualizacion.put(
                    ('ram', memoria_total, memoria_usada, memoria_disponible, porcentaje_memoria))

            except Exception as e:
                self.logger.error(f"Error al obtener métricas de RAM: {e}")

            time.sleep(1)

    def actualizar_graficos(self):
        while self.ejecutando:
            try:
                # Actualizar gráficos
                porcentaje_ram = psutil.virtual_memory().percent
                self.puntos_datos.append(porcentaje_ram)
                if len(self.puntos_datos) > self.max_puntos_datos:
                    self.puntos_datos.pop(0)

                self.cola_actualizacion.put(('grafico', porcentaje_ram))

            except Exception as e:
                self.logger.error(f"Error al actualizar gráficos: {e}")

            time.sleep(1)

    def actualizar_procesos(self):
        while self.ejecutando:
            try:
                aplicaciones = []
                procesos_segundo_plano = []
                for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_info', 'status']):
                    try:
                        pinfo = proc.as_dict(attrs=['name', 'cpu_percent', 'memory_info', 'status'])
                        if pinfo['status'] == psutil.STATUS_RUNNING:
                            memoria_mb = pinfo['memory_info'].rss / (1024 * 1024)  # Convertir a MB
                            if pinfo['name'].lower().endswith('.exe'):
                                aplicaciones.append((pinfo['name'], pinfo['cpu_percent'], memoria_mb))
                            else:
                                procesos_segundo_plano.append((pinfo['name'], pinfo['cpu_percent'], memoria_mb))
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass

                self.cola_actualizacion.put(('procesos', aplicaciones))
            except Exception as e:
                self.logger.error(f"Error al obtener procesos: {e}")

            time.sleep(5)  # Actualizar cada 5 segundos

    def actualizar_ui(self):
        try:
            while not self.cola_actualizacion.empty():
                actualizacion = self.cola_actualizacion.get_nowait()
                if actualizacion[0] == 'ram':
                    _, memoria_total, memoria_usada, memoria_disponible, porcentaje_memoria = actualizacion
                    self.etiquetas_ram["RAM Total"].config(text=f"{memoria_total:.2f} GB")
                    self.etiquetas_ram["RAM Usada"].config(text=f"{memoria_usada:.2f} GB")
                    self.etiquetas_ram["Disponible"].config(text=f"{memoria_disponible:.2f} GB")
                    self.etiquetas_ram["Uso"].config(text=f"{porcentaje_memoria:.1f}%")
                    # Actualizar gráfico circular de RAM
                    self.ax_circular.clear()
                    self.ax_circular.pie([porcentaje_memoria, 100 - porcentaje_memoria],
                                         colors=[self.colores['acento'], self.colores['fondo_claro']],
                                         startangle=90, counterclock=False, autopct='%1.1f%%',
                                         textprops={'color': self.colores['texto_primario']})
                    self.ax_circular.set_title("Uso de RAM", color=self.colores['texto_primario'])
                elif actualizacion[0] == 'grafico':
                    _, porcentaje_ram = actualizacion
                    self.linea.set_ydata(self.puntos_datos)
                    self.ax_linea.set_ylim(0, 100)
                    
                elif actualizacion[0] == 'procesos':
                    _, aplicaciones = actualizacion
                    self.actualizar_treeview_procesos(self.arbol_app, aplicaciones)
                    


            # Actualizar marca de tiempo
            self.marca_tiempo.config(text=time.strftime("%Y-%m-%d %H:%M:%S"))

            # Redibujar el canvas
            self.canvas.draw()

        except Exception as e:
            self.logger.error(f"Error al actualizar UI: {e}")

        if self.ejecutando:
            self.raiz.after(100, self.actualizar_ui)

    def actualizar_treeview_procesos(self, arbol, procesos):
        for item in arbol.get_children():
            arbol.delete(item)
        for i, proc in enumerate(procesos):
            arbol.insert("", "end", values=(proc[0], f"{proc[2]:.1f}"),  # Solo mostrar nombre y RAM
                         tags=('par' if i % 2 == 0 else 'impar'))

    def al_cerrar(self):
        self.ejecutando = False
        self.raiz.quit()


if __name__ == "__main__":
    raiz = tk.Tk()
    monitor = MonitorSistema(raiz)
    raiz.mainloop()