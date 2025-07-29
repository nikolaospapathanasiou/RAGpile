import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from neo4j import Driver

logger = logging.getLogger(__name__)


@dataclass
class Knowledge:
    user_id: str
    subject: str
    predicate: str
    object: str
    confidence: float
    created_at: datetime


def _run_query(
    driver: Driver, query: str, parameters: Optional[Dict[str, str]] = None
) -> List[Dict[str, dict]]:
    with driver.session() as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]


class Neo4jClient:
    def __init__(self, driver: Driver):
        self.driver = driver

    def create_knowledge(  # pylint: disable=too-many-arguments too-many-positional-arguments
        self,
        user_id: str,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 1.0,
    ) -> Knowledge:
        query = """
        MERGE (u:User {id: $user_id})
        MERGE (s:Entity {name: $subject, user_id: $user_id})
        MERGE (o:Entity {name: $obj, user_id: $user_id})
        MERGE (s)-[r:RELATION {
            predicate: $predicate, 
            confidence: $confidence,
            created_at: datetime()
        }]->(o)
        MERGE (u)-[:OWNS]->(s)
        MERGE (u)-[:OWNS]->(o)
        RETURN r
        """

        res = _run_query(
            self.driver,
            query,
            {
                "user_id": user_id,
                "subject": subject,
                "predicate": predicate,
                "obj": obj,
                "confidence": str(confidence),
            },
        )
        return Knowledge(
            user_id=user_id,
            subject=subject,
            predicate=predicate,
            object=obj,
            confidence=confidence,
            created_at=datetime.fromisoformat(str(res[0]["created_at"])),
        )
