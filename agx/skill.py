from typing import Optional

import requests
from openai import OpenAI

import config


def run_skill_voice(text: str) -> dict:
    prompt = _build_prompt_voice(text)
    raw = _call_llm(prompt)
    return _parse_and_dispatch(raw, None)


def run_skill_vision(label: str, confidence: float) -> dict:
    prompt = _build_prompt_vision(label, confidence)
    raw = _call_llm(prompt)
    return _parse_and_dispatch(raw, confidence)


def _build_prompt_voice(text: str) -> str:
    return (
        f"你是垃圾分類助理。使用者說：「{text}」。\n\n"
        "請判斷這是哪種垃圾，只能回答以下其中一個英文詞：\n\n"
        "tissue / paper_box / plastic_can\n\n"
        "不得有其他文字或標點。"
    )


def _build_prompt_vision(label: str, confidence: float) -> str:
    return (
        f"你是垃圾分類助理。相機偵測到物體為：{label}（信心值 {confidence:.2f}）。\n\n"
        "請確認分類，只能回答以下其中一個英文詞：\n\n"
        "tissue / paper_box / plastic_can\n\n"
        "不得有其他文字或標點。"
    )


def _call_llm(prompt: str) -> str:
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=20,
    )
    return (response.choices[0].message.content or "").strip()


def _parse_and_dispatch(raw: str, confidence: Optional[float]) -> dict:
    label = raw.strip()
    if label not in config.CLASS_NAMES:
        raise ValueError(f"無法辨識類別: {raw}")

    bin_value = config.BIN_MAP[label]
    message = config.MESSAGE_MAP[label]
    move_url = config.RPI_URL.rstrip("/") + "/move"

    try:
        response = requests.post(
            move_url,
            json={"bin": bin_value},
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Warning: failed to dispatch move command: {exc}")

    return {
        "bin": bin_value,
        "label": label,
        "message": message,
        "confidence": confidence,
    }
