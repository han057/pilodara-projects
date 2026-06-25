from __future__ import annotations

import html

import streamlit as st

from app.api_client import (
    ApiError,
    comprobar_api,
    consultar,
    finalizar_sesion,
)
from app.schemas import ChatResponse, PasoRecorrido


st.set_page_config(
    page_title="Soporte Smart WiFi 6",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)


CSS = """
<style>
    :root {
        --bg: #fbfaf7;
        --ink: #1f2933;
        --muted: #687180;
        --line: #e8ded2;
        --accent: #16737a;
        --accent-soft: #e7f6f5;
        --blue: #3867d6;
        --blue-soft: #eef4ff;
        --gold: #d88a1d;
        --gold-soft: #fff4df;
        --coral: #d95b43;
        --coral-soft: #fff0ec;
        --ok: #4f8a5d;
        --ok-soft: #ecf7ef;
        --panel: #ffffff;
    }
    html, body, [data-testid="stAppViewContainer"] {
        background: var(--bg);
    }
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stStatusWidget"],
    .stDeployButton {
        display: none !important;
    }
    .block-container {
        max-width: 980px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fff7e8 0%, #f0f8ff 62%, #f7fbf7 100%);
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--ink);
    }
    [data-testid="stChatMessageAvatarAssistant"],
    [data-testid="stChatMessageAvatarUser"] {
        background: var(--accent-soft);
        color: var(--accent);
        border: 1px solid rgba(22, 115, 122, .16);
    }
    .stButton > button {
        border-color: var(--line);
        background: #ffffff;
        color: var(--ink);
        border-radius: 8px;
        min-height: 2.55rem;
    }
    .stButton > button:hover {
        border-color: rgba(47, 111, 115, .42);
        color: var(--accent);
        background: var(--accent-soft);
    }
    [class*="st-key-solved_"] .stButton > button:hover {
        border-color: rgba(79, 138, 93, .58) !important;
        color: #356b42 !important;
        background: var(--ok-soft) !important;
    }
    [class*="st-key-unsolved_"] .stButton > button:hover {
        border-color: rgba(217, 91, 67, .62) !important;
        color: #a43e2d !important;
        background: var(--coral-soft) !important;
    }
    .stButton > button:disabled {
        background: #f3f2ef;
        color: #9aa1aa;
    }
    [data-baseweb="select"] > div {
        background: rgba(255, 255, 255, .76);
        border-color: #ead7bf;
        border-radius: 10px;
    }
    h1, h2, h3 {
        letter-spacing: 0;
    }
    .topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        padding: 1rem 1.1rem;
        border: 1px solid #ead7bf;
        border-radius: 16px;
        margin-bottom: 1.25rem;
        background: linear-gradient(135deg, #fff7e8 0%, #edf8ff 58%, #edf8ef 100%);
        box-shadow: 0 10px 28px rgba(31, 41, 51, .06);
        position: relative;
        overflow: visible;
    }
    .hero-copy {
        display: flex;
        align-items: center;
        gap: .95rem;
    }
    .router-icon {
        width: 52px;
        height: 52px;
        border-radius: 14px;
        display: grid;
        place-items: center;
        flex: 0 0 auto;
        background: rgba(255, 255, 255, .72);
        border: 1px solid rgba(22, 115, 122, .18);
        box-shadow: inset 0 -10px 16px rgba(22, 115, 122, .05);
    }
    .router-icon svg {
        width: 32px;
        height: 32px;
        stroke: var(--accent);
        stroke-width: 1.8;
        fill: none;
        stroke-linecap: round;
        stroke-linejoin: round;
    }
    .topbar::before {
        content: "";
        position: absolute;
        left: 1.1rem;
        right: 1.1rem;
        bottom: -.5px;
        height: 3px;
        border-radius: 999px;
        background: linear-gradient(90deg, var(--accent), var(--gold), var(--coral), var(--blue));
    }
    .brand-title {
        font-size: 1.52rem;
        font-weight: 760;
        color: var(--ink);
        line-height: 1.32;
        padding-top: .05rem;
        overflow: visible;
    }
    .brand-subtitle {
        color: var(--muted);
        font-size: .96rem;
        margin-top: .15rem;
        max-width: 620px;
        line-height: 1.45;
    }
    .sidebar-note {
        color: var(--muted);
        font-size: .84rem;
        line-height: 1.35;
        margin: -.35rem 0 .75rem;
    }
    .question-preview {
        border: 1px solid #ead7bf;
        border-radius: 10px;
        background: rgba(255, 255, 255, .74);
        padding: .75rem .85rem;
        margin: .72rem 0 .85rem;
        color: var(--ink);
        font-size: .88rem;
        line-height: 1.38;
        word-break: normal;
        overflow-wrap: anywhere;
    }
    .flow-shell {
        border-top: 1px solid var(--line);
        margin-top: .65rem;
        padding-top: .8rem;
    }
    .flow-heading {
        color: var(--muted);
        font-size: .82rem;
        font-weight: 720;
        letter-spacing: .02em;
        text-transform: uppercase;
        margin-bottom: .55rem;
    }
    .flow-board {
        display: flex;
        flex-wrap: wrap;
        gap: .5rem;
        margin: .25rem 0 .75rem;
    }
    .flow-node {
        min-height: 34px;
        border: 1px solid var(--line);
        border-radius: 999px;
        padding: .38rem .68rem;
        background: #fff;
        display: inline-flex;
        align-items: center;
        gap: .38rem;
        width: auto;
        max-width: 100%;
    }
    .flow-node::before {
        content: "";
        width: .42rem;
        height: .42rem;
        border-radius: 999px;
        background: #b8c0ca;
        flex: 0 0 auto;
    }
    .flow-node .label {
        font-weight: 700;
        color: var(--ink);
        font-size: .78rem;
        line-height: 1.15;
        white-space: nowrap;
    }
    .flow-node .detail {
        display: none;
    }
    .flow-node.done {
        border-color: rgba(22, 115, 122, .35);
        background: var(--accent-soft);
    }
    .flow-node.done::before {
        background: var(--accent);
    }
    .flow-node.final {
        border-color: rgba(63, 115, 88, .42);
        background: var(--ok-soft);
    }
    .flow-node.final::before {
        background: var(--ok);
    }
    .flow-node.escalated {
        border-color: rgba(216, 138, 29, .42);
        background: var(--gold-soft);
    }
    .flow-node.escalated::before {
        background: var(--gold);
    }
    .flow-node.human {
        border-color: rgba(217, 91, 67, .42);
        background: var(--coral-soft);
    }
    .flow-node.human::before {
        background: var(--coral);
    }
    .flow-node.muted {
        opacity: .48;
        background: #fbfaf8;
    }
    .trace-row {
        border-left: 2px solid var(--line);
        padding: .34rem 0 .34rem .65rem;
        margin-bottom: .28rem;
    }
    .trace-title {
        font-weight: 700;
        color: var(--ink);
        font-size: .82rem;
    }
    .trace-detail {
        color: var(--muted);
        font-size: .77rem;
    }
    .resolution-actions {
        border: 1px solid var(--line);
        border-radius: 12px;
        background: rgba(255, 255, 255, .74);
        padding: .85rem;
        margin: .6rem 0 .9rem;
    }
    .resolution-title {
        color: var(--muted);
        font-size: .82rem;
        font-weight: 700;
        margin-bottom: .55rem;
    }
    @media (max-width: 920px) {
        .topbar {
            align-items: flex-start;
            flex-direction: column;
        }
    }
</style>
"""


ORDEN_NODOS = [
    ("entrada_llm", "Consulta recibida"),
    ("clasificador_entrada", "Clasificación"),
    ("recepcion", "Recepción"),
    ("rag_n1", "Ayuda consultada"),
    ("soporte_n1", "Respuesta preparada"),
    ("clasificador_n1", "Consulta resuelta"),
    ("rag_n2", "Revisión técnica"),
    ("soporte_n2", "Respuesta técnica"),
    ("clasificador_n2", "Validación técnica"),
    ("humano", "Atención humana"),
]


DETALLES_CLIENTE = {
    "entrada_llm": "Hemos recibido tu consulta.",
    "clasificador_entrada": "Comprobamos si el mensaje contiene una consulta sobre el router.",
    "recepcion": "Atendemos tu mensaje sin iniciar una consulta técnica.",
    "rag_n1": "Revisamos las preguntas frecuentes del servicio.",
    "soporte_n1": "Preparamos una respuesta con la información disponible.",
    "clasificador_n1": "Comprobamos si la respuesta resuelve la consulta.",
    "rag_n2": "Revisamos documentación técnica adicional.",
    "soporte_n2": "Preparamos una respuesta técnica.",
    "clasificador_n2": "Comprobamos si hace falta derivar la consulta.",
    "humano": "Derivamos la consulta a atención humana.",
}


AVATARES_NIVEL = {
    "Entrada": "📡",
    "Recepción": "👋",
    "N1": "💬",
    "N2": "🔧",
    "Humano": "👤",
    "Sistema": "ℹ️",
}


PREGUNTAS_FRECUENTES = [
    {"label": "Instalación sin técnico", "pregunta": "¿Puedo instalar yo mismo el router Smart WiFi 6 o necesito técnico?"},
    {"label": "Cambio desde ONT separada", "pregunta": "Si en mi instalación antigua hay una ONT separada, ¿qué hago al cambiar al Smart WiFi 6?"},
    {"label": "Primera conexión WiFi", "pregunta": "¿Cómo conecto un móvil, tablet o portátil por WiFi la primera vez?"},
    {"label": "Conexión por código QR", "pregunta": "¿Puedo conectarme escaneando el código QR del router?"},
    {"label": "Conexión por cable Ethernet", "pregunta": "¿Puedo conectar un equipo por cable Ethernet?"},
    {"label": "Nombre WiFi y claves", "pregunta": "¿Dónde está el nombre del WiFi, la clave y la contraseña de acceso al router?"},
    {"label": "Luces LED del router", "pregunta": "¿Qué significan las luces LED del router?"},
    {"label": "Internet rojo parpadeando", "pregunta": "¿Qué hago si la luz de Internet está roja parpadeando?"},
    {"label": "Internet rojo fijo", "pregunta": "¿Qué hago si la luz de Internet está roja fija?"},
    {"label": "Reinicio y configuración", "pregunta": "¿Reiniciar el router borra mi configuración?"},
    {"label": "Reiniciar correctamente", "pregunta": "¿Cómo reinicio correctamente el router?"},
    {"label": "Entrar en configuración local", "pregunta": "¿Cómo entro en la configuración local del router?"},
    {"label": "Compatibilidad app Smart WiFi", "pregunta": "¿Mi router Smart WiFi 6 es compatible con la app Smart WiFi?"},
    {"label": "Acceso a app Smart WiFi", "pregunta": "¿Cómo accedo a la app Smart WiFi?"},
    {"label": "Dispositivos conectados", "pregunta": "¿Cómo veo los dispositivos conectados?"},
    {"label": "Velocidad y cobertura", "pregunta": "¿Cómo mido velocidad y cobertura desde la app Smart WiFi?"},
    {"label": "Cambiar nombre WiFi", "pregunta": "¿Cómo cambio el nombre del WiFi?"},
    {"label": "Cambiar contraseña WiFi", "pregunta": "¿Cómo cambio la contraseña del WiFi?"},
    {"label": "Red WiFi de invitados", "pregunta": "¿Cómo creo una red WiFi de invitados?"},
    {"label": "Pausar o bloquear dispositivo", "pregunta": "¿Cómo pauso o bloqueo un dispositivo?"},
]


def inicializar_estado() -> None:
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = [
            {
                "role": "assistant",
                "content": "Hola, soy el soporte del Router Smart WiFi 6. Cuéntame qué ocurre.",
                "nivel": "Entrada",
                "respuesta": None,
            }
        ]
    if "ultima_respuesta" not in st.session_state:
        st.session_state.ultima_respuesta = None
    if "ultima_pregunta" not in st.session_state:
        st.session_state.ultima_pregunta = ""


@st.cache_data(ttl=12)
def comprobar_servicio():
    return comprobar_api()


def procesar_y_guardar(pregunta: str) -> None:
    st.session_state.ultima_pregunta = pregunta
    st.session_state.mensajes.append({"role": "user", "content": pregunta})
    try:
        respuesta = consultar(
            pregunta,
            session_id=st.session_state.get("session_id"),
        )
        st.session_state.session_id = respuesta.session_id
        st.session_state.mensajes.append(
            {
                "role": "assistant",
                "content": respuesta.respuesta,
                "nivel": respuesta.nivel,
                "respuesta": respuesta,
            }
        )
        st.session_state.ultima_respuesta = respuesta
    except ApiError:
        texto = (
            "El servicio no está disponible temporalmente. Inténtalo de nuevo "
            "en unos instantes."
        )
        st.session_state.mensajes.append(
            {"role": "assistant", "content": texto, "nivel": "Sistema", "respuesta": None}
        )
    except Exception:  # pragma: no cover - visible en la UI de clase
        texto = "Se produjo un error al procesar la consulta. Inténtalo de nuevo."
        st.session_state.mensajes.append(
            {"role": "assistant", "content": texto, "nivel": "Sistema", "respuesta": None}
        )


def revisar_no_solucionada() -> None:
    respuesta_anterior: ChatResponse | None = st.session_state.ultima_respuesta
    pregunta = st.session_state.ultima_pregunta
    if not respuesta_anterior or not pregunta:
        return

    st.session_state.mensajes.append(
        {
            "role": "user",
            "content": "No se solucionó la pregunta.",
        }
    )

    try:
        nueva_respuesta = consultar(
            pregunta,
            session_id=st.session_state.get("session_id"),
            feedback="insatisfecho",
        )
        st.session_state.session_id = nueva_respuesta.session_id

        st.session_state.mensajes.append(
            {
                "role": "assistant",
                "content": nueva_respuesta.respuesta,
                "nivel": nueva_respuesta.nivel,
                "respuesta": nueva_respuesta,
            }
        )
        st.session_state.ultima_respuesta = nueva_respuesta
    except ApiError:
        st.session_state.mensajes.append(
            {
                "role": "assistant",
                "content": "No he podido revisar la consulta en este momento. Inténtalo de nuevo.",
                "nivel": "Sistema",
                "respuesta": None,
            }
        )


def reiniciar_conversacion() -> None:
    session_id = st.session_state.get("session_id")
    if session_id:
        try:
            finalizar_sesion(session_id)
        except ApiError:
            pass
    st.session_state.clear()
    st.rerun()


def render_topbar() -> None:
    st.markdown(
        """
        <div class="topbar">
            <div class="hero-copy">
                <div class="router-icon" aria-hidden="true">
                    <svg viewBox="0 0 48 48">
                        <rect x="9" y="24" width="30" height="12" rx="4"></rect>
                        <path d="M15 24c2.4-4.2 5.4-6.3 9-6.3s6.6 2.1 9 6.3"></path>
                        <path d="M19 19c1.3-1.5 3-2.3 5-2.3s3.7.8 5 2.3"></path>
                        <path d="M24 14v-4"></path>
                        <path d="M15 36v3M33 36v3"></path>
                        <circle cx="17" cy="30" r="1.3"></circle>
                        <circle cx="23" cy="30" r="1.3"></circle>
                        <circle cx="29" cy="30" r="1.3"></circle>
                    </svg>
                </div>
                <div>
                    <div class="brand-title">Bienvenido al soporte del Router Smart WiFi 6</div>
                    <div class="brand-subtitle">Te ayudamos con la instalación, la red WiFi y la configuración de tu router.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_recorrido(respuesta: ChatResponse | None) -> None:
    if not respuesta:
        st.info("El detalle aparecerá con la primera consulta.")
        return

    pasos = {paso.id: paso for paso in respuesta.pasos} if respuesta else {}
    html_nodes = []
    for node_id, etiqueta in ORDEN_NODOS:
        paso = pasos.get(node_id)
        if paso is None:
            continue
        clase = _clase_paso(paso)
        detalle = DETALLES_CLIENTE.get(node_id, paso.detalle)
        if node_id == "humano" and paso:
            clase += " human"
        html_nodes.append(
            f'<div class="flow-node {html.escape(clase)}" title="{html.escape(detalle)}">'
            f'<div class="label">{html.escape(etiqueta)}</div>'
            "</div>"
        )
    st.markdown(
        '<div class="flow-shell"><div class="flow-heading">Resumen de la atención</div>'
        '<div class="flow-board">'
        + "".join(html_nodes)
        + "</div></div>",
        unsafe_allow_html=True,
    )


def render_detalle(respuesta: ChatResponse | None) -> None:
    if not respuesta:
        return

    for paso in respuesta.pasos:
        nombre = _nombre_paso_cliente(paso.id, paso.nombre)
        detalle = DETALLES_CLIENTE.get(paso.id, paso.detalle)
        st.markdown(
            '<div class="trace-row">'
            f'<div class="trace-title">{html.escape(nombre)} · {html.escape(_estado_cliente(paso.estado))}</div>'
            f'<div class="trace-detail">{html.escape(detalle)}</div>'
            "</div>",
            unsafe_allow_html=True,
        )


def _clase_paso(paso: PasoRecorrido | None) -> str:
    if paso is None:
        return "muted"
    if paso.estado == "final":
        return "final"
    if paso.estado == "escalado":
        return "escalated"
    if paso.estado == "completado":
        return "done"
    return "muted"


def _nombre_paso_cliente(paso_id: str, fallback: str) -> str:
    for node_id, etiqueta in ORDEN_NODOS:
        if node_id == paso_id:
            return etiqueta
    return fallback


def _estado_cliente(estado: str) -> str:
    return {
        "completado": "completado",
        "final": "resuelto",
        "escalado": "derivado",
        "omitido": "omitido",
        "pendiente": "pendiente",
    }.get(estado, estado)


def render_sidebar() -> None:
    with st.sidebar:
        st.subheader("Preguntas frecuentes")
        st.markdown(
            '<div class="sidebar-note">Elige una consulta y pulsa responder para enviarla al flujo.</div>',
            unsafe_allow_html=True,
        )
        opciones = ["Selecciona una pregunta"] + [
            item["label"] for item in PREGUNTAS_FRECUENTES
        ]
        seleccion = st.selectbox(
            "Consulta",
            opciones,
            label_visibility="collapsed",
        )
        pregunta_seleccionada = None
        if seleccion != "Selecciona una pregunta":
            indice = opciones.index(seleccion) - 1
            pregunta_seleccionada = PREGUNTAS_FRECUENTES[indice]
            st.markdown(
                f"""
                <div class="question-preview">
                    {html.escape(pregunta_seleccionada["pregunta"])}
                </div>
                """,
                unsafe_allow_html=True,
            )
        if st.button(
            "Responder",
            use_container_width=True,
            disabled=pregunta_seleccionada is None,
        ):
            procesar_y_guardar(pregunta_seleccionada["pregunta"])
            st.rerun()

        st.divider()
        if st.button("Reiniciar conversación", use_container_width=True):
            reiniciar_conversacion()


def render_chat() -> None:
    for mensaje in st.session_state.mensajes:
        avatar = (
            "🙂"
            if mensaje["role"] == "user"
            else AVATARES_NIVEL.get(
                mensaje.get("nivel"),
                "👤",
            )
        )
        with st.chat_message(mensaje["role"], avatar=avatar):
            if mensaje.get("nivel"):
                st.caption(mensaje["nivel"])
            st.markdown(_limpiar_respuesta_cliente(mensaje["content"]))


def render_resolution_actions() -> None:
    respuesta = st.session_state.ultima_respuesta
    if respuesta is None or respuesta.nivel in {"Entrada", "Recepción", "Sistema"}:
        return

    proxima_accion = {
        "N1": "Si no se solucionó, revisará soporte técnico.",
        "N2": "Si no se solucionó, se derivará a atención humana.",
        "Humano": "La consulta ya está derivada a atención humana.",
    }.get(respuesta.nivel, "Revisaremos la consulta.")
    st.markdown(
        f"""
        <div class="resolution-actions">
            <div class="resolution-title">¿La respuesta ha solucionado tu consulta?</div>
            <div style="color: var(--muted); font-size: .82rem;">{html.escape(proxima_accion)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_ok, col_no = st.columns(2)
    action_key = f"{respuesta.nivel}_{len(st.session_state.mensajes)}"
    with col_ok:
        if st.button(
            "Pregunta solucionada",
            use_container_width=True,
            type="primary",
            key=f"solved_{action_key}",
        ):
            reiniciar_conversacion()
    with col_no:
        if st.button(
            "No se solucionó la pregunta",
            use_container_width=True,
            key=f"unsolved_{action_key}",
        ):
            revisar_no_solucionada()
            st.rerun()


def _limpiar_respuesta_cliente(texto: str) -> str:
    normalizado = texto.casefold()
    marcadores = (
        "fuentes consultadas:",
        "dificultad:",
        "tiempo estimado:",
        "soporte/técnico:",
        "soporte / técnico:",
        "estado documental:",
    )
    posiciones = [
        normalizado.find(marcador)
        for marcador in marcadores
        if normalizado.find(marcador) >= 0
    ]
    if posiciones:
        texto = texto[: min(posiciones)]
    return texto.rstrip(" \n\t.;,:-")


def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    inicializar_estado()
    try:
        comprobar_servicio()
    except ApiError:
        pass
    render_sidebar()
    render_topbar()

    render_chat()
    render_resolution_actions()
    with st.expander("Ver detalle de la atención", expanded=False):
        render_recorrido(st.session_state.ultima_respuesta)
        render_detalle(st.session_state.ultima_respuesta)

    pregunta = st.chat_input("Pregunta sobre el Router Smart WiFi 6")
    if pregunta:
        with st.spinner("Revisando tu consulta..."):
            procesar_y_guardar(pregunta)
        st.rerun()


if __name__ == "__main__":
    main()
