# Planning Agent

AIを活用したプロジェクト計画支援システム

## 概要

このシステムは、プロジェクトの計画立案を支援するAIエージェントシステムです。以下の機能を提供します：

- 要件の分析と具体化
- タスクの自動分解
- 依存関係の分析
- クリティカルパスの特定
- プロジェクト計画の最適化

## 機能

- 要件分析エージェント
- タスク分解エージェント
- 依存関係分析エージェント
- 計画マネージャエージェント
- コマンドラインインターフェース
- Webインターフェース（Gradio）

## 技術スタック

- Python 3.9+
- Gradio（Webインターフェース）
- YAML（データ構造）

## セットアップ

```bash
# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt
```

## 使用方法

### コマンドライン

```bash
python main.py --input requirements.yaml
```

### Webインターフェース

```bash
python web_app.py
```

## ライセンス

MIT License

## 貢献

プルリクエストやイシューの作成は大歓迎です。