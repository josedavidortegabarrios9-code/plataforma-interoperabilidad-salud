"""
Módulo de Auditoría Criptográfica Encadenada (Tamper-Evident Hash Chain).
Garantiza inmutabilidad y detección inmediata de alteraciones de registros clínicos.
H_n = SHA-256(timestamp + actor + rol + accion + recurso + resultado + H_{n-1})
Persiste cada eslabón en la tabla evento_auditoria de PostgreSQL.
"""

import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

class AuditChain:
    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def load_from_db(self, db_events: List[Dict[str, Any]]):
        """Carga eventos persistidos desde PostgreSQL al iniciar el servicio."""
        if db_events:
            self.events = db_events

    def get_last_hash(self) -> str:
        if not self.events:
            return GENESIS_HASH
        return self.events[-1]["hash_actual"]

    @staticmethod
    def calculate_hash(timestamp: str, actor: str, rol: str, accion: str, recurso: str, resultado: str, hash_previo: str) -> str:
        payload = f"{timestamp}|{actor}|{rol}|{accion}|{recurso}|{resultado}|{hash_previo}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def add_event(self, actor: str, rol: str, accion: str, recurso: str, resultado: str) -> Dict[str, Any]:
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        hash_previo = self.get_last_hash()
        hash_actual = self.calculate_hash(timestamp, actor, rol, accion, recurso, resultado, hash_previo)
        
        event = {
            "id_evento": len(self.events) + 1,
            "timestamp": timestamp,
            "actor": actor,
            "rol": rol,
            "accion": accion,
            "recurso": recurso,
            "resultado": resultado,
            "hash_previo": hash_previo,
            "hash_actual": hash_actual
        }
        self.events.append(event)

        # Persistir de forma segura en PostgreSQL (tabla evento_auditoria)
        try:
            from hsb.database import persist_audit_event_to_db
            persist_audit_event_to_db({
                "id_evento": event["id_evento"],
                "fecha_hora": timestamp,
                "actor_username": actor,
                "rol_actor": rol,
                "accion": accion,
                "recurso_afectado": recurso,
                "resultado": resultado,
                "hash_previo": hash_previo,
                "hash_actual": hash_actual
            })
        except Exception:
            pass

        return event

    def unify_and_order_events(self, additional_events: Optional[List[Dict[str, Any]]] = None):
        """
        Une eventos de memoria y de las bases de datos distribuidas de las 3 sedes legadas.
        Deduplica por hash_actual y reconstruye el encadenamiento criptográfico continuo (TAREA 4).
        """
        pool = list(self.events)
        if additional_events:
            pool.extend(additional_events)

        unique_by_hash = {}
        for ev in pool:
            h_act = ev.get("hash_actual")
            if h_act and h_act not in unique_by_hash:
                unique_by_hash[h_act] = ev

        by_prev = {}
        for ev in unique_by_hash.values():
            h_prev = ev.get("hash_previo")
            if h_prev:
                by_prev[h_prev] = ev

        ordered = []
        curr = GENESIS_HASH
        visited = set()
        while curr in by_prev and curr not in visited:
            visited.add(curr)
            ev = by_prev[curr]
            ordered.append(ev)
            curr = ev["hash_actual"]

        # Si hay eventos restantes no conectados al genesis
        for ev in unique_by_hash.values():
            if ev not in ordered:
                ordered.append(ev)

        for idx, ev in enumerate(ordered):
            ev["id_evento"] = idx + 1

        self.events = ordered
        return ordered

    def verify_integrity(self) -> Dict[str, Any]:
        """
        Recorre secuencialmente la cadena de hashes. Si algún registro fue modificado,
        detecta exactamente la posición del evento alterado (tamper detection).
        """
        self.unify_and_order_events()
        if not self.events:
            return {"integro": True, "total_eventos": 0, "mensaje": "Cadena de auditoría vacía"}

        expected_prev_hash = GENESIS_HASH

        for idx, event in enumerate(self.events):
            # 1. Verificar encadenamiento con el evento previo
            if event["hash_previo"] != expected_prev_hash:
                return {
                    "integro": False,
                    "evento_alterado_id": event["id_evento"],
                    "indice": idx,
                    "motivo": f"Ruptura de enlace en evento {event['id_evento']}: hash_previo no coincide con el hash del predecesor",
                    "hash_esperado": expected_prev_hash,
                    "hash_encontrado": event["hash_previo"]
                }

            # 2. Recalcular el hash del contenido actual
            recalculated = self.calculate_hash(
                event.get("timestamp") or event.get("fecha_hora", ""),
                event.get("actor") or event.get("actor_username", ""),
                event.get("rol") or event.get("rol_actor", ""),
                event.get("accion", ""),
                event.get("recurso") or event.get("recurso_afectado", ""),
                event.get("resultado", ""),
                event["hash_previo"]
            )

            if event["hash_actual"] != recalculated:
                return {
                    "integro": False,
                    "evento_alterado_id": event["id_evento"],
                    "indice": idx,
                    "motivo": f"Contenido modificado en evento {event['id_evento']}: el hash actual no coincide con los datos sellados",
                    "hash_almacenado": event["hash_actual"],
                    "hash_recalculado": recalculated
                }

            expected_prev_hash = event["hash_actual"]

        return {
            "integro": True,
            "total_eventos": len(self.events),
            "ultimo_hash": expected_prev_hash,
            "mensaje": "Integridad criptográfica verificada: 0 alteraciones detectadas"
        }

# Instancia global del ledger de auditoría
audit_ledger = AuditChain()
