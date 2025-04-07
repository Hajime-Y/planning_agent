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
from typing import Dict, List, Any, Optional, Union, Tuple, TypedDict


# Type definitions for data structures based on design doc
class RequirementsData(TypedDict):
    task_id: str
    created_at: str
    updated_at: str
    title: str
    description: str
    constraints: List[str]
    resources: List[str]

class Subtask(TypedDict):
    id: str
    description: str
    status: str
    order: int
    inputs: List[str]
    outputs: List[str]

class PlanData(TypedDict):
    plan_id: str
    task_id: str
    created_at: str
    updated_at: str
    version: int
    status: str
    subtasks: List[Subtask]

class Issue(TypedDict):
    issue_id: str
    created_at: str
    status: str
    description: str
    impact: str
    solution: str
    remarks: Optional[str]
    related_subtasks: List[str]

class IssueFileData(TypedDict):
    task_id: str
    updated_at: str
    issues: List[Issue]


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
        # TypedDict を通常の dict に変換してから保存
        serializable_data = dict(data)
        if 'subtasks' in serializable_data:
            serializable_data['subtasks'] = [dict(s) for s in serializable_data['subtasks']]
        if 'issues' in serializable_data:
             serializable_data['issues'] = [dict(i) for i in serializable_data['issues']]

        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(serializable_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
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
                # YAMLファイルが空の場合も考慮
                loaded_data = yaml.safe_load(f)
                return loaded_data if loaded_data is not None else {}
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"YAMLの解析に失敗しました: {e}")
    
    def save_requirements(
        self,
        task_id: str,
        title: str,
        description: str,
        constraints: List[str],
        resources: List[str],
        created_at: Optional[str] = None, # 新規作成時に設定する場合
    ) -> str:
        """
        要件ファイルを保存または更新する
        
        Args:
            task_id: タスクID
            title: タスクのタイトル
            description: タスクの説明
            constraints: 制約条件のリスト
            resources: 利用可能なリソースのリスト
            created_at: 作成日時 (指定しない場合、既存ファイルがあればその値を維持、なければ現在時刻)
            
        Returns:
            保存したファイルのパス
        """
        now = datetime.now().isoformat()
        file_path = self.requirements_dir / f"{task_id}.yaml"
        final_created_at = created_at # 指定されたcreated_atを優先

        if not final_created_at:
             try:
                 existing_data = self.load_requirements(task_id)
                 final_created_at = existing_data.get("created_at", now)
             except FileNotFoundError:
                 final_created_at = now # 既存ファイルがなければ現在時刻

        requirements_data: RequirementsData = {
            "task_id": task_id,
            "title": title,
            "description": description,
            "constraints": constraints,
            "resources": resources,
            "created_at": final_created_at,
            "updated_at": now, # 常に現在時刻で更新
        }

        self._save_yaml(file_path, requirements_data)
        return str(file_path)
    
    def load_requirements(self, task_id: str) -> RequirementsData:
        """
        要件ファイルを読み込む
        
        Args:
            task_id: タスクID
            
        Returns:
            読み込んだ要件データ
        """
        file_path = self.requirements_dir / f"{task_id}.yaml"
        # 型安全のため、ロードしたデータをキャストする（必要に応じて検証を追加）
        return self._load_yaml(file_path) # type: ignore
    
    def save_plan(
        self,
        plan_id: str,
        task_id: str,
        status: str,
        subtasks: List[Subtask],
    ) -> Tuple[str, int]:
        """
        プランファイルを保存または更新する。バージョン管理とバックアップを自動で行う。
        
        Args:
            plan_id: プランID
            task_id: 関連するタスクID
            status: プランのステータス
            subtasks: サブタスクのリスト
            
        Returns:
            保存したファイルのパスと新しいバージョン番号のタプル
        """
        now = datetime.now().isoformat()
        file_path = self.plans_dir / f"{plan_id}.yaml"
        version = 1
        created_at = now

        try:
            existing_plan = self.load_plan(plan_id)
            current_version = existing_plan.get("version", 0)
            created_at = existing_plan.get("created_at", now)
            # バックアップ実行
            self.backup_plan(plan_id, current_version)
            version = current_version + 1
        except FileNotFoundError:
            # 新規プランの場合は何もしない
            pass

        plan_data: PlanData = {
            "plan_id": plan_id,
            "task_id": task_id,
            "created_at": created_at,
            "updated_at": now,
            "version": version,
            "status": status,
            "subtasks": subtasks,
        }

        self._save_yaml(file_path, plan_data)
        return str(file_path), version
    
    def load_plan(self, plan_id: str) -> PlanData:
        """
        プランファイルを読み込む
        
        Args:
            plan_id: プランID
            
        Returns:
            読み込んだプランデータ
        """
        file_path = self.plans_dir / f"{plan_id}.yaml"
        # 型安全のため、ロードしたデータをキャストする（必要に応じて検証を追加）
        return self._load_yaml(file_path) # type: ignore
    
    def backup_plan(self, plan_id: str, version: int) -> Optional[str]:
        """
        プランの指定されたバージョンを履歴としてバックアップする
        
        Args:
            plan_id: プランID
            version: バックアップするプランのバージョン番号
            
        Returns:
            バックアップファイルのパス、またはNone（失敗時）
        """
        try:
            source_path = self.plans_dir / f"{plan_id}.yaml"
            if not source_path.exists():
                # バックアップはベストエフォート。ソースがなくてもエラーにはしない。
                # print(f"バックアップ対象のプランファイルが見つかりません: {source_path}")
                return None

            # 履歴ディレクトリ
            plan_history_dir = self.history_dir / plan_id
            plan_history_dir.mkdir(parents=True, exist_ok=True)

            # バックアップファイルパス
            timestamp = self._get_timestamp()
            # バックアップファイル名にバージョンを含める
            backup_path = plan_history_dir / f"v{version}_{timestamp}.yaml"

            # バックアップを作成
            shutil.copy2(source_path, backup_path)
            # print(f"プランをバックアップしました: {backup_path}")
            return str(backup_path)
        except Exception as e:
            print(f"プランのバックアップに失敗しました: {e}")
            return None
    
    def save_issue(
        self,
        task_id: str,
        issue_id: Optional[str], # Noneの場合は新規作成
        status: str,
        description: str,
        impact: str,
        solution: str,
        remarks: Optional[str],
        related_subtasks: List[str],
    ) -> Tuple[str, str]:
        """
        個別の課題を課題ファイルに追加または更新する
        
        Args:
            task_id: 関連するタスクID
            issue_id: 課題ID (Noneの場合は新規発行)
            status: 課題のステータス
            description: 課題の説明
            impact: 課題の影響
            solution: 解決策
            remarks: 備考
            related_subtasks: 関連するサブタスクIDのリスト
            
        Returns:
            (保存したファイルのパス, 割り当てられた/更新された課題ID) のタプル
        """
        now = datetime.now().isoformat()
        file_path = self.issues_dir / f"{task_id}.yaml"
        issues_data: IssueFileData

        try:
            # 既存の課題ファイルを読み込む
            loaded_data = self._load_yaml(file_path)
            # 簡単なバリデーション
            if isinstance(loaded_data, dict) and "task_id" in loaded_data and "issues" in loaded_data:
                 issues_data = loaded_data # type: ignore
            else:
                 print(f"警告: 課題ファイル {file_path} の形式が不正または空です。新規作成します。")
                 issues_data = {"task_id": task_id, "updated_at": now, "issues": []}
        except FileNotFoundError:
            # ファイルが存在しない場合は新規作成
            issues_data = {"task_id": task_id, "updated_at": now, "issues": []}

        issues = issues_data.get("issues", [])
        target_issue_id = issue_id
        created_at = now # デフォルトは現在時刻

        # 課題リストを更新
        updated = False
        if target_issue_id:
             # 更新の場合：既存の課題を探す
             for i, existing_issue in enumerate(issues):
                 if existing_issue.get("issue_id") == target_issue_id:
                     created_at = existing_issue.get("created_at", now) # 既存のcreated_atを維持
                     new_issue: Issue = {
                         "issue_id": target_issue_id,
                         "created_at": created_at,
                         "status": status,
                         "description": description,
                         "impact": impact,
                         "solution": solution,
                         "remarks": remarks,
                         "related_subtasks": related_subtasks,
                     }
                     issues[i] = new_issue
                     updated = True
                     break
             if not updated:
                  print(f"警告: 更新対象の課題IDが見つかりません: {target_issue_id}")
                  # 見つからなかった場合、新規として追加することも検討できるが、
                  # ここではエラー扱いとせず、次の新規追加ロジックにも進まない
                  pass

        if not updated and issue_id is None: # 新規追加の場合 (issue_idがNone)
             # 新規課題IDを生成
             issue_count = len(issues)
             target_issue_id = f"issue-{task_id}-{issue_count + 1:03d}"
             created_at = now

             new_issue: Issue = {
                 "issue_id": target_issue_id,
                 "created_at": created_at,
                 "status": status,
                 "description": description,
                 "impact": impact,
                 "solution": solution,
                 "remarks": remarks,
                 "related_subtasks": related_subtasks,
             }
             issues.append(new_issue)
             updated = True # 追加されたことを示す

        # issues_data を更新 (課題リストと最終更新日時)
        if updated:
             issues_data["issues"] = issues
             issues_data["updated_at"] = now # ファイル全体の更新日時
             # ファイルに保存
             self._save_yaml(file_path, issues_data)
             return str(file_path), target_issue_id if target_issue_id else "Error"
        else:
             # 更新も追加もされなかった場合（例：更新対象IDが見つからない）
             print(f"課題の保存/更新が行われませんでした (task_id: {task_id}, issue_id: {issue_id})")
             # エラーを示すために空のパスとIDを返すか、例外を発生させる
             return "", "NotSaved"

    def load_issues(self, task_id: str) -> IssueFileData:
        """
        課題ファイルを読み込む
        
        Args:
            task_id: タスクID
            
        Returns:
            読み込んだ課題データ
        """
        file_path = self.issues_dir / f"{task_id}.yaml"
        try:
             loaded_data = self._load_yaml(file_path)
             # 簡単なバリデーション
             if isinstance(loaded_data, dict) and "task_id" in loaded_data and "issues" in loaded_data:
                 return loaded_data # type: ignore
             else:
                 # 不正な形式の場合は空のデータを返す
                 print(f"警告: 課題ファイル {file_path} の形式が不正です。空のデータを返します。")
                 return {"task_id": task_id, "updated_at": "", "issues": []} # type: ignore
        except FileNotFoundError:
             # ファイルが存在しない場合は空のデータを返す
             return {"task_id": task_id, "updated_at": "", "issues": []} # type: ignore
    
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
