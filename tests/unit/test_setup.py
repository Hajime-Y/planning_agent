import os
import sys
import pytest
from pathlib import Path

def test_python_version():
    """Pythonバージョンが3.9以上であることを確認"""
    version = sys.version_info
    assert version.major == 3 and version.minor >= 9, "Python 3.9以上が必要です"

def test_project_structure():
    """プロジェクトの基本構造が正しいことを確認"""
    root = Path(__file__).parent.parent.parent
    required_dirs = ["src", "tests", "tests/unit", "tests/integration"]
    required_files = ["pyproject.toml", ".gitignore"]
    
    for dir_path in required_dirs:
        assert (root / dir_path).is_dir(), f"{dir_path}ディレクトリが存在しません"
    
    for file_path in required_files:
        assert (root / file_path).is_file(), f"{file_path}ファイルが存在しません"

def test_pyproject_toml_content():
    """pyproject.tomlの基本設定を確認"""
    root = Path(__file__).parent.parent.parent
    pyproject_path = root / "pyproject.toml"
    
    with open(pyproject_path, "r") as f:
        content = f.read()
    
    required_sections = [
        "[project]",
        "requires-python",
        "dependencies",
        "[build-system]",
        "[tool.pytest.ini_options]"
    ]
    
    for section in required_sections:
        assert section in content, f"{section}セクションが見つかりません"

def test_gitignore_content():
    """基本的な.gitignore設定を確認"""
    root = Path(__file__).parent.parent.parent
    gitignore_path = root / ".gitignore"
    
    with open(gitignore_path, "r") as f:
        content = f.read()
    
    required_ignores = [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".Python",
        "env/",
        "venv/",
        ".env",
        ".venv",
        "dist/",
        "build/",
        "*.egg-info/",
    ]
    
    for ignore in required_ignores:
        assert ignore in content, f"{ignore}が.gitignoreに含まれていません" 