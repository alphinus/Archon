# DESIGN DOKUMENT: Agent Abstraction Layer (AAL)

**Status:** Entwurf | **Version:** 1.0 | **Autor:** Gemini Pro

---

## 1. Vision & Kernprinzipien

Die Agent Abstraction Layer (AAL) ist das Herzstück der intelligenten Ausführung im AI Empire HQ. Ihre Aufgabe ist es, den Rest des Systems vollständig von der Komplexität und der sich ständig verändernden Landschaft der KI-Modelle zu entkoppeln.

**Kernprinzipien:**

*   **Agenten-Agnostisch:** Das System spricht eine einzige, universelle Sprache. Es weiß nicht und muss nicht wissen, ob im Hintergrund Claude, GPT-5, Gemini 2.0, ein Open-Source-Modell via Ollama oder ein spezialisierter Finetune-Agent arbeitet.
*   **Plug-and-Play-Architektur:** Das Hinzufügen, Entfernen oder Austauschen eines KI-Agenten ist eine reine Konfigurationsänderung, vergleichbar mit dem Einstecken einer neuen Grafikkarte. Kein einziger Code-Bestandteil des Kernsystems muss dafür geändert werden.
*   **Fähigkeiten-basiertes Routing (Capability-Based Routing):** Das System fordert nicht "ein Modell", sondern "eine Fähigkeit" an. Es sagt: "Ich brauche einen Experten für Python-Code-Refactoring mit großem Kontextfenster" und die AAL findet den besten verfügbaren Agenten für diesen Job.
*   **Intelligente Orchestrierung:** Die AAL ist mehr als eine Weiterleitung. Sie ist ein intelligenter Router, der Entscheidungen basierend auf Kosten, Geschwindigkeit, Qualität und Systemlast treffen kann. Sie kann bei Fehlern automatisch auf einen Fallback-Agenten ausweichen.
*   **Absolute Beobachtbarkeit (Observability):** Jeder einzelne Aufruf durch die AAL wird mit detaillierten Metriken (Latenz, Kosten, Token-Verbrauch, Erfolg/Fehler) protokolliert. Wir wissen zu jeder Zeit, was das System tut und was es kostet.

---

## 2. Architektur & Komponenten

Die AAL besteht aus mehreren losen gekoppelten Komponenten, die über klar definierte Schnittstellen kommunizieren.

```
+--------------------------+        +--------------------------------+
|   Work Order Service     |------->|   Agent Abstraction Layer (AAL)|
+--------------------------+        |      (Zentraler Service)       |
                                    +--------------------------------+
                                                   |
                                                   |
                 +---------------------------------V---------------------------------+
                 |                Agent Router / Orchestrator                        |
                 | (Entscheidet, welcher Provider genutzt wird)                      |
                 +---------------------------------V---------------------------------+
                                                   |
                 +---------------------------------V---------------------------------+
                 |                     Provider Registry                             |
                 | (Kennt alle verfügbaren Agenten-Provider)                         |
                 +-----------------V-----------------V-----------------V-------------+
                                   |                 |                 |
                       +-----------+---------+ +-----+-----------+ +---+-------------+
                       | IAgentProvider      | | IAgentProvider  | | IAgentProvider  |
                       +=====================+ +=================+ +=================+
                       |  ClaudeProvider     | |  OpenAIProvider | |  OllamaProvider |
                       | (claude.ai API)     | | (OpenAI API)    | | (Lokale Modelle)|
                       +---------------------+ +-----------------+ +-----------------+
```

**Komponenten im Detail:**

1.  **Agent Abstraction Layer (AAL Service):** Der einzige Einstiegspunkt für den Rest des Systems. Er empfängt einen standardisierten `AgentRequest` und liefert einen `AgentResponse` zurück.
2.  **Agent Router / Orchestrator:** Das Gehirn der AAL. Er nimmt den `AgentRequest` entgegen und entscheidet auf Basis von Regeln (expliziter Name, geforderte Fähigkeiten, Kosten-Limit), welcher Provider die Anfrage bearbeiten soll.
3.  **Provider Registry:** Ein einfaches Register, das beim Start alle verfügbaren Agenten-Provider (Plugins) lädt und für den Router bereithält.
4.  **`IAgentProvider` (Interface):** Ein abstrakter Vertrag (eine Python `ABC`), den jeder konkrete Provider implementieren *muss*. Er definiert Methoden wie `get_name()`, `get_capabilities()` und `async execute(request)`.
5.  **Konkrete Provider (`ClaudeProvider`, `OpenAIProvider`, ...):** Dies sind die "Treiber" für die spezifischen KI-Modelle. Jeder Provider ist dafür verantwortlich, den standardisierten `AgentRequest` in das spezifische API-Format des jeweiligen Dienstes zu übersetzen und dessen Antwort zurück in einen standardisierten `AgentResponse` zu konvertieren.

---

## 3. Kernkonzepte im Detail

### 3.1. Standardisiertes Kommunikationsprotokoll

Alle Interaktionen erfolgen über zwei Pydantic-Modelle:

```python
class AgentRequest(BaseModel):
    prompt: str
    conversation_history: list[dict] = []
    
    # Routing-Präferenzen
    preferred_provider: Optional[str] = None # z.B. "openai"
    required_capabilities: list[str] = [] # z.B. ["code_generation", "context_window_200k"]
    
    # Kosten- & Qualitätskontrolle
    max_cost_usd: Optional[float] = None
    quality_tier: Literal["low", "medium", "high"] = "medium"
    
    # Modell-Parameter
    temperature: float = 0.7
    max_tokens: int = 4096

class AgentResponse(BaseModel):
    content: str
    provider_used: str
    model_name_used: str
    
    # Metadaten zur Beobachtbarkeit
    usage: dict # Enthält input_tokens, output_tokens
    cost_usd: float
    latency_ms: int
    
    error: Optional[str] = None
```

### 3.2. Das Provider-Plugin-System

Ein neuer Agent wird durch das Hinzufügen einer neuen Python-Datei im `aal/providers`-Verzeichnis integriert:

```python
# aal/providers/anthropic_provider.py

class ClaudeProvider(IAgentProvider):
    def get_name(self) -> str:
        return "anthropic"

    def get_capabilities(self) -> list[str]:
        return ["text_generation", "code_generation", "context_window_200k", "tool_use"]

    async def execute(self, request: AgentRequest) -> AgentResponse:
        # Hier findet die Übersetzung zum Anthropic API-Format statt
        # ...
        # API-Aufruf
        # ...
        # Rück-Übersetzung in AgentResponse
        return AgentResponse(...)
```

Eine Konfigurationsdatei `agents.yml` registriert diesen Provider:
```yaml
providers:
  anthropic:
    class: aal.providers.anthropic_provider.ClaudeProvider
    api_key_env: "ANTHROPIC_API_KEY"
    models:
      claude-3-opus:
        capabilities: ["quality_high", "context_window_200k"]
        cost_per_million_tokens: {input: 15.0, output: 75.0}
      claude-3-sonnet:
        capabilities: ["quality_medium", "context_window_200k"]
        cost_per_million_tokens: {input: 3.0, output: 15.0}
```

### 3.3. Fähigkeiten-basiertes Routing & Orchestrierung

Der Router implementiert eine Chain-of-Responsibility-Logik:
1.  **Explizite Anforderung?** Wurde `preferred_provider` im Request gesetzt? Wenn ja, nutze ihn.
2.  **Fähigkeiten-Filter:** Filtere alle Provider, die *alle* `required_capabilities` erfüllen.
3.  **Qualitäts-Filter:** Wähle aus den verbleibenden Providern diejenigen, die dem `quality_tier` entsprechen.
4.  **Kosten-Optimierung:** Wähle aus den verbleibenden den Provider mit dem günstigsten Modell.
5.  **Fallback-Logik:** Wenn der ausgewählte Provider einen Fehler liefert (z.B. API-Ausfall), nimmt der Router den nächstbesten Provider aus der gefilterten Liste und versucht es erneut.

---

## 4. Implementierungsplan (Neue Phase-2-Checkliste)

Dies wird die neue, detaillierte Checkliste für den ersten Teil von Phase 2.

- [ ] **2.1.1 - AAL Core-Struktur:** Erstelle die Verzeichnisstruktur (`aal/`, `aal/providers/`) und die Pydantic-Modelle (`AgentRequest`, `AgentResponse`).
- [ ] **2.1.2 - AAL Interfaces:** Definiere das `IAgentProvider`-Interface (abstrakte Basisklasse).
- [ ] **2.1.3 - Provider Nr. 1 (Claude):** Implementiere den `ClaudeProvider` als erste konkrete Implementierung.
- [ ] **2.1.4 - AAL Service (Simple):** Implementiere den AAL-Service mit einem einfachen Router, der nur explizite Provider-Namen (`preferred_provider`) unterstützt.
- [ ] **2.1.5 - Integration:** Integriere den AAL-Service in den bestehenden `Agent Work Orders`-Dienst und ersetze die direkte `claude`-Abhängigkeit.
- [ ] **2.1.6 - Provider Nr. 2 (OpenAI):** Implementiere einen `OpenAIProvider`, um die Abstraktion zu validieren.
- [ ] **2.1.7 - Provider Registry & Config:** Implementiere das Laden der Provider aus der `agents.yml`-Konfigurationsdatei.
- [ ] **2.1.8 - AAL Router (Advanced):** Erweitere den Router um das Fähigkeiten-basierte Routing und die Kosten-Optimierung.
- [ ] **2.1.9 - Observability:** Integriere strukturiertes Logging für jeden AAL-Aufruf, das Kosten, Latenz und Token-Verbrauch erfasst.

---
