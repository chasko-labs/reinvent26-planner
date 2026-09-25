import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cli"))

from reinvent26 import inventory, schedule  # noqa: E402


def test_load_tag_mapping_list(tmp_path):
    payload = {
        "ResourceTagMappingList": [
            {"ResourceARN": "arn:aws:lambda:us-east-1:123:function:web",
             "ResourceType": "lambda"},
            {"ResourceARN": "arn:aws:dynamodb:us-east-1:123:table/sess",
             "ResourceType": "dynamodb"},
        ]
    }
    p = tmp_path / "resources.json"
    p.write_text(json.dumps(payload))
    resources = inventory.load_resources_file(str(p))
    assert len(resources) == 2
    kws = schedule.stack_keywords(resources)
    assert "lambda" in kws and "dynamodb" in kws


def test_load_bare_array(tmp_path):
    p = tmp_path / "r.json"
    p.write_text(json.dumps([{"service": "Amazon Bedrock"}]))
    resources = inventory.load_resources_file(str(p))
    assert "bedrock" in schedule.stack_keywords(resources)


def test_fetch_requires_explicit_profile():
    try:
        inventory.fetch_via_aws_cli("")
    except ValueError:
        return
    raise AssertionError("expected ValueError for missing profile")


def test_summarize_counts():
    out = inventory.summarize_inventory(
        [{"ResourceType": "lambda"}, {"ResourceType": "lambda"},
         {"ResourceType": "s3"}]
    )
    assert out[0] == ("lambda", 2)


def test_stack_pick_end_to_end_names_services_in_use():
    resources = [
        {"ResourceARN": "arn:aws:lambda:us-east-1:123:function:api",
         "ResourceType": "lambda"},
        {"ResourceARN": "arn:aws:bedrock:us-east-1:123:model/x",
         "ResourceType": "bedrock"},
    ]
    kws = schedule.stack_keywords(resources)
    sessions = [
        {"sessionId": "a", "code": "AIM301", "title": "agents with bedrock",
         "topics": ["agents"], "level": "300",
         "startTime": "2026-12-01T10:00:00", "endTime": "2026-12-01T11:00:00"},
        {"sessionId": "b", "code": "STO201", "title": "s3 deep dive",
         "topics": ["storage"], "level": "200",
         "startTime": "2026-12-01T10:00:00", "endTime": "2026-12-01T11:00:00"},
    ]
    ranked = schedule.match_topics(sessions, kws)
    assert ranked and ranked[0]["sessionId"] == "a"
    assert any(t in kws for t in ("bedrock", "lambda", "agents"))


def test_summarize_personal_time_fallbacks():
    from reinvent26.schedule import summarize
    line = summarize({"blockId": "b1", "title": "Lunch",
                      "start": "2026-12-01T12:00:00",
                      "end": "2026-12-01T13:00:00"})
    assert line.startswith("b1 | Lunch")
    assert "2026-12-01T12:00:00->2026-12-01T13:00:00" in line
