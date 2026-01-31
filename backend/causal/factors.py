from datetime import datetime, timezone

# Factor taxonomy — all known causal factors and target variables
SIGNAL_FACTORS = [
    {
        "id": "electricity_demand_pjm",
        "label": "PJM Electricity Demand",
        "type": "signal",
        "source": "eia_electricity",
    },
    {
        "id": "electricity_demand_ercot",
        "label": "ERCOT Electricity Demand",
        "type": "signal",
        "source": "eia_electricity",
    },
    {
        "id": "electricity_demand_ciso",
        "label": "CAISO Electricity Demand",
        "type": "signal",
        "source": "eia_electricity",
    },
    {
        "id": "temperature_us_east",
        "label": "Temperature (us-east-1 / Virginia)",
        "type": "signal",
        "source": "weather",
    },
    {
        "id": "temperature_us_west",
        "label": "Temperature (us-west-2 / Oregon)",
        "type": "signal",
        "source": "weather",
    },
    {
        "id": "time_of_day",
        "label": "Time of Day (UTC hour)",
        "type": "derived",
        "source": "system",
    },
    {
        "id": "day_of_week",
        "label": "Day of Week",
        "type": "derived",
        "source": "system",
    },
]

TARGET_FACTORS = [
    {
        "id": "spot_price_p3_2xlarge",
        "label": "p3.2xlarge Spot Price",
        "type": "target",
        "source": "aws_spot",
    },
    {
        "id": "spot_price_g4dn_xlarge",
        "label": "g4dn.xlarge Spot Price",
        "type": "target",
        "source": "aws_spot",
    },
    {
        "id": "spot_price_g5_xlarge",
        "label": "g5.xlarge Spot Price",
        "type": "target",
        "source": "aws_spot",
    },
]

ALL_FACTORS = SIGNAL_FACTORS + TARGET_FACTORS


def get_initial_graph() -> dict:
    """Create the seed causal graph with uniform weights.

    All plausible signal→target edges start at weight 0.5.
    The learner will strengthen/weaken these based on prediction accuracy.
    """
    now = datetime.now(timezone.utc).isoformat()
    nodes = [
        {"id": f["id"], "label": f["label"], "type": f["type"], "source": f["source"]}
        for f in ALL_FACTORS
    ]

    edges = {}
    for signal in SIGNAL_FACTORS:
        for target in TARGET_FACTORS:
            edge_key = f"{signal['id']}->{target['id']}"
            edges[edge_key] = {
                "from": signal["id"],
                "to": target["id"],
                "weight": 0.5,
                "confidence": 0.5,
                "direction": "positive",
                "update_count": 0,
                "last_updated": now,
            }

    # Add some plausible signal→signal edges
    # Temperature affects electricity demand
    for temp in ["temperature_us_east", "temperature_us_west"]:
        for demand in ["electricity_demand_pjm", "electricity_demand_ercot", "electricity_demand_ciso"]:
            edge_key = f"{temp}->{demand}"
            edges[edge_key] = {
                "from": temp,
                "to": demand,
                "weight": 0.5,
                "confidence": 0.5,
                "direction": "positive",
                "update_count": 0,
                "last_updated": now,
            }

    return {
        "version": 0,
        "nodes": nodes,
        "edges": edges,
        "created_at": now,
        "last_updated": now,
    }
