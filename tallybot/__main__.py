"""Command line utility to start tallybot."""

import argparse
import tomllib
import sys

from zoozl.server import start


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="tallybot",
        description="Start tallybot server to listen to different inputs.",
    )
    parser.add_argument(
        "config_path",
        type=str,
        help="Path to toml configuration file.",
    )
    args = parser.parse_args()
    with open(args.config_path, "rb") as f:
        config = tomllib.load(f)
    if "tallybot" not in config:
        print("No `tallybot` configuration found in config file.")
        sys.exit(1)
    if "database" not in config["tallybot"]:
        print(
            "No `database` configuration found in `tallybot` section of config file."
        )
        sys.exit(1)
    zoozl_cfg = {
        "memory_path": f'sqlite://{config["tallybot"]["database"]}',
        "extensions": ["tallybot.plugin"],
        "tallybot": config["tallybot"],
    }
    if "log_level" in config["tallybot"]:
        zoozl_cfg["log_level"] = config["tallybot"]["log_level"]
    if "slack" in config:
        if "port" in config["slack"]:
            zoozl_cfg["slack_port"] = config["slack"]["port"]
        else:
            print(
                "No slack port specified in config file. Using default port 8080."
            )
            zoozl_cfg["slack_port"] = 8080
        if "signing_secret" in config["slack"]:
            zoozl_cfg["slack_signing_secret"] = config["slack"][
                "signing_secret"
            ]
        else:
            print("No slack signing secret specified in config file. Exiting.")
            sys.exit(1)
        if "workspace_token" in config["slack"]:
            zoozl_cfg["slack_app_token"] = config["slack"]["workspace_token"]
        else:
            print("No slack workspace token specified in config file. Exiting.")
            sys.exit(1)
    start(zoozl_cfg)
