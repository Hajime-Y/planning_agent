#!/usr/bin/env python3
import os
import sys
import subprocess
import venv
from pathlib import Path

def check_python_version():
    """Pythonバージョンが3.9以上であることを確認"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        raise RuntimeError("Python 3.9以上が必要です")

def setup_virtual_environment(root_dir: Path):
    """仮想環境をセットアップ"""
    venv_dir = root_dir / ".venv"
    if not venv_dir.exists():
        print("仮想環境を作成中...")
        venv.create(venv_dir, with_pip=True)
    return venv_dir

def install_uv(venv_dir: Path):
    """uvをインストール"""
    pip_path = venv_dir / "bin" / "pip"
    try:
        subprocess.run(
            [str(pip_path), "install", "uv"],
            check=True,
            capture_output=True,
            text=True
        )
        print("uvのインストールが完了しました")
    except subprocess.CalledProcessError as e:
        print(f"uvのインストールに失敗しました: {e.stderr}")
        raise

def install_dependencies(venv_dir: Path, root_dir: Path):
    """プロジェクトの依存関係をインストール"""
    python_path = venv_dir / "bin" / "python"
    try:
        subprocess.run(
            [str(python_path), "-m", "pip", "install", "-e", "."],
            cwd=root_dir,
            check=True,
            capture_output=True,
            text=True
        )
        print("依存関係のインストールが完了しました")
    except subprocess.CalledProcessError as e:
        print(f"依存関係のインストールに失敗しました: {e.stderr}")
        raise

def main():
    """メインの実行関数"""
    try:
        # プロジェクトルートディレクトリを取得
        root_dir = Path(__file__).parent.parent.absolute()
        
        # Pythonバージョンチェック
        check_python_version()
        
        # 仮想環境のセットアップ
        venv_dir = setup_virtual_environment(root_dir)
        
        # uvのインストール
        install_uv(venv_dir)
        
        # 依存関係のインストール
        install_dependencies(venv_dir, root_dir)
        
        print("環境セットアップが完了しました")
        return 0
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 