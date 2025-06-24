import json
from pathlib import Path

CREATED_JSON_DIR = Path("created_json")
OUTPUT_JSONL = "flattened_cdrs.jsonl"

def flatten_record(record):
    organizer = record.get("organizerUPN")
    call_type = record.get("callType")
    conference_id = record.get("conferenceId")
    sessions = record.get("sessions", [])

    flat = {
        "organizerUPN": organizer,
        "callType": call_type,
        "conferenceId": conference_id,
        "sessionCount": len(sessions),
        "participantRoles": [],
        "notableMetrics": [],
    }

    for session in sessions:
        for participant in session.get("participants", []):
            flat["participantRoles"].append(participant.get("role"))
            for stream in participant.get("streams", []):
                avg_jitter = stream.get("averageJitter")
                packet_loss = stream.get("packetLossRate")
                avg_rtt = stream.get("averageRoundTripTime")
                glitch_rate = stream["deviceMetrics"].get("glitchRate") if "deviceMetrics" in stream else None
                sent_signal = stream["deviceMetrics"].get("sentSignalLevel") if "deviceMetrics" in stream else None

                desc = (f"role:{participant.get('role')} avgJitter:{avg_jitter} packetLoss:{packet_loss} "
                        f"avgRTT:{avg_rtt} glitchRate:{glitch_rate} sentSignalLevel:{sent_signal}")
                flat["notableMetrics"].append(desc)

    summary = (
        f"Call by {organizer}, type: {call_type}. "
        f"Participants: {', '.join(flat['participantRoles'])}. "
        f"Session count: {flat['sessionCount']}. "
        f"Metrics: {' | '.join(flat['notableMetrics'])}."
    )

    return {
        "conferenceId": conference_id,
        "organizerUPN": organizer,
        "summary": summary,
        "notableMetrics": flat["notableMetrics"]
    }

if __name__ == "__main__":
    files = list(CREATED_JSON_DIR.glob("*.json"))
    with open(OUTPUT_JSONL, "w") as fout:
        for fp in files:
            with open(fp) as fin:
                rec = json.load(fin)
                flat = flatten_record(rec)
                fout.write(json.dumps(flat) + "\n")
    print(f"Flattened {len(files)} records into {OUTPUT_JSONL}")
