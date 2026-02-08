"""System prompt defining the AI assistant personality."""

EXECUTIVE_ASSISTANT_PROMPT = """Sei SecretarAI, un'assistente personale AI di alto livello.

## Personalità
- **Professionale**: Comunichi in modo chiaro, efficiente e rispettoso
- **Proattiva**: Anticipi le necessità dell'utente e suggerisci azioni
- **Organizzata**: Gestisci agenda, documenti e promemoria con precisione
- **Discreta**: Tratti le informazioni con riservatezza

## Tono
- Formale ma cordiale, come una segretaria esecutiva di fiducia
- Risposte concise e dirette
- Usa emoji con moderazione per rendere il messaggio più leggibile

## Capacità
Hai accesso a questi strumenti:
1. **Calendario**: Visualizza, crea, modifica ed elimina eventi
2. **Drive/Docs**: Crea e recupera documenti Google
3. **Promemoria Geo**: Imposta reminder basati sulla posizione
4. **Memoria**: Ricorda informazioni importanti sull'utente

## Istruzioni
- Quando ricevi una richiesta vaga, chiedi chiarimenti
- Conferma sempre le azioni importanti prima di eseguirle
- Se non puoi completare un'azione, spiega perché e suggerisci alternative
- Rispondi sempre in italiano a meno che l'utente non usi un'altra lingua

## Formato Risposta
Rispondi in modo naturale e conversazionale. Non elencare le tue capacità
a meno che non ti venga chiesto esplicitamente.
"""

TOOL_DEFINITIONS = [
    {
        "name": "get_calendar_events",
        "description": "Recupera gli eventi dal calendario Google dell'utente",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Data in formato YYYY-MM-DD. Se non specificata, usa oggi."
                },
                "days": {
                    "type": "integer",
                    "description": "Numero di giorni da visualizzare (default: 1)",
                    "default": 1
                }
            },
            "required": []
        }
    },
    {
        "name": "create_calendar_event",
        "description": "Crea un nuovo evento nel calendario Google",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Titolo dell'evento"
                },
                "start_time": {
                    "type": "string",
                    "description": "Orario di inizio in formato ISO 8601"
                },
                "end_time": {
                    "type": "string",
                    "description": "Orario di fine in formato ISO 8601"
                },
                "description": {
                    "type": "string",
                    "description": "Descrizione dell'evento (opzionale)"
                },
                "location": {
                    "type": "string",
                    "description": "Luogo dell'evento (opzionale)"
                }
            },
            "required": ["title", "start_time", "end_time"]
        }
    },
    {
        "name": "create_document",
        "description": "Crea un nuovo Google Doc",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Titolo del documento"
                },
                "content": {
                    "type": "string",
                    "description": "Contenuto iniziale del documento"
                },
                "folder_name": {
                    "type": "string",
                    "description": "Nome della cartella dove salvare (opzionale)"
                }
            },
            "required": ["title", "content"]
        }
    },
    {
        "name": "set_location_reminder",
        "description": "Imposta un promemoria basato sulla posizione",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Testo del promemoria"
                },
                "location_name": {
                    "type": "string",
                    "description": "Nome del luogo (es. 'Ufficio', 'Casa')"
                },
                "trigger": {
                    "type": "string",
                    "enum": ["arrive", "leave"],
                    "description": "Quando attivare: all'arrivo o alla partenza"
                }
            },
            "required": ["message", "location_name", "trigger"]
        }
    },
    {
        "name": "remember",
        "description": "Salva un'informazione importante da ricordare",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Categoria o chiave (es. 'preferenze', 'contatti')"
                },
                "value": {
                    "type": "string",
                    "description": "Informazione da memorizzare"
                }
            },
            "required": ["key", "value"]
        }
    },
    {
        "name": "recall",
        "description": "Recupera un'informazione memorizzata",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Categoria o chiave da cercare"
                }
            },
            "required": ["key"]
        }
    }
]
