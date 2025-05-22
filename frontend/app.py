import re
import streamlit as st
from fastmcp import Client
import openai
from dotenv import load_dotenv
import os
import asyncio
import pandas as pd

# Configuración inicial
load_dotenv()

# Cliente MCP que se conecta a nuestro servidor usando SSE transport
mcp_client = Client("http://localhost:8000/sse")

st.title("Gestión de Usuarios - MCP 🚀")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Crear un contenedor en la sidebar para la tabla
if "table_container" not in st.session_state:
    st.session_state.table_container = st.sidebar.empty()


# Función para actualizar la tabla de usuarios
async def actualizar_tabla_usuarios():
    try:
        async with mcp_client as client:
            result = await client.call_tool("api_UsuariosController_findAll")
            users = eval(result[0].text)

            # Limpiar el contenedor antes de actualizar
            st.session_state.table_container.empty()

            # Crear nuevo contenido en el contenedor
            with st.session_state.table_container.container():
                st.subheader("📋 Usuarios Registrados")
                if users:
                    df = pd.DataFrame(users)
                    df = df[["id", "nombre", "email"]]  # No mostrar passwords
                    df.columns = ["ID", "Nombre", "Email"]
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No hay usuarios registrados")
    except Exception as e:
        st.session_state.table_container.empty()
        with st.session_state.table_container.container():
            st.error("Error al cargar usuarios")


# Input del usuario
user_input = st.text_input("Escribe tu mensaje:")


def extraer_id_usuario(texto):
    # Buscar patrones como "id=123", "ID: 123", "usuario 123", etc.
    patrones = [
        r"(?:id|ID)\s*[=:]\s*(\d+)",
        r"(?:usuario|user)\s+(\d+)",
        r"(?:número|numero|#)\s*(\d+)",
        r"id\s+(\d+)",
    ]

    for patron in patrones:
        match = re.search(patron, texto)
        if match:
            return int(match.group(1))
    return None


def extraer_datos_usuario(texto):
    texto = texto.replace(":", " ").replace(",", " ")
    email_match = re.search(r"[\w\.-]+@[\w\.-]+", texto)
    if not email_match:
        return None
    email = email_match.group(0)
    pass_match = re.search(r"(?:contraseña|password|clave)?\s*([^\s]+)$", texto)
    if not pass_match:
        return None
    password = pass_match.group(1)
    nombre_match = re.search(
        r"(?:usuario|alta|agrega|registrar|insertar)\s+a?\s*([\w\s]+?)\s+(?:con\s+el\s+email|email|correo|mail)?",
        texto,
        re.IGNORECASE,
    )
    if not nombre_match:
        return None
    nombre = nombre_match.group(1).strip()
    return nombre, email, password


client = openai.OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)


def responder_llm(mensaje_usuario):
    respuesta = client.chat.completions.create(
        model="orca-mini", messages=[{"role": "user", "content": mensaje_usuario}]
    )
    return respuesta.choices[0].message.content


def detectar_accion(texto):
    texto = texto.lower()
    if any(pal in texto for pal in ["eliminar", "borrar", "quitar"]):
        return "eliminar"
    elif any(pal in texto for pal in ["modificar", "cambiar", "actualizar"]):
        return "modificar"
    elif any(
        pal in texto
        for pal in ["consultar", "mostrar", "buscar", "ver", "listar", "obtener"]
    ):
        if "id" in texto or "usuario" in texto and not "usuarios" in texto:
            return "consultar_uno"
        return "consultar_todos"
    elif any(pal in texto for pal in ["agregar", "alta", "insertar", "registrar"]):
        return "agregar"
    else:
        return None


async def procesar_mensaje(user_input):
    accion = detectar_accion(user_input)
    try:
        async with mcp_client as client:
            if accion == "agregar":
                datos = extraer_datos_usuario(user_input)
                if datos:
                    nombre, email, password = datos
                    result = await client.call_tool(
                        "api_UsuariosController_create",
                        {"nombre": nombre, "email": email, "password": password},
                    )
                    created_user = eval(result[0].text)
                    # Actualizar tabla después de crear
                    await actualizar_tabla_usuarios()
                    return f"✅ Usuario {nombre} creado exitosamente con ID {created_user['id']}"
                else:
                    return "❌ No entendí los datos para agregar el usuario. Necesito nombre, email y contraseña."

            elif accion == "consultar_todos":
                result = await client.call_tool("api_UsuariosController_findAll")
                users = eval(result[0].text)
                # Actualizar tabla al consultar
                await actualizar_tabla_usuarios()
                if users:
                    response = "📋 Usuarios encontrados:\n"
                    for user in users:
                        response += (
                            f"• ID {user['id']}: {user['nombre']} ({user['email']})\n"
                        )
                    return response
                return "ℹ️ No hay usuarios registrados"

            elif accion == "consultar_uno":
                user_id = extraer_id_usuario(user_input)
                if not user_id:
                    return "❌ Por favor, especifica el ID del usuario (ejemplo: 'consultar usuario id=5')"
                try:
                    result = await client.call_tool(
                        "api_UsuariosController_findOne", {"id": user_id}
                    )
                    user = eval(result[0].text)
                    return f"👤 Usuario encontrado:\nID: {user['id']}\nNombre: {user['nombre']}\nEmail: {user['email']}"
                except Exception as e:
                    return f"❌ No se encontró el usuario con ID {user_id}"

            elif accion == "modificar":
                user_id = extraer_id_usuario(user_input)
                if not user_id:
                    return "❌ Por favor, especifica el ID del usuario (ejemplo: 'modificar usuario id=5 nombre=Nuevo Nombre')"

                nombre_match = re.search(r"nombre\s*=\s*([\w\s]+)", user_input)
                pass_match = re.search(
                    r"(?:contraseña|password|clave)\s*=\s*([^\s]+)", user_input
                )

                datos = {}
                if nombre_match:
                    datos["nombre"] = nombre_match.group(1).strip()
                if pass_match:
                    datos["password"] = pass_match.group(1)

                if datos:
                    try:
                        result = await client.call_tool(
                            "api_UsuariosController_update", {"id": user_id, **datos}
                        )
                        updated_user = eval(result[0].text)
                        # Actualizar tabla después de modificar
                        await actualizar_tabla_usuarios()
                        return f"✅ Usuario con ID {user_id} actualizado exitosamente a {updated_user['nombre']}"
                    except Exception as e:
                        return f"❌ No se encontró el usuario con ID {user_id}"
                else:
                    return "❌ No se especificaron datos para actualizar. Usa 'nombre=Nuevo Nombre' o 'password=nueva_contraseña'"

            elif accion == "eliminar":
                user_id = extraer_id_usuario(user_input)
                if not user_id:
                    return "❌ Por favor, especifica el ID del usuario (ejemplo: 'eliminar usuario id=5')"
                try:
                    result = await client.call_tool(
                        "api_UsuariosController_remove", {"id": user_id}
                    )
                    deleted_info = eval(result[0].text)
                    # Actualizar tabla después de eliminar
                    await actualizar_tabla_usuarios()
                    return f"✅ {deleted_info['mensaje']} (ID: {deleted_info['usuarioId']})"
                except Exception as e:
                    return f"❌ No se encontró el usuario con ID {user_id}"

            else:
                return responder_llm(user_input)

    except Exception as e:
        st.error(f"Error completo: {str(e)}")
        return f"❌ Error: {str(e)}"


# Actualizar tabla al inicio
if st.sidebar.button("🔄 Actualizar Lista"):
    asyncio.run(actualizar_tabla_usuarios())

# Procesar el mensaje cuando se envía
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    response = asyncio.run(procesar_mensaje(user_input))
    st.session_state.messages.append({"role": "assistant", "content": response})
    # Actualizar tabla después de cada acción
    asyncio.run(actualizar_tabla_usuarios())

# Mostrar el historial de mensajes
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
