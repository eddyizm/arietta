import requests


def add_reaction(url, token, reaction):
    """Adds a reaction (+1 or -1) to the triggering comment."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    payload = {"content": reaction}
    requests.post(
        url,
        headers=headers,
        json=payload
    )

def add_label(url, headers, value):
    # If label doesn't exist it gets created
    response = requests.post(url, headers=headers, json={"labels": [value]})
    return response.status_code == 200 or response.status_code == 201


def add_milestone(url_milestone, url_issue, headers, value):
    m_response = requests.get(url_milestone, headers=headers)
    if m_response.status_code != 200:
        return False

    milestone_id = None
    # Can only add existent milestones
    for m in m_response.json():
        if m["title"].lower() == value.lower():
            milestone_id = m["number"]
            break

    if not milestone_id:
        return False

    response = requests.patch(url_issue, headers=headers, json={"milestone": milestone_id})
    return response.status_code == 200
