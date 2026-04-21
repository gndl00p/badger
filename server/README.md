# Badger Aggregator

FastAPI service that feeds the Badger 2040 W desk-mode dashboard.

## Run (dev)

    cd ~/code/badger
    source server/.venv/bin/activate
    cp server/.env.example server/.env   # then fill in secrets
    uvicorn server.app:app --host 127.0.0.1 --port 8088 --env-file server/.env

## Test

    cd ~/code/badger
    source server/.venv/bin/activate
    pytest server/tests -v

## Deploy (user systemd)

    mkdir -p ~/.config/systemd/user
    cp server/badger.service ~/.config/systemd/user/badger.service
    systemctl --user daemon-reload
    systemctl --user enable --now badger
    systemctl --user status badger
