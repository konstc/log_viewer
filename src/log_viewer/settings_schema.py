""" Application settings JSON schema """

APP_SETTINGS_SCHEMA = {
    "type": "object",
    "properties": {
        "mode": {"enum": ["simple_csv", "j1939_dump"]},
        "plot": {
            "type": "object",
            "properties": {
                "style": {"type": "string"},
                "linestyle": {"enum": ["solid", "dashed", "dashdot", "dotted"]},
                "linewidth": {"enum": [0.5, 1.0, 1.5, 2.0]},
                "marker": {"type": "boolean"},
                "use_mpl_toolbar": {"type": "boolean"},
                "cursor": {
                    "type": "object",
                    "properties": {
                        "style": {"enum": ["solid", "dashed", "dashdot", 
                                           "dotted"]},
                        "width": {"enum": [0.25, 0.5, 0.75, 1.0]},
                        "color": {"enum": ["red", "green", "blue", "cyan", 
                                           "magenta", "yellow", "black"]}
                    },
                    "required": ["style", "width", "color"]
                }
            },
            "required": ["style", "linestyle", "linewidth", "marker",
                         "use_mpl_toolbar", "cursor"]
        },
        "simple_csv": {
            "type": "object",
            "properties": {
                "delimiter": {"type": "string"},
                "timestamp": {"type": "string"},
                "scales": {
                    "type": "object",
                    "patternProperties": {
                        ".": {"type": "number"}
                    }
                }
            },
            "required": ["delimiter", "timestamp", "scales"]
        },
        "j1939_dump": {
            "type": "object",
            "properties": {
                "asc_base": {"enum": ["hex", "dec"]},
                "asc_rel_timestamp": {"type": "boolean"},
                "db": {"type": "array", "items": {"type": "string"}
                }
            },
            "required": ["asc_base", "asc_rel_timestamp", "db"]
        }
    },
    "required": ["mode", "plot"]
}
