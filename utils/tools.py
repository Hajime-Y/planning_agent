"""
Smolagentsツール集

このモジュールはSmolagentsのCodeAgentで使用できるツールを提供します。
各ツールは@toolデコレータでラップされています。
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

# テスト時の互換性問題を回避するためのフォールバック
try:
    from smolagents import tool
except ImportError:
    # モックツールデコレータ（テスト用）
    def tool(func):
        """テスト用のモックツールデコレータ"""
        return func

from .file_manager import FileManager, save_yaml_file, load_yaml_file


# ファイルマネージャのインスタンス
# データディレクトリの場所はここで一元管理
_file_manager = FileManager(base_dir="./data")


@tool
def save_yaml(file_path: str, data: Dict[str, Any]) -> str:
    """YAMLファイルにデータを保存します。
    
    Args:
        file_path: 保存先のファイルパス
        data: 保存するデータ
        
    Returns:
        保存したファイルのパス
    """
    return save_yaml_file(file_path, data)


@tool
def load_yaml(file_path: str) -> Dict[str, Any]:
    """YAMLファイルからデータを読み込みます。
    
    Args:
        file_path: 読み込むファイルパス
        
    Returns:
        読み込んだデータ
    """
    return load_yaml_file(file_path)


@tool
def save_requirements(task_id: str, requirements: Dict[str, Any]) -> str:
    """タスクの要件データをYAMLファイルに保存します。
    
    Args:
        task_id: タスクID
        requirements: 要件データ
        
    Returns:
        保存したファイルのパス
    """
    return _file_manager.save_requirements(task_id, requirements)


@tool
def load_requirements(task_id: str) -> Dict[str, Any]:
    """タスクの要件データをYAMLファイルから読み込みます。
    
    Args:
        task_id: タスクID
        
    Returns:
        読み込んだ要件データ
    """
    return _file_manager.load_requirements(task_id)


@tool
def save_plan(plan_id: str, plan: Dict[str, Any]) -> str:
    """プランデータをYAMLファイルに保存します。
    
    Args:
        plan_id: プランID
        plan: プランデータ
        
    Returns:
        保存したファイルのパス
    """
    file_path, version = _file_manager.save_plan(plan_id, plan)
    return f"プランを保存しました: {file_path} (バージョン: {version})"


@tool
def load_plan(plan_id: str) -> Dict[str, Any]:
    """プランデータをYAMLファイルから読み込みます。
    
    Args:
        plan_id: プランID
        
    Returns:
        読み込んだプランデータ
    """
    return _file_manager.load_plan(plan_id)


@tool
def save_issue(task_id: str, issue: Dict[str, Any]) -> str:
    """課題データをYAMLファイルに保存します。
    
    Args:
        task_id: タスクID
        issue: 課題データ
        
    Returns:
        保存したファイルのパス
    """
    return _file_manager.save_issue(task_id, issue)


@tool
def load_issues(task_id: str) -> Dict[str, Any]:
    """課題データをYAMLファイルから読み込みます。
    
    Args:
        task_id: タスクID
        
    Returns:
        読み込んだ課題データ
    """
    return _file_manager.load_issues(task_id)


@tool
def list_plans() -> List[str]:
    """全プランIDのリストを取得します。
    
    Returns:
        プランIDのリスト
    """
    return _file_manager.list_plans()


@tool
def list_requirements() -> List[str]:
    """全タスクIDのリストを取得します。
    
    Returns:
        タスクIDのリスト
    """
    return _file_manager.list_requirements()


@tool
def backup_plan(plan_id: str) -> Optional[str]:
    """プランのバックアップを作成します。
    
    Args:
        plan_id: プランID
        
    Returns:
        バックアップファイルのパス、またはNone（失敗時）
    """
    return _file_manager.backup_plan(plan_id)


@tool
def delete_plan(plan_id: str) -> bool:
    """プランを削除します（履歴も含む）。
    
    Args:
        plan_id: プランID
        
    Returns:
        削除に成功したかどうか
    """
    return _file_manager.delete_plan(plan_id) 