import os
import sys
import pytest
from pathlib import Path

def test_python_version():
    """Pythonバージョンが3.9以上であることを確認"""
    version = sys.version_info
    assert version.major == 3 and version.minor >= 9, "Python 3.9以上が必要です"

def test_project_structure():
    """プロジェクトの基本構造を確認"""
    root = Path.cwd()
    
    # 必要なディレクトリの存在確認
    required_dirs = [
        "src",
        "tests",
        "docs",
    ]
    
    for dir_name in required_dirs:
        assert (root / dir_name).exists(), f"{dir_name}ディレクトリが存在しません"

def test_config_files():
    """設定ファイルの存在と基本内容を確認"""
    root = Path.cwd()
    
    # 必要なファイルの存在確認
    required_files = [
        "pyproject.toml",
        ".gitignore",
        "README.md",
    ]
    
    for file_name in required_files:
        assert (root / file_name).exists(), f"{file_name}が存在しません"

def test_gitignore_content():
    """gitignoreの基本設定を確認"""
    with open(".gitignore", "r") as f:
        content = f.read()
    
    required_ignores = [
        "__pycache__",
        "*.pyc",
        ".env",
        ".venv",
        "dist",
        "build",
    ]
    
    for ignore in required_ignores:
        assert ignore in content, f"{ignore}が.gitignoreに含まれていません"

def test_pyproject_toml():
    """pyproject.tomlの基本設定を確認"""
    import tomli
    
    with open("pyproject.toml", "rb") as f:
        config = tomli.load(f)
    
    # 基本設定の確認
    assert "project" in config, "project設定が見つかりません"
    assert "dependencies" in config.get("project", {}), "依存関係が定義されていません"
    
    # 必要な依存関係の確認
    dependencies = config["project"]["dependencies"]
    required_packages = [
        "uv",
    ]
    
    for package in required_packages:
        assert any(package in dep for dep in dependencies), f"{package}が依存関係に含まれていません"

def test_uv_installation():
    """uvのインストールと設定を確認"""
    import subprocess
    
    # uvコマンドが利用可能か確認
    result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
    assert result.returncode == 0, "uvがインストールされていません" 