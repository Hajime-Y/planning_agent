#!/usr/bin/env python3
import os
import sys
import subprocess
import venv
import platform
from pathlib import Path

def check_python_version():
    """Pythonバージョンが3.9以上であることを確認"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        raise RuntimeError("Python 3.9以上が必要です")

def get_bin_dir_name():
    """プラットフォームに応じたbinディレクトリ名を返す"""
    return "Scripts" if platform.system() == "Windows" else "bin"

def setup_virtual_environment(root_dir: Path):
    """仮想環境をセットアップ"""
    venv_dir = root_dir / ".venv"
    if not venv_dir.exists():
        print("仮想環境を作成中...")
        # 新規作成時のみPythonバージョンをチェック
        check_python_version()
        venv.create(venv_dir, with_pip=True)
    return venv_dir

def install_uv(venv_dir: Path):
    """uvをインストール"""
    bin_dir = get_bin_dir_name()
    pip_path = venv_dir / bin_dir / "pip"
    try:
        subprocess.run(
            [str(pip_path), "install", "uv"],
            check=True,
            text=True
        )
        print("uvのインストールが完了しました")
    except subprocess.CalledProcessError as e:
        print(f"uvのインストールに失敗しました")
        raise

def install_dependencies(venv_dir: Path, root_dir: Path):
    """プロジェクトの依存関係をインストール"""
    bin_dir = get_bin_dir_name()
    python_path = venv_dir / bin_dir / "python"
    uv_path = venv_dir / bin_dir / ("uv.exe" if platform.system() == "Windows" else "uv")
    
    # uvが存在するか確認
    if uv_path.exists():
        try:
            # uvを使用して依存関係をインストール
            subprocess.run(
                [str(uv_path), "sync"],
                cwd=root_dir,
                check=True,
                text=True
            )
            print("uvを使用して依存関係のインストールが完了しました")
            return
        except subprocess.CalledProcessError:
            print("uvでの依存関係インストールに失敗しました。pipを使用します")
    
    # uvが使えない場合はpipを使用
    try:
        subprocess.run(
            [str(python_path), "-m", "pip", "install", "-e", "."],
            cwd=root_dir,
            check=True,
            text=True
        )
        print("依存関係のインストールが完了しました")
    except subprocess.CalledProcessError:
        print(f"依存関係のインストールに失敗しました")
        raise

def print_activation_instructions(venv_dir: Path):
    """仮想環境のアクティベーション方法を表示"""
    bin_dir = get_bin_dir_name()
    is_windows = platform.system() == "Windows"
    
    print("\n仮想環境をアクティベートする方法:")
    if is_windows:
        print(f"  コマンドプロンプト: {venv_dir}\\{bin_dir}\\activate.bat")
        print(f"  PowerShell: {venv_dir}\\{bin_dir}\\Activate.ps1")
    else:
        print(f"  source {venv_dir}/{bin_dir}/activate")
    print("")

def main():
    """メインの実行関数"""
    try:
        # プロジェクトルートディレクトリを取得
        root_dir = Path(__file__).parent.parent.absolute()
        
        # 仮想環境のセットアップ
        venv_dir = setup_virtual_environment(root_dir)
        
        # uvのインストール
        install_uv(venv_dir)
        
        # 依存関係のインストール
        install_dependencies(venv_dir, root_dir)
        
        # アクティベーション手順の表示
        print_activation_instructions(venv_dir)
        
        print("環境セットアップが完了しました")
        return 0
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 