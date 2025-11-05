# 🚀 Proyecto FastAPI - RAG Pipeline

Este proyecto implementa una API basada en **FastAPI** junto con una pipeline de Recuperación Aumentada por Generación (**RAG**).  
Sigue los pasos a continuación para configurar el entorno virtual, instalar las dependencias y ejecutar el servidor con **Uvicorn**.

---

## 📦 Requisitos previos

Antes de comenzar, asegúrate de tener instalados los siguientes componentes:

- **Python 3.10 o superior**
- **Git**
- **PowerShell** (en Windows)

---

## ⚙️ Instalación y configuración del entorno

Abre PowerShell y ejecuta:

python -m venv venv
.\venv\Scripts\Activate
💡 Si obtienes un error sobre políticas de ejecución, usa:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
4️⃣ Instalar las dependencias
pip install -r requirements.txt
INICIAR SERVIDOR 
uvicorn app:app --reload --host 0.0.0.0 --port 8000 
