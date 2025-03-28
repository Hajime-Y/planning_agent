import os
import subprocess
import pytest
from pathlib import Path

def test_uv_installation():
    """uvコマンドが利用可能であることを確認"""
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, "uvコマンドが見つかりません"
    except FileNotFoundError:
        pytest.fail("uvがインストールされていません")

def test_dependency_installation():
    """依存関係のインストールをテスト"""
    root = Path(__file__).parent.parent.parent
    
    # 一時的な仮想環境を作成してテスト
    try:
        result = subprocess.run(
            ["python", "-m", "venv", ".test_venv"],
            cwd=root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "仮想環境の作成に失敗しました"

        # 依存関係のインストール
        venv_python = str(root / ".test_venv" / "bin" / "python")
        result = subprocess.run(
            [venv_python, "-m", "pip", "install", "-e", "."],
            cwd=root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "依存関係のインストールに失敗しました"

    finally:
        # テスト用の仮想環境を削除
        subprocess.run(["rm", "-rf", ".test_venv"], cwd=root)

def test_project_importable():
    """プロジェクトがPythonパッケージとしてインポート可能であることを確認"""
    root = Path(__file__).parent.parent.parent
    src_init = root / "src" / "__init__.py"
    
    # srcディレクトリが存在しない場合は作成
    if not src_init.parent.exists():
        src_init.parent.mkdir(parents=True)
    
    # __init__.pyが存在しない場合は作成
    if not src_init.exists():
        src_init.touch()
    
    try:
        import src
        assert True, "プロジェクトのインポートに成功"
    except ImportError:
        pytest.fail("プロジェクトをインポートできません") 