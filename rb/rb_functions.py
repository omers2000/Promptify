import json, re
from rb.request_sender import request_sender
from config.rb_consts import HEADERS, GET_REC_URL, GET_AUDIO_FEATURES_URL

def get_recommendations(params: dict) -> str:
    parsed_params = "&".join([f"{key}={value}" for key, value in params.items()])
    url = GET_REC_URL + "?" + parsed_params
    sender = request_sender()
    response_text = sender.send_request(url, method="GET", headers=HEADERS)
    return response_text

def get_audio_features(item: dict) -> dict:
    url = GET_AUDIO_FEATURES_URL.replace("{rec_id}", item["rec_id"])
    sender = request_sender()
    response_text = sender.send_request(url, method="GET", headers=HEADERS)
    response_json = json.loads(response_text)
    response_json.update({"spot_id": item["spot_id"]})
    return response_json

def parse_recommendations(response_text: str) -> list:
    response_json = json.loads(response_text)
    ids = [
        {
            "spot_id": _extract_track_id(item.get("href", "")),
            "rec_id": item.get("id")
        }
        for item in response_json.get("content", [])
    ]
    # remove None values if you want only valid ids
    ids = [i for i in ids if i["spot_id"] is not None]
    return ids

def _extract_track_id(href: str) -> str | None:
    m = re.search(r"/track/([^/?#]+)", href)
    return m.group(1) if m else None


def get_recommendations_ids_by_params(params: dict) -> list:
    response_text = get_recommendations(params)
    return parse_recommendations(response_text)


def main():
    params = {'seeds': '7qiZfU4dY1lWllzX7mPBI3', 'acousticness': 0.1, 'energy': 0.8, 'valence': 0.5, 'featureWeight': 3.0, 'size': 20}
    response_text = get_recommendations(params)
    print(response_text, "\n")
    print(parse_recommendations(response_text))
    # url = "https://api.reccobeats.com/v1/track/recommendation?size=5&seeds=7qiZfU4dY1lWllzX7mPBI3"
    # sender = request_sender()
    # response_text = sender.send_request(url, method="GET", headers=HEADERS)
    # print(response_text, "\n")
    # print(parse_recommendations(response_text))


if __name__ == "__main__":
    main()