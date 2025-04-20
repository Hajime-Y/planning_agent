import os
import re
import sys

# カレントディレクトリの変更は不要
# sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../..")))
# os.chdir(os.path.dirname(os.path.abspath(__file__)))
# スクリプトのディレクトリを取得
script_dir = os.path.dirname(os.path.abspath(__file__))
# プロジェクトルートを計算 (benchmarks/travel_planner の2つ上のディレクトリ)
project_root = os.path.abspath(os.path.join(script_dir, "../.."))
# プロジェクトルートをsys.pathの先頭に追加
sys.path.insert(0, project_root)

# from agents.prompts import planner_agent_prompt, cot_planner_agent_prompt, react_planner_agent_prompt,react_reflect_planner_agent_prompt,reflect_prompt
from prompts import planner_agent_prompt
# from utils.func import get_valid_name_city,extract_before_parenthesis, extract_numbers_from_filenames
import json
import time
import asyncio
from langchain.callbacks import get_openai_callback

# planning_agentのrun_agent_sessionをインポート
from front_agents.generic_task_agent import run_agent_session

from tqdm import tqdm
# from tools.planner.apis import Planner, ReactPlanner, ReactReflectPlanner
import openai
import argparse
from datasets import load_dataset




def load_line_json_data(filename):
    data = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f.read().strip().split('\n'):
            unit = json.loads(line)
            data.append(unit)
    return data

def extract_numbers_from_filenames(directory):
    # Define the pattern to match files
    pattern = r'annotation_(\d+).json'

    # List all files in the directory
    files = os.listdir(directory)

    # Extract numbers from filenames that match the pattern
    numbers = [int(re.search(pattern, file).group(1)) for file in files if re.match(pattern, file)]

    return numbers


def catch_openai_api_error():
    error = sys.exc_info()[0]
    if error == openai.error.APIConnectionError:
        print("APIConnectionError")
    elif error == openai.error.RateLimitError:
        print("RateLimitError")
        time.sleep(60)
    elif error == openai.error.APIError:
        print("APIError")
    elif error == openai.error.AuthenticationError:
        print("AuthenticationError")
    else:
        print("API error:", error)


async def main():
    # model_name= ['gpt-3.5-turbo-1106','gpt-4-1106-preview','gemini','mixtral'][1]
    # set_type = ['dev','test'][0]
    # strategy = ['direct','cot','react','reflexion'][0]

    parser = argparse.ArgumentParser()
    parser.add_argument("--set_type", type=str, default="validation")
    parser.add_argument("--model_name", type=str, default="gpt-4.1")
    parser.add_argument("--output_dir", type=str, default="benchmarks/travel_planner/results/")
    # strategyは常にdirectなので引数から削除
    # parser.add_argument("--strategy", type=str, default="direct")
    parser.add_argument("--use_planning_server", action="store_true", help="Use planning server for run_agent_session")
    parser.add_argument("--limit", type=int, default=None, help="サンプル数の制限（指定しない場合は全サンプル）")  # サンプル数の制限の追加
    args = parser.parse_args()
    
    # コマンドライン引数からstrategyが削除されたため、directに固定
    strategy = "direct"
    
    directory = f'{args.output_dir}/{args.set_type}'
    if args.set_type == 'train':
        query_data_list  = load_dataset('osunlp/TravelPlanner','train')['train']
    elif args.set_type == 'validation':
        query_data_list  = load_dataset('osunlp/TravelPlanner','validation')['validation']
    elif args.set_type == 'test':
        query_data_list  = load_dataset('osunlp/TravelPlanner','test')['test']
    
    numbers = [i for i in range(1,len(query_data_list)+1)]
    
    # サンプル数を制限する場合
    if args.limit is not None:
        numbers = numbers[:args.limit]
        print(f"サンプル数を{args.limit}に制限します")

    # PLANNERの初期化をrun_agent_sessionに置き換えるため、この部分はコメントアウト
    # if args.strategy == 'direct':
    #     planner = Planner(model_name=args.model_name, agent_prompt=planner_agent_prompt)
    # elif args.strategy == 'cot':
    #     planner = Planner(model_name=args.model_name, agent_prompt=cot_planner_agent_prompt)
    # elif args.strategy == 'react':
    #     planner = ReactPlanner(model_name=args.model_name, agent_prompt=react_planner_agent_prompt)
    # elif args.strategy == 'reflexion':
    #     planner = ReactReflectPlanner(model_name=args.model_name, agent_prompt=react_reflect_planner_agent_prompt,reflect_prompt=reflect_prompt)


    with get_openai_callback() as cb:
        for number in tqdm(numbers[:]):
            
            query_data = query_data_list[number-1]
            reference_information = query_data['reference_information']
            while True:
                # メッセージ作成
                prompt = planner_agent_prompt.format(text=reference_information, query=query_data['query'])
                user_input = {
                    "role": "user",
                    "content": prompt
                }
                
                # 非同期関数を呼び出す
                agent_results = await run_agent_session(
                    user_input=[user_input],
                    model=args.model_name,
                    use_planning_server=args.use_planning_server
                )
                planner_results = agent_results.final_output
                
                if planner_results != None:
                    break
            
            print(planner_results)
            # check if the directory exists
            if not os.path.exists(os.path.join(f'{args.output_dir}/{args.set_type}')):
                os.makedirs(os.path.join(f'{args.output_dir}/{args.set_type}'))
            if not os.path.exists(os.path.join(f'{args.output_dir}/{args.set_type}/generated_plan_{number}.json')):
                result =  [{}]
            else:
                result = json.load(open(os.path.join(f'{args.output_dir}/{args.set_type}/generated_plan_{number}.json')))
            # if args.strategy in ['react','reflexion']:
            #     result[-1][f'{args.model_name}_{args.strategy}_sole-planning_results_logs'] = scratchpad 
            result[-1][f'{args.model_name}_{strategy}_sole-planning_results'] = planner_results
            # write to json file
            with open(os.path.join(f'{args.output_dir}/{args.set_type}/generated_plan_{number}.json'), 'w') as f:
                json.dump(result, f, indent=4)
        print(cb)

if __name__ == "__main__":
    # .env ファイル読み込み
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print(".env file loaded if found.")
    except ImportError:
        print("python-dotenv not installed, skipping .env file loading.")
        
    asyncio.run(main())