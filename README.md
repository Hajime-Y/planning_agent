# Planning Agent システム

マルチエージェントシステムにおけるプランニング機能を効率化・最適化するエージェントベースのシステム

## 概要

Planning Agentシステムは、複数のエージェントが協調して動作するマルチエージェントシステムに対して、効率的かつ柔軟なプランニング機能を提供するシステムです。本システムは、エージェントシステムの性能における「プランニングの正確さとその管理能力」の重要性を検証することを目的としています。

## 主要機能

- **タスク分析機能**: ユーザーから受け取ったタスクを分析し、要件を明確化
- **プラン生成・分解機能**: タスクを実行可能なサブタスクに分解し、依存関係を特定
- **プラン管理機能**: プランの実行状況追跡と動的な調整
- **エージェント調整機能**: サブタスクに適したエージェントの選定と協調作業の最適化
- **ファイル管理機能**: YAML形式でのデータ保存・読み込み・履歴管理

## システム構成

本システムは以下のエージェントから構成されています：

1. **プランニングマネージャエージェント**: 全体のプランニングプロセスを統括
2. **要件分析エージェント**: ユーザー入力の分析と要件の明確化
3. **タスク分解エージェント**: タスクの分解と実行可能性評価
4. **課題管理エージェント**: プロジェクトの課題追跡と対応方針提示

## 技術スタック

- **言語**: Python 3.10以上
- **フレームワーク**: smolagentsフレームワーク
- **インターフェース**: 
  - CLIでの操作
  - MCP (Model Context Protocol) 対応
  - Claude 3.7 Sonnetとの連携

## プロジェクト構造

```
planning_agent/
├── config/
│   ├── agent_config.yaml      # エージェント設定
│   └── mcp_config.yaml        # MCP設定
├── agents/
│   ├── __init__.py
│   ├── planning_manager.py    # プランニングマネージャエージェント
│   ├── requirement_analyzer.py # 要件分析エージェント
│   ├── task_decomposer.py     # タスク分解エージェント
│   └── issue_manager.py       # 課題管理エージェント
├── mcp_interface/           # MCPサーバー関連
│   ├── __init__.py
│   └── server.py            # MCPサーバー実装 (FastMCP使用)
├── utils/
│   ├── __init__.py
│   ├── file_manager.py        # ファイル入出力機能
│   ├── tools.py               # smolagentsツール集
│   └── prompt_templates.py    # プロンプトテンプレート
├── cli.py                     # CLIインターフェース
└── main.py                    # メインエントリーポイント
```

## MCP機能

- **CreatePlan**: 新規プラン作成機能（既存プランのアーカイブ含む）
- **UpdatePlan**: プラン更新機能
- **ReportIssue**: 課題報告・対応方針提示機能

## インストール方法

```bash
# リポジトリのクローン
git clone https://github.com/Hajime-Y/planning_agent.git
cd planning_agent

# 環境のセットアップと依存パッケージのインストール
uv venv
source .venv/bin/activate
uv sync
```

## ファイル管理ユーティリティ

本システムでは、以下のYAML形式ファイル操作機能を提供しています：

- **要件ファイル管理**: タスク要件の保存と読み込み
- **プランファイル管理**: プランデータの保存、バージョン管理、履歴管理
- **課題ファイル管理**: 課題データの保存と追跡

これらの機能は、`utils/file_manager.py`で実装されており、smolagentsのツールとして`utils/tools.py`から利用可能です。

## 使用方法

### コマンドラインインターフェース (CLI)

`cli.py` を使用して、MCPツール関数の直接呼び出しや、Planning Agentとの対話が可能です。

**1. MCPツール関数の呼び出し**

`mcp call` サブコマンドを使用します。引数はJSON形式の文字列で渡します。

```bash
# 例: create_plan を呼び出す
uv run python cli.py mcp call create_plan '{"task_description": "新しい機能Xを実装する"}'

# 例: update_plan を呼び出す
uv run python cli.py mcp call update_plan '{"task_number": 1, "artifacts": ["path/to/output.py"], "comments": "タスク1完了"}'

# 例: report_issue を呼び出す
uv run python cli.py mcp call report_issue '{"task_number": 2, "issue_description": "テスト中にエラー発生"}'
```

**2. Planning Agentとの対話**

`chat` サブコマンドを使用します。

```bash
uv run python cli.py chat
```

実行すると、`Initializing Planning Agent...` と表示された後、プロンプト (`>`) が表示されます。
エージェントに指示や質問を入力し、Enterキーを押してください。
対話を終了するには `quit` または `exit` と入力します。

### MCP クライアントとしての実行 (`main.py`)

`main.py` は、OpenAI Agent SDK を使用して MCP クライアントとして動作する **汎用タスク実行エージェント (`GenericTaskAgent`)** を起動します。このエージェントの主な役割はユーザーからの指示に基づいてタスクを実行することですが、**複雑なタスクの計画立案と管理は MCP サーバー (`PlanningAgentServer`) に委任します。**

エージェントは、サブプロセスとして起動した MCP サーバー (`mcp_interface/server.py`) と標準入出力を介して通信し、利用可能なツール (`create_plan`, `update_plan` など) を使用します。

**実行方法:**

```bash
# リポジトリのルートディレクトリで実行
uv run python main.py
```

実行すると、MCP サーバーへの接続と Agent の初期化が行われ、`Please enter the initial task or request:` というプロンプトが表示されます。ここに最初のタスク指示を入力してください。
**Agent はまず、その指示に基づいて計画を立てるために、MCP サーバーの `create_plan` ツールを呼び出します。** その後、得られた計画や指示に従ってタスクを実行し、必要に応じて `update_plan` や `report_issue` ツールを使って進捗や問題を MCP サーバーに報告します。

**注意点:**

- このスクリプトは、`mcp_interface/server.py` をサブプロセスとして起動します。Python の実行パスが正しく設定されている必要があります。
- 現在、グレースフルシャットダウン機能は実装されていません。終了するには Ctrl+C を使用してください。
- OpenAI Agent SDK が内部で OpenAI API キーを使用する可能性があるため、環境変数 `OPENAI_API_KEY` の設定が必要になる場合があります（モデル設定によります）。

## 開発ロードマップ

1. **シングルエージェント基本機能とMCP基盤**
   - 要件定義機能
   - タスク分解機能
   - YAMLファイル出力機能

2. **プラン更新機能**
   - タスク完了フラグの更新
   - プラン変更機能
   - プラン履歴管理機能

3. **課題管理機能**
   - 課題管理機能
   - 課題ファイル出力機能
   - プラン更新提案機能

4. **マルチエージェント化**
   - 要件分析エージェントの追加
   - タスク分解エージェントの追加
   - 課題管理エージェントの追加

## 評価方法

- Sudoku-Benchを使用した定量評価
- エージェント間協調の効率性評価
- プランニング精度の評価
- タスク実行効率の比較評価

## ライセンス

（ライセンス情報を追記予定）

## 注記

本システムは概念実証（PoC）段階のプロジェクトであり、個人の開発環境での動作を前提としています。パフォーマンスやスケーラビリティは検証対象外です。

## 関連ドキュメント

- [PRD（Product Requirements Document）](docs/rpd.md)
- [設計ドキュメント](docs/design_doc.md) 