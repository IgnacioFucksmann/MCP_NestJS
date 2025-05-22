import re
import streamlit as st
from fastmcp import Client
import openai
from dotenv import load_dotenv
import os
import asyncio

# Configuración inicial
load_dotenv()

# Cliente MCP que se conecta a nuestro servidor usando SSE transport
mcp_client = Client("http://localhost:8000/sse")

st.title("Gestión de Usuarios - MCP 🚀")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Add a sidebar for user ID input
user_id = st.sidebar.number_input(
    "ID del usuario (para modificar/eliminar/consultar):", min_value=1, value=1
)

user_input = st.text_input("Escribe tu mensaje:")


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
        async with mcp_client:  # Use context manager for the client
            if accion == "agregar":
                datos = extraer_datos_usuario(user_input)
                if datos:
                    nombre, email, password = datos
                    # Usar el tool api_UsuariosController_create
                    result = await mcp_client.call_tool(
                        "api_UsuariosController_create",
                        {"nombre": nombre, "email": email, "password": password},
                    )
                    # Parse the response
                    created_user = eval(result[0].text)
                    return f"✅ Usuario {nombre} creado exitosamente con ID {created_user['id']}"
                else:
                    return "❌ No entendí los datos para agregar el usuario. Necesito nombre, email y contraseña."

            elif accion == "consultar_todos":
                # Usar el tool api_UsuariosController_findAll
                result = await mcp_client.call_tool("api_UsuariosController_findAll")
                users = eval(result[0].text)
                if users:
                    response = "📋 Usuarios encontrados:\n"
                    for user in users:
                        response += (
                            f"• ID {user['id']}: {user['nombre']} ({user['email']})\n"
                        )
                    return response
                return "ℹ️ No hay usuarios registrados"

            elif accion == "consultar_uno":
                # Usar el tool api_UsuariosController_findOne
                result = await mcp_client.call_tool(
                    "api_UsuariosController_findOne", {"id": user_id}
                )
                user = eval(result[0].text)
                return f"👤 Usuario encontrado:\nID: {user['id']}\nNombre: {user['nombre']}\nEmail: {user['email']}"

            elif accion == "modificar":
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
                    # Usar el tool api_UsuariosController_update
                    result = await mcp_client.call_tool(
                        "api_UsuariosController_update", {"id": user_id, **datos}
                    )
                    updated_user = eval(result[0].text)
                    return f"✅ Usuario con ID {user_id} actualizado exitosamente a {updated_user['nombre']}"
                else:
                    return "❌ No se especificaron datos para actualizar. Usa 'nombre=Nuevo Nombre' o 'password=nueva_contraseña'"

            elif accion == "eliminar":
                # Usar el tool api_UsuariosController_remove
                result = await mcp_client.call_tool(
                    "api_UsuariosController_remove", {"id": user_id}
                )
                deleted_info = eval(result[0].text)
                return f"✅ {deleted_info['mensaje']} (ID: {deleted_info['usuarioId']})"

            else:
                # Si no es una acción de usuario, usamos el LLM
                return responder_llm(user_input)

    except Exception as e:
        st.error(f"Error completo: {str(e)}")
        return f"❌ Error: {str(e)}"


# Procesar el mensaje cuando se envía
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    response = asyncio.run(procesar_mensaje(user_input))
    st.session_state.messages.append({"role": "assistant", "content": response})

# Mostrar el historial de mensajes
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
