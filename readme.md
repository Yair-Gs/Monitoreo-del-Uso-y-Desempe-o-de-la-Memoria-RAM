# 🖥️ MONITOREO DE USO Y DESEMPEÑO DE LA RAM

## 🧠 Descripción del Proyecto
Aplicación de escritorio desarrollada en Python para el monitoreo del uso de memoria RAM en tiempo real. Permite visualizar métricas del sistema, procesos activos y gráficos dinámicos para analizar el rendimiento del equipo.

---

## ⚙️ Tecnologías utilizadas
- Python  
- Tkinter (interfaz gráfica)  
- psutil (obtención de datos del sistema)  
- matplotlib (visualización de gráficos)  

---

## 🚀 Funcionalidades
- Monitoreo de RAM en tiempo real  
- Visualización de memoria total, usada y disponible  
- Gráfico circular del uso de RAM  
- Gráfico de líneas del consumo a lo largo del tiempo  
- Lista de procesos activos con consumo de memoria  
- Interfaz gráfica moderna e interactiva  

---

## 🔧 Instalación
Instalar dependencias necesarias:

```bash
pip install psutil matplotlib
```
## ▶️ Ejecución
Ejecutar el programa con:

```bash
python RamVF.py
```
## 🧩 Cómo funciona

El sistema utiliza la librería **psutil** para obtener información del uso de la memoria RAM y los procesos activos del sistema en tiempo real.

Los datos se actualizan mediante hilos (`threading`) y se gestionan usando una cola (`queue`), lo que permite una comunicación segura con la interfaz gráfica.

La interfaz fue desarrollada con **tkinter**, mientras que **matplotlib** se utiliza para generar gráficos dinámicos que representan el comportamiento del uso de memoria.

---

## 💡 Valor del proyecto

Permite analizar el rendimiento del sistema, identificar procesos que consumen demasiados recursos y mejorar la gestión de memoria, siendo útil en entornos académicos y profesionales.
