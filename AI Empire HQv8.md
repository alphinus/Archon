# AI Empire HQ v8 – Manifest für eine adaptive KI-Entwicklungsplattform

Dieses Dokument ist die zentrale "Single Source of Truth" für die Entwicklung des AI Empire HQ. Jede KI oder jeder Agent, der an diesem Projekt arbeitet, muss sich an die folgende Prozessordnung halten:
1.  **LESEN:** Lies dieses gesamte Dokument, bevor du mit der Arbeit beginnst.
2.  **AUSFÜHREN:** Wähle den nächsten offenen Punkt aus der Master-Checkliste.
3.  **PROTOKOLLIEREN:** Trage deine Arbeitssession in das Logbuch ein.
4.  **AKTUALISIEREN:** Aktualisiere den Status der bearbeiteten Punkte in der Master-Checkliste.
5.  **COMMITEN:** Committe deine Änderungen am Code und an diesem Dokument.

---

## LOGBUCH DER KI-AGENTEN

*   **Session-ID:** `20251127-1430-Gemini-Init`
    *   **Agent:** `Gemini Pro (via Google)`
    *   **Aktionen:** Analyse von `v7.md`, Entwurf der Vision `v8`, Erstellung des Manifests.
*   **Session-ID:** `20251127-1445-Gemini-Konfiguration`
    *   **Agent:** `Gemini Pro (via Google)`
    *   **Aktionen:** `.env` und `docker-compose.yml` aktualisiert.
*   **Session-ID:** `20251127-1500-Gemini-SQL-Korrektur`
    *   **Agent:** `Gemini Pro (via Google)`
    *   **Aktionen:** Nach Experten-Review wurde ein neues, konsolidiertes Migrations-Skript `V3` erstellt.
*   **Session-ID:** `20251127-1515-Gemini-SQL-Finalisierung`
    *   **Agent:** `Gemini Pro (via Google)`
    *   **Aktionen:** Nach `gen_random_uuid()`-Fehler wurde das finale Skript `V4_agent_work_orders_setup.sql` erstellt.
*   **Session-ID:** `20251127-1530-GPT-Mini-5-SQL-Ausführung`
    *   **Agent:** `GPT Mini 5 (via Benutzer)`
    *   **Aktionen:** Das finale SQL-Migrationsskript `migration/V4_agent_work_orders_setup.sql` wurde innerhalb von Supabase erfolgreich repariert und ausgeführt.
*   **Session-ID:** `20251127-1600-Gemini-Phase-1-Abschluss`
    *   **Agent:** `Gemini Pro (via Google)`
    *   **Aktionen:** Phase 1 erfolgreich abgeschlossen und committet.
*   **Session-ID:** `20251127-1615-Gemini-AAL-Design`
    *   **Agent:** `Gemini Pro (via Google)`
    *   **Aktionen:** Detailliertes Architektur-Design für die "Agent Abstraction Layer" entworfen und in `DESIGN_AAL.md` dokumentiert. Phase 2 Implementierungsplan erstellt.
*   **Session-ID:** `20251127-1700-Gemini-AAL-Implementierung`
    *   **Agent:** `Gemini Pro (via Google)`
    *   **Aktionen:**
        *   AAL Core-Struktur (`aal/`, `aal/providers/`, `aal/models.py`) erstellt.
        *   AAL Interfaces (`aal/interfaces.py`) definiert (`IAgentProvider`).
        *   `ClaudeProvider` (`anthropic_provider.py`) als erste Implementierung erstellt und an neues Interface angepasst.
        *   `AgentService` (`aal/service.py`) mit einfachem Router erstellt.
        *   AAL-Service in `workflow_orchestrator.py` und `workflow_operations.py` integriert, um direkte `claude`-Abhängigkeit zu ersetzen.
        *   `OpenAIProvider` (`openai_provider.py`) als zweite Implementierung erstellt.
        *   `pyproject.toml` um `openai` und `PyYAML` Abhängigkeiten erweitert.
        *   `agents.yml` als Provider-Konfigurationsdatei erstellt.
        *   `ProviderRegistry` (`aal/registry.py`) implementiert, um Provider dynamisch zu laden und `model_configs` zu übergeben.
        *   `AgentService`-Router um Fähigkeiten-basiertes Routing, Kosten-Optimierung und Fallback-Logik erweitert.
        *   Strukturiertes Logging in `AgentService` für Observability integriert.
        *   **Phase 2: Strategische Erweiterung - Teil 1: Agent Abstraction Layer VOLLSTÄNDIG IMPLEMENTIERT.**

---

## STATUS QUO
- **System:** Phase 1 (Stabilisierung) ist abgeschlossen. Das System läuft stabil mit Supabase-Backend. Phase 2.1 (AAL) ist vollständig implementiert.
- **Unmittelbares Ziel:** Verifizierung der AAL-Implementierung und Vorbereitung auf die nächste strategische Erweiterung.

---

## STRATEGISCHE VISION V8
1.  **Agenten-Abstraktionsschicht:** Agenten-agnostische Architektur.
2.  **Event-gesteuerte Architektur & "Everything as a Playbook":** Erweiterung auf Marketing, Deployment etc.
3.  **Dynamische Feedback-Schleife:** Selbstlernendes System durch Rückführung von Live-Daten.

---

## MASTER-CHECKLISTE

### Phase 1: Stabilisierung & Fundament (Basis v7)
- [x] **Speicherplatz:** Manuell sichergestellt.
- [x] **Konfiguration .env:** Abgeschlossen.
- [x] **Konfiguration docker-compose:** Abgeschlossen.
- [x] **Datenbank-Migration:** Abgeschlossen.
- [x] **Systemstart:** Abgeschlossen.
- [x] **Verifizierung (Work Orders):** Abgeschlossen.
- [x] **Verifizierung (Gesamtsystem):** Abgeschlossen.
- [x] **Secrets-Check:** Abgeschlossen und committet.

### Phase 2: Strategische Erweiterung - Teil 1: Agent Abstraction Layer
- [x] **Architektur:** Design der "Agent Abstraction Layer" entworfen und in `DESIGN_AAL.md` dokumentiert.
- [x] **2.1.1 - AAL Core-Struktur:** Erstelle die Verzeichnisstruktur (`aal/`, `aal/providers/`) und die Pydantic-Modelle (`AgentRequest`, `AgentResponse`).
- [x] **2.1.2 - AAL Interfaces:** Definiere das `IAgentProvider`-Interface (abstrakte Basisklasse).
- [x] **2.1.3 - Provider Nr. 1 (Claude):** Implementiere den `ClaudeProvider` als erste konkrete Implementierung.
- [x] **2.1.4 - AAL Service (Simple):** Implementiere den AAL-Service mit einem einfachen Router, der nur explizite Provider-Namen (`preferred_provider`) unterstützt.
- [x] **2.1.5 - Integration:** Integriere den AAL-Service in den bestehenden `Agent Work Orders`-Dienst und ersetze die direkte `claude`-Abhängigkeit.
- [x] **2.1.6 - Provider Nr. 2 (OpenAI):** Implementiere einen `OpenAIProvider`, um die Abstraktion zu validieren.
- [x] **2.1.7 - Provider Registry & Config:** Implementiere das Laden der Provider aus der `agents.yml`-Konfigurationsdatei.
- [x] **2.1.8 - AAL Router (Advanced):** Erweitere den Router um das Fähigkeiten-basierte Routing und die Kosten-Optimierung.
- [x] **2.1.9 - Observability:** Integriere strukturiertes Logging für jeden AAL-Aufruf, das Kosten, Latenz und Token-Verbrauch erfasst.

### Phase 2: Strategische Erweiterung - Teil 2: (Als nächstes zu definieren)
- [ ] **Architektur:** Design der Event-gesteuerten Architektur entwerfen.
- [ ] ...

---

## NÄCHSTE SCHRITTE

1.  **Aktion:** Erstelle einen Commit, der die Implementierung der Agent Abstraction Layer zusammenfasst.
2.  **Frage:** Nach dem Commit können wir das System neu starten und die Funktionalität der AAL verifizieren.
