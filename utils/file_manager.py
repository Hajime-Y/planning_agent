"""
ファイル管理ユーティリティ

このモジュールはYAML形式のファイル操作と履歴管理機能を提供します。
smolagentsのCodeAgentのツールとして使用することを想定しています。
"""

import os
import shutil
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple


class FileManager:
    """
    YAML形式のファイル操作と履歴管理機能を提供するクラス
    
    Attributes:
        base_dir (Path): ファイル保存の基本ディレクトリ
        requirements_dir (Path): 要件ファイル保存ディレクトリ
        plans_dir (Path): プランファイル保存ディレクトリ
        issues_dir (Path): 課題ファイル保存ディレクトリ
        history_dir (Path): 履歴ファイル保存ディレクトリ
    """
    
    def __init__(self, base_dir: str = "./data"):
        """
        FileManagerを初期化する
        
        Args:
            base_dir: ファイル保存の基本ディレクトリ（デフォルト: "./data"）
        """
        self.base_dir = Path(base_dir)
        self.requirements_dir = self.base_dir / "requirements"
        self.plans_dir = self.base_dir / "plans"
        self.issues_dir = self.base_dir / "issues"
        self.history_dir = self.base_dir / "history"
        
        # 必要なディレクトリを作成
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """必要なディレクトリを作成する"""
        directories = [
            self.base_dir,
            self.requirements_dir,
            self.plans_dir, 
            self.issues_dir,
            self.history_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _get_timestamp(self) -> str:
        """現在のタイムスタンプを取得する（ファイル名用）"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _save_yaml(self, file_path: Path, data: Dict[str, Any]) -> None:
        """
        YAMLファイルを保存する
        
        Args:
            file_path: 保存先のファイルパス
            data: 保存するデータ
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """
        YAMLファイルを読み込む
        
        Args:
            file_path: 読み込むファイルパス
            
        Returns:
            読み込んだデータ
            
        Raises:
            FileNotFoundError: ファイルが存在しない場合
            yaml.YAMLError: YAMLの解析に失敗した場合
        """
        if not file_path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                return yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"YAMLの解析に失敗しました: {e}")
    
    def save_requirements(self, task_id: str, requirements: Dict[str, Any]) -> str:
        """
        要件ファイルを保存する
        
        Args:
            task_id: タスクID
            requirements: 要件データ
            
        Returns:
            保存したファイルのパス
        """
        # タイムスタンプがない場合は追加
        if "created_at" not in requirements:
            requirements["created_at"] = datetime.now().isoformat()
        
        # task_idがない場合は追加
        if "task_id" not in requirements:
            requirements["task_id"] = task_id
        
        file_path = self.requirements_dir / f"{task_id}.yaml"
        self._save_yaml(file_path, requirements)
        return str(file_path)
    
    def load_requirements(self, task_id: str) -> Dict[str, Any]:
        """
        要件ファイルを読み込む
        
        Args:
            task_id: タスクID
            
        Returns:
            読み込んだ要件データ
        """
        file_path = self.requirements_dir / f"{task_id}.yaml"
        return self._load_yaml(file_path)
    
    def save_plan(self, plan_id: str, plan: Dict[str, Any]) -> Tuple[str, int]:
        """
        プランファイルを保存する
        
        Args:
            plan_id: プランID
            plan: プランデータ
            
        Returns:
            保存したファイルのパスとバージョン番号のタプル
        """
        # 既存のプランを読み込み、バージョンを増やす
        version = 1
        try:
            existing_plan = self.load_plan(plan_id)
            version = existing_plan.get("version", 0) + 1
        except FileNotFoundError:
            # 新規プランの場合は何もしない
            pass
        
        # メタデータを更新
        plan["updated_at"] = datetime.now().isoformat()
        if "created_at" not in plan:
            plan["created_at"] = plan["updated_at"]
        plan["version"] = version
        
        # 既存プランが存在する場合は履歴を作成
        if version > 1:
            self.backup_plan(plan_id)
        
        file_path = self.plans_dir / f"{plan_id}.yaml"
        self._save_yaml(file_path, plan)
        return str(file_path), version
    
    def load_plan(self, plan_id: str) -> Dict[str, Any]:
        """
        プランファイルを読み込む
        
        Args:
            plan_id: プランID
            
        Returns:
            読み込んだプランデータ
        """
        file_path = self.plans_dir / f"{plan_id}.yaml"
        return self._load_yaml(file_path)
    
    def backup_plan(self, plan_id: str) -> Optional[str]:
        """
        プランの履歴を作成する
        
        Args:
            plan_id: プランID
            
        Returns:
            バックアップファイルのパス、またはNone（失敗時）
        """
        try:
            source_path = self.plans_dir / f"{plan_id}.yaml"
            if not source_path.exists():
                return None
            
            # 現在のプランを読み込み
            plan = self._load_yaml(source_path)
            version = plan.get("version", 0)
            
            # 履歴ディレクトリ
            plan_history_dir = self.history_dir / plan_id
            plan_history_dir.mkdir(parents=True, exist_ok=True)
            
            # バックアップファイルパス
            timestamp = self._get_timestamp()
            backup_path = plan_history_dir / f"v{version}_{timestamp}.yaml"
            
            # バックアップを作成
            shutil.copy2(source_path, backup_path)
            return str(backup_path)
        except Exception as e:
            print(f"プランのバックアップに失敗しました: {e}")
            return None
    
    def save_issue(self, task_id: str, issue: Dict[str, Any]) -> str:
        """
        課題ファイルを保存する
        
        Args:
            task_id: タスクID
            issue: 課題データ
            
        Returns:
            保存したファイルのパス
        """
        # 既存の課題ファイルを読み込む
        issues_data = {"task_id": task_id, "issues": []}
        file_path = self.issues_dir / f"{task_id}.yaml"
        
        try:
            if file_path.exists():
                issues_data = self._load_yaml(file_path)
        except Exception:
            # ファイルが存在しないか、読み込みに失敗した場合は新規作成
            pass
        
        # 課題にIDがない場合は生成
        if "issue_id" not in issue:
            issue_count = len(issues_data.get("issues", []))
            issue["issue_id"] = f"issue-{task_id}-{issue_count + 1:03d}"
        
        # 作成日時がない場合は追加
        if "created_at" not in issue:
            issue["created_at"] = datetime.now().isoformat()
        
        # 更新日時を設定
        issues_data["updated_at"] = datetime.now().isoformat()
        
        # 課題を追加または更新
        issue_id = issue["issue_id"]
        issues = issues_data.get("issues", [])
        
        for i, existing_issue in enumerate(issues):
            if existing_issue.get("issue_id") == issue_id:
                # 既存の課題を更新
                issues[i] = issue
                break
        else:
            # 新規課題を追加
            issues.append(issue)
        
        issues_data["issues"] = issues
        
        # ファイルに保存
        self._save_yaml(file_path, issues_data)
        return str(file_path)
    
    def load_issues(self, task_id: str) -> Dict[str, Any]:
        """
        課題ファイルを読み込む
        
        Args:
            task_id: タスクID
            
        Returns:
            読み込んだ課題データ
        """
        file_path = self.issues_dir / f"{task_id}.yaml"
        return self._load_yaml(file_path)
    
    def list_plans(self) -> List[str]:
        """
        全プランIDのリストを取得する
        
        Returns:
            プランIDのリスト
        """
        return [f.stem for f in self.plans_dir.glob("*.yaml")]
    
    def list_requirements(self) -> List[str]:
        """
        全タスクIDのリストを取得する
        
        Returns:
            タスクIDのリスト
        """
        return [f.stem for f in self.requirements_dir.glob("*.yaml")]
    
    def list_plan_versions(self, plan_id: str) -> List[Tuple[int, str]]:
        """
        プランの全バージョンのリストを取得する
        
        Args:
            plan_id: プランID
            
        Returns:
            (バージョン番号, ファイルパス) のタプルのリスト
        """
        plan_history_dir = self.history_dir / plan_id
        if not plan_history_dir.exists():
            return []
        
        versions = []
        # 現在のバージョンを追加
        try:
            current_plan = self.load_plan(plan_id)
            current_version = current_plan.get("version", 1)
            versions.append((current_version, str(self.plans_dir / f"{plan_id}.yaml")))
        except FileNotFoundError:
            pass
        
        # 履歴バージョンを追加
        for f in plan_history_dir.glob("v*_*.yaml"):
            try:
                # ファイル名から "v{バージョン番号}_{タイムスタンプ}.yaml" の形式を解析
                version_str = f.stem.split("_")[0]
                version = int(version_str[1:])  # "v" を削除してint型に変換
                versions.append((version, str(f)))
            except (ValueError, IndexError):
                continue
        
        # バージョン番号で降順ソート
        versions.sort(reverse=True)
        return versions
    
    def delete_plan(self, plan_id: str) -> bool:
        """
        プランを削除する（履歴も含む）
        
        Args:
            plan_id: プランID
            
        Returns:
            削除に成功したかどうか
        """
        try:
            # プランファイルを削除
            plan_path = self.plans_dir / f"{plan_id}.yaml"
            if plan_path.exists():
                plan_path.unlink()
            
            # 履歴ディレクトリを削除
            history_dir = self.history_dir / plan_id
            if history_dir.exists():
                shutil.rmtree(history_dir)
            
            return True
        except Exception as e:
            print(f"プランの削除に失敗しました: {e}")
            return False


# smolagentsのツールとして提供するための関数
def save_yaml_file(file_path: str, data: Dict[str, Any]) -> str:
    """
    YAMLファイルを保存するユーティリティ関数
    
    Args:
        file_path: 保存先のファイルパス
        data: 保存するデータ
        
    Returns:
        保存したファイルのパス
    """
    path_obj = Path(file_path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path_obj, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    return file_path

def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """
    YAMLファイルを読み込むユーティリティ関数
    
    Args:
        file_path: 読み込むファイルパス
        
    Returns:
        読み込んだデータ
        
    Raises:
        FileNotFoundError: ファイルが存在しない場合
        yaml.YAMLError: YAMLの解析に失敗した場合
    """
    path_obj = Path(file_path)
    
    if not path_obj.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
    
    with open(path_obj, 'r', encoding='utf-8') as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"YAMLの解析に失敗しました: {e}")
