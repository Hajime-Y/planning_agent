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
uv run python benchmarks/travel_planner/sole_planning.py \
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

### 評価の実行

### 評価プロセスの概要

TravelPlannerベンチマークの評価は、生成されたプランが様々な制約条件を満たしているかを検証します。評価プロセスは以下のステップで構成されています：

1. **プランの解析（Parsing）**: 生成されたプランをJSON形式に変換します
2. **要素の抽出（Element Extraction）**: JSONから評価に必要な要素を抽出します
3. **評価用ファイルの生成（Combination）**: 抽出した要素から評価用のファイルを作成します
4. **評価の実行（Evaluation）**: 各制約条件に対する評価を実行します

### 前提条件

評価を実行する前に、以下を確認してください：

- `sole_planning.py`スクリプトを実行済みで、結果ファイルが生成されていること
- 生成されたプランが適切なフォーマットであること（日程ごとのアクティビティが含まれていること）

### 評価コマンド

各ステップを順番に実行する必要があります：

#### 1. プランの解析（Parsing）

```bash
uv run python benchmarks/travel_planner/TravelPlanner/postprocess/parsing.py \
    --set_type validation \
    --output_dir benchmarks/travel_planner/results \
    --model_name gpt-4.1 \
    --strategy direct \
    --mode sole-planning \
    --tmp_dir benchmarks/travel_planner/tmp
```

#### 2. 要素の抽出（Element Extraction）

```bash
uv run python benchmarks/travel_planner/TravelPlanner/postprocess/element_extraction.py \
    --set_type validation \
    --output_dir benchmarks/travel_planner/results \
    --model_name gpt-4.1 \
    --strategy direct \
    --mode sole-planning \
    --tmp_dir benchmarks/travel_planner/tmp
```

#### 3. 評価用ファイルの生成（Combination）

```bash
uv run python benchmarks/travel_planner/TravelPlanner/postprocess/combination.py \
    --set_type validation \
    --output_dir benchmarks/travel_planner/results \
    --model_name gpt-4.1 \
    --strategy direct \
    --mode sole-planning \
    --submission_file_dir benchmarks/travel_planner/submission
```

#### 4. 最終評価の実行（Evaluation）

```bash
cd benchmarks/travel_planner/TravelPlanner/evaluation
uv run python eval.py \
    --set_type validation \
    --evaluation_file_path ../../submission/validation_gpt-4.1_direct_sole-planning_submission.jsonl
```

**注意:** `test` データセットの評価は、リーダーボードシステム側で行われます。`eval.py` は `validation` データセットの評価にのみ使用してください。生成された `test` データセットの提出ファイル (`submission` ディレクトリ内の `.jsonl` ファイル) をリーダーボードに提出することで評価が行われます。

### 評価メトリクス

`eval.py`スクリプトは以下のメトリクスを計算します：

1. **デリバリーレート（Delivery Rate）**: 正常に解析・評価できたプランの割合
2. **常識的制約メトリクス（Commonsense Constraint Metrics）**:
   - マイクロパスレート: 各制約を満たした個別のアクティビティの割合
   - マクロパスレート: すべての常識的制約を満たしたプランの割合
3. **ハード制約メトリクス（Hard Constraint Metrics）**:
   - マイクロパスレート: 各制約を満たした個別のアクティビティの割合
   - マクロパスレート: すべてのハード制約を満たしたプランの割合
4. **最終パスレート（Final Pass Rate）**: すべての制約（常識的+ハード）を満たしたプランの割合

#### 評価される制約

**常識的制約（Commonsense Constraints）**:
- 現在の都市内（Within Current City）
- 予算内（Budget）
- 有効な交通手段（Transportation）
- 営業時間内（Opening Hours）
- 滞在時間（Duration）
- 食事の時間帯（Meal Time）

**ハード制約（Hard Constraints）**:
- 旅行日数（Travel Days）
- 宿泊（Accommodation）
- 特定の場所への訪問（Visit Specific Place）
- 特定のアクティビティタイプ（Specific Activity Type）
- 予算範囲（Budget Range）
- 食事の回数（Number of Meals）

### 簡易評価方法

より簡単な評価方法として、`example_commands.sh`に含まれる以下のコマンドも使用できます（`validation` データセットの場合）：

```bash
python external/TravelPlanner/postprocess/evaluate.py \
    --result_dir results/travel_planner \
    --model_name "gpt-4-turbo_direct_sole-planning" \
    --set_type validation
```

このコマンドは、`validation` データセットに対する評価に必要なすべてのステップを自動的に実行します。ただし、`external/TravelPlanner`リポジトリが必要です。

### 注意事項

- 生成されるJSONファイル内のパラメータ名は評価時の期待値と一致する必要があります
- 評価結果は指定した`output_dir`ディレクトリ内に保存されます
- 詳細なログは各評価スクリプトの実行時に出力されます 