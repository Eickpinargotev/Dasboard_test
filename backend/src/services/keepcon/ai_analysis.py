import json
import logging
import time
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)


class KeepconAIAnalyzer:
    def __init__(self, config):
        self.config = config

    PROMPT = (
        "Analiza comentarios sobre Claro Ecuador. "
        "Responde SOLO JSON valido con esta estructura exacta: "
        '{"results":[{"id":"id","ai_sentiment":"positive|negative|neutral|no sentiment","ai_location":"Ciudad, Provincia/Region, Pais|null"}]}. '

        "El sentimiento SIEMPRE debe evaluarse desde la perspectiva reputacional de Claro Ecuador. "
        "No analices el sentimiento general del texto, analiza unicamente si el comentario favorece, perjudica o es irrelevante para Claro Ecuador. "

        "Usa 'negative' SOLO cuando el comentario exprese una experiencia negativa, reclamo, critica, burla, frustracion, amenaza de cancelacion, denuncia o insatisfaccion DIRECTAMENTE relacionada con Claro Ecuador, sus servicios o atencion. "
        "Incluye problemas de internet, llamadas, cobertura, WhatsApp, soporte, facturacion, cobros, lentitud, caidas, mala atencion, tiendas, tecnicos, contratos, promociones o cualquier mala experiencia atribuida a Claro. "
        "Tambien usa 'negative' cuando el usuario exprese molestia implicita aunque no use palabras agresivas. "
        "Ejemplo negative: 'No tengo internet y Claro no responde'. "

        "Usa 'positive' SOLO cuando el comentario elogie, recomiende o exprese satisfaccion DIRECTA hacia Claro Ecuador, sus servicios o experiencia. "
        "Debe existir una valoracion claramente favorable hacia Claro. "
        "Ejemplo positive: 'Claro tiene mejor señal que las otras operadoras'. "

        "Usa 'neutral' cuando el comentario mencione a Claro Ecuador pero sea informativo, noticioso, publicitario, conversacional o descriptivo SIN expresar una experiencia positiva o negativa hacia Claro. "
        "Incluye noticias, campañas, historias personales, publicaciones de terceros, saludos simples, preguntas simples y contenido donde Claro solo sea mencionado incidentalmente. "
        "Ejemplos neutral: "
        "'@ClaroEcua hola Claro', "
        "'Adriana superó un cáncer y ahora ayuda a otros pacientes @ClaroEcua', "
        "'Claro transmitirá el evento mañana'. "

        "Usa 'no sentiment' SOLO cuando el texto no tenga suficiente contexto para determinar una postura o cuando la mencion a Claro sea irrelevante, ambigua, automatica o aislada. "
        "Ejemplos no sentiment: "
        "'@ClaroEcua', "
        "'Claro.', "
        "'RT @ClaroEcua'. "

        "NO marques 'negative' si la critica es contra otra empresa, persona, gobierno, entidad o marca distinta de Claro aunque Claro sea mencionado. "
        "Si otra empresa recibe la critica y Claro queda mejor posicionado, eso favorece a Claro. "
        "Ejemplo: "
        "'Netlife es una mierda, con Claro me va mejor' = positive. "

        "Si el comentario compara empresas, el sentimiento debe reflejar unicamente el impacto hacia Claro Ecuador. "
        "Si Claro queda mejor => positive. "
        "Si Claro queda peor => negative. "
        "Si no hay conclusion clara => neutral. "

        "Extrae una ubicacion SOLO cuando el comentario mencione explicitamente una ciudad, provincia, canton, sector o pais. "
        "No infieras ubicaciones por contexto, modismos, numeros telefonicos o conocimiento externo. "
        "Si la ubicacion es una ciudad de Ecuador normalizala como 'Ciudad, Ecuador'. "
        "Si no existe una ubicacion explicita usa null."
    )

    def analyze_missing(self, records):
        return self.analyze_missing_with_stats(records)["results"]

    def analyze_missing_with_stats(self, records):
        started = time.perf_counter()
        pending = [
            {"id": item["id"], "text": item.get("text", "")}
            for item in records
            if item.get("id") and not item.get("ai_sentiment")
        ]
        stats = {
            "pending_records": len(pending),
            "chunks": 0,
            "analyzed_records": 0,
            "duration_ms": 0,
        }
        if not pending:
            return {"results": {}, "stats": stats}

        if not self.config.openai_api_key:
            logger.warning("No OpenAI API key found. Leaving Keepcon AI analysis empty.")
            stats["duration_ms"] = int((time.perf_counter() - started) * 1000)
            return {"results": {}, "stats": stats}

        analyzed = {}
        for index in range(0, len(pending), self.config.openai_sync_chunk_size):
            stats["chunks"] += 1
            analyzed.update(self._analyze_chunk(pending[index:index + self.config.openai_sync_chunk_size]))
        stats["analyzed_records"] = len(analyzed)
        stats["duration_ms"] = int((time.perf_counter() - started) * 1000)
        return {"results": analyzed, "stats": stats}

    def _payload(self, pending):
        return {
            "model": self.config.openai_model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": self.PROMPT},
                {"role": "user", "content": json.dumps({"comments": pending}, ensure_ascii=False)},
            ],
        }

    def _analyze_chunk(self, pending):
        payload = self._payload(pending)
        headers = {
            "Authorization": f"Bearer {self.config.openai_api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(self.config.openai_url, json=payload, headers=headers, timeout=60)
            if response.status_code != 200:
                logger.error("OpenAI Keepcon analysis error: %s - %s", response.status_code, response.text)
                return {}

            content = response.json()["choices"][0]["message"]["content"]
            return self._parse_analysis_content(content)
        except Exception as exc:
            logger.error("Error during OpenAI Keepcon analysis request: %s", exc)
            return {}

    def _parse_analysis_content(self, content):
        parsed = json.loads(content)
        now = datetime.now(timezone.utc).isoformat()
        analyzed = {}

        for result in parsed.get("results", []):
            item_id = str(result.get("id", ""))
            sentiment = str(result.get("ai_sentiment", "no sentiment")).lower()
            if sentiment not in {"positive", "negative", "neutral", "no sentiment"}:
                sentiment = "no sentiment"
            location = self._clean_location(result.get("ai_location"))

            if item_id:
                analyzed[item_id] = {
                    "ai_sentiment": sentiment,
                    "ai_location": str(location).strip(),
                    "ai_sentiment_model": self.config.openai_model,
                    "ai_sentiment_analyzed_at": now,
                }

        return analyzed

    def _clean_location(self, value):
        if value is None:
            return ""
        parts = [
            part.strip()
            for part in str(value).split(",")
            if part.strip() and part.strip().lower() not in {"null", "none", "unknown", "unrecognized"}
        ]
        return ", ".join(parts)
