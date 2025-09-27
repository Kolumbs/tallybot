"""Command line utility to start tallybot."""

import argparse
import tomllib
import sys

from zoozl.server import start


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Start tallybot server to listen to different inputs."
    )
    parser.add_argument(
        "config_path",
        type=str,
        help="Path to toml configuration file.",
    )
    args = parser.parse_args()
    with open(args.config_path, "rb") as f:
        config = tomllib.load(f)
    zoozl_cfg = {}
    if "slack" in config:
        if "port" in config["slack"]:
            zoozl_cfg["slack_port"] = config["slack"]["port"]
        else:
            print("No slack port specified in config file. Using default port 8080.")
            zoozl_cfg["slack_port"] = 8080
        if "signing_secret" in config["slack"]:
            zoozl_cfg["slack_signing_secret"] = config["slack"]["signing_secret"]
        else:
            print("No slack signing secret specified in config file. Exiting.")
            sys.exit(1)
        if "workspace_token" in config["slack"]:
            zoozl_cfg["slack_app_token"] = config["slack"]["workspace_token"]
        else:
            print("No slack workspace token specified in config file. Exiting.")
            sys.exit(1)
    start(zoozl_cfg)
