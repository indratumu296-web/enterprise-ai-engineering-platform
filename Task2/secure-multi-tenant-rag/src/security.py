from typing import Dict, Any


class SecurityManager:
    """
    Handles RBAC and multi-tenant security verification and translates user identity
    into secure database filters before retrieval occurs.
    """

    @staticmethod
    def build_security_filter(user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translates user identity into ChromaDB metadata filter conditions.
        Enforces tenant isolation, department matching, and clearance level bounds.
        """
        required_keys = ["tenant_id", "department", "clearance_level"]
        for key in required_keys:
            if key not in user:
                raise ValueError(f"Missing required identity field: {key}")

        return {
            "$and": [
                {"tenant_id": {"$eq": user["tenant_id"]}},
                {"department": {"$eq": user["department"]}},
                {"clearance_level": {"$lte": user["clearance_level"]}}
            ]
        }

    @staticmethod
    def validate_document_access(doc_metadata: Dict[str, Any], user: Dict[str, Any]) -> bool:
        """
        Post-check verification guard to validate if a chunk is accessible by the given user.
        """
        if doc_metadata.get("tenant_id") != user.get("tenant_id"):
            return False
        if doc_metadata.get("department") != user.get("department"):
            return False
        if doc_metadata.get("clearance_level", 999) > user.get("clearance_level", -1):
            return False
        return True
