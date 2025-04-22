from smolagents.agent_types import AgentType


def normalize_result(result) -> str:
    """
    result が以下の型のときに一律文字列に変換して返す:
      - AgentType 継承クラス: .to_string() の結果
      - int: str() にて文字列化
      - dict: キーと値を階層化して整形
      - list: 要素ごとに階層化して整形
      - その他: str() で文字列化
    """
    # AgentType (AgentText, AgentImage, …) の場合
    if isinstance(result, AgentType):
        return result.to_string()

    # int の場合
    if isinstance(result, int):
        return str(result)

    # dict の場合: 階層化して文字列化
    if isinstance(result, dict):
        return _dict_to_str(result)

    # list の場合: 各要素を階層化して文字列化
    if isinstance(result, list):
        return _list_to_str(result)

    # その他の型は一律文字列化
    return str(result)


def _dict_to_str(d: dict, indent: int = 0) -> str:
    """
    dict をインデント付きで文字列化
    """
    lines = []
    prefix = '  ' * indent
    for key, val in d.items():
        if isinstance(val, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_dict_to_str(val, indent + 1))
        elif isinstance(val, list):
            lines.append(f"{prefix}{key}:")
            lines.append(_list_to_str(val, indent + 1))
        else:
            lines.append(f"{prefix}{key}: {val}")
    return "\n".join(lines)


def _list_to_str(lst: list, indent: int = 0) -> str:
    """
    list をインデント付きで文字列化
    """
    lines = []
    prefix = '  ' * indent
    for item in lst:
        if isinstance(item, dict):
            lines.append(f"{prefix}-")
            lines.append(_dict_to_str(item, indent + 1))
        elif isinstance(item, list):
            lines.append(f"{prefix}-")
            lines.append(_list_to_str(item, indent + 1))
        else:
            lines.append(f"{prefix}- {item}")
    return "\n".join(lines)
