from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class RequirementData:
    """要件データを表現するクラス"""
    id: str
    title: str
    description: str
    priority: str
    status: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 有効な値のリスト
    VALID_PRIORITIES = ["high", "medium", "low"]
    VALID_STATUSES = ["open", "in_progress", "completed", "closed"]

    def __post_init__(self):
        """バリデーションと初期化後の処理"""
        self._validate_required_fields()
        self._validate_priority()
        self._validate_status()

    def _validate_required_fields(self):
        """必須フィールドの検証"""
        if not self.id or not self.title or self.priority is None or self.status is None:
            raise ValueError("必須フィールド（id, title, priority, status）が必要です")

    def _validate_priority(self):
        """優先度の検証"""
        if self.priority not in self.VALID_PRIORITIES:
            raise ValueError(f"無効な優先度です。有効な値: {', '.join(self.VALID_PRIORITIES)}")

    def _validate_status(self):
        """ステータスの検証"""
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"無効なステータスです。有効な値: {', '.join(self.VALID_STATUSES)}")

    def to_dict(self) -> Dict[str, Any]:
        """データをディクショナリに変換"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "tags": self.tags,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RequirementData':
        """ディクショナリからインスタンスを作成"""
        return cls(**data) 