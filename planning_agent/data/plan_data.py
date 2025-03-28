from typing import Dict, Any, List, TypedDict, Optional
from dataclasses import dataclass, field

class StepData(TypedDict):
    """ステップデータの型定義"""
    order: int              # ステップの順序
    action: str             # 実行アクション
    description: str        # 説明
    expected_output: Optional[str]  # 想定成果物
    actual_output: Optional[str]    # 実際の成果物
    dependencies: Optional[List[int]]  # 依存タスク番号のリスト

@dataclass
class PlanData:
    """プランデータを表現するクラス"""
    id: str
    title: str
    description: str
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    steps: List[StepData] = field(default_factory=list)

    # 有効なステータス値
    VALID_STATUSES = ["draft", "in_progress", "completed"]

    def __post_init__(self):
        """バリデーションと初期化後の処理"""
        self._validate_required_fields()
        # ステータスのバリデーションはセッターで行われるため、ここでは行わない
        self._validate_steps()
        self._sort_steps()
        
        # status属性を_statusにコピー（@property経由での設定を行うため）
        self._status = self.status
        
    def _validate_required_fields(self):
        """必須フィールドの検証"""
        if not self.id or not self.title or self.status is None:
            raise ValueError("必須フィールド（id, title, status）が必要です")

    def _validate_steps(self):
        """ステップデータの検証"""
        if not self.steps:
            return

        orders = set()
        for step in self.steps:
            # 必須フィールドの確認
            if not all(key in step for key in ["order", "action", "description"]):
                raise ValueError("各ステップには order, action, description が必要です")
            
            # orderの型と値のチェック
            if not isinstance(step["order"], int):
                raise ValueError(f"order は整数である必要があります: {step['order']}")
            if step["order"] < 0:
                raise ValueError(f"order は非負である必要があります: {step['order']}")
            
            # orderの重複チェック
            if step["order"] in orders:
                raise ValueError(f"重複するorder値が存在します: {step['order']}")
            orders.add(step["order"])

    def _sort_steps(self):
        """ステップを順序で並び替え"""
        if self.steps:
            self.steps.sort(key=lambda x: x["order"])

    def to_dict(self) -> Dict[str, Any]:
        """データをディクショナリに変換"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "steps": self.steps,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlanData':
        """ディクショナリからインスタンスを作成"""
        return cls(**data)

    @property
    def status(self) -> str:
        """ステータスのゲッター"""
        return self._status

    @status.setter
    def status(self, value: str):
        """ステータスのセッター（バリデーション付き）"""
        if value not in self.VALID_STATUSES:
            raise ValueError(f"無効なステータスです。有効な値: {', '.join(self.VALID_STATUSES)}")
        self._status = value 