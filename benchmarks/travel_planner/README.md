# TravelPlanner Sole-Planning ベンチマーク

このディレクトリには、[TravelPlanner](https://github.com/OSU-NLP-Group/TravelPlanner)ベンチマークのSole-Planning設定を実行するためのスクリプトが含まれています。

## 概要

`sole_planning.py`スクリプトは、TravelPlannerデータセットの問題に対する旅行計画を生成します。このスクリプトは元のTravelPlannerのコードを修正したもので、`front_agents.generic_task_agent.run_agent_session`関数を使用して計画を生成します。

## 前提条件

- Python 3.9以上
- 以下のPythonパッケージ（`requirements.txt`に含まれています）：
  - huggingface_hub
  - datasets
  - tqdm
  - langchain
  - ...（その他の依存関係）
- 環境変数：
  - OpenAI APIキー（`OPENAI_API_KEY`）または他の使用するモデルに応じたAPIキー

## 実行方法

基本的な実行コマンド：

```bash
python benchmarks/travel_planner/sole_planning.py \
    --model_name gpt-4.1 \
    --set_type validation \
    --output_dir benchmarks/travel_planner/results
```

### コマンドライン引数

- `--model_name`: 使用するモデル名（例：`gpt-4.1`、`gpt-4-turbo`など）。デフォルトは `gpt-4.1`。
- `--set_type`: 使用するデータセットの種類（`validation`または`test`）。デフォルトは `validation`。
- `--output_dir`: 結果を保存するディレクトリ。デフォルトは実行ディレクトリ (`./`)。
- `--use_planning_server`: 計画サーバーを使用するかどうか（フラグ）。
- `--limit`: 処理するサンプル数の制限（オプション）。

詳細なコマンド例については[example_commands.sh](./example_commands.sh)を参照してください。

## 出力形式

結果は以下の形式でJSONファイルとして保存されます：
```
{output_dir}/{set_type}/generated_plan_{number}.json
```

各JSONファイルには、入力問題、生成された計画、およびメタデータが含まれます。

## 評価

`example_commands.sh`に記載の評価コマンドを使用して、生成された計画の評価を行うことができます。評価時は`model_name`パラメータが生成されたJSONファイル内のキー名と一致するよう注意してください。例えば、`gpt-4.1`モデルを使用した場合は`"gpt-4.1_direct_sole-planning"`となります。 