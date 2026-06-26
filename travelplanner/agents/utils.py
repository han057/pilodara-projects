import re


def strip_thinking(text: str) -> str:
    """Elimina bloques <think>...</think> que genera qwen3 en modo razonamiento."""
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned.strip()


def format_history(history: list, max_turns: int = 4) -> str:
    """Formatea el historial reciente de conversación para el prompt."""
    if not history:
        return ""
    recent = history[-(max_turns * 2):]
    lines = ["Conversación previa con el viajero:"]
    for msg in recent:
        role = "Viajero" if msg.get("role") == "user" else "Marco"
        content = msg.get("text", msg.get("content", msg.get("message", "")))
        truncated = content[:300] + "..." if len(content) > 300 else content
        lines.append(f"{role}: {truncated}")
    return "\n".join(lines)


class ThinkingStreamFilter:
    """Filtra los bloques <think>...</think> de qwen3 en modo streaming chunk a chunk."""

    LOOKING = 0   # aún no hemos visto <think>
    THINKING = 1  # dentro del bloque de razonamiento
    DONE = 2      # bloque terminado, pasar todo directamente

    def __init__(self):
        self._state = self.LOOKING
        self._buf = ""

    def feed(self, chunk: str) -> str:
        """Procesa un chunk y devuelve el texto que debe enviarse al cliente."""
        if self._state == self.DONE:
            return chunk

        self._buf += chunk

        if self._state == self.LOOKING:
            if "<think>" in self._buf:
                idx = self._buf.index("<think>")
                pre = self._buf[:idx]
                self._buf = self._buf[idx:]
                self._state = self.THINKING
                return pre

            # Si el buffer crece sin ver '<', o supera 50 chars, no hay bloque thinking
            if "<" not in self._buf or len(self._buf) > 50:
                out = self._buf
                self._buf = ""
                self._state = self.DONE
                return out
            return ""

        # state == THINKING
        if "</think>" in self._buf:
            idx = self._buf.index("</think>") + len("</think>")
            after = self._buf[idx:].lstrip("\n")
            self._buf = ""
            self._state = self.DONE
            return after
        return ""

    def flush(self) -> str:
        """Devuelve texto pendiente al final del stream."""
        if self._state == self.DONE:
            return ""
        out = self._buf
        self._buf = ""
        return out
