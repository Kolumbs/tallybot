# tallybot
Chat assistant to keep track of your accounting. Able to answer on slack and email messages.

## installation

```bash
pip install tallybot
```

## usage

```bash
python tallybot --help
```

### example of configuration

```toml
[slack]
port = 8080
signing_secret = "absdefg145%$"
workspace_token = "xoxb-1234567890"

[email]
enabled = true

[tallybot]
name = "tallybot"
database = "sqlite:///tallybot.db"
```
