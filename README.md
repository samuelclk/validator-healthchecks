# TLDR
Simple and lightweight health checker service for Lido CSM or DVT operators to monitor client-level health and send alerts via Telegram otherwise.

Healthchecks.io (Free!) notifies users if the health checker service itself is offline.

Follow me on [Twitter](https://x.com/stakesaurus) or subscribe to my [newsletter](https://stakesaurus.beehiiv.com/) if you find this useful for you!

*Special thanks to Eridian for sharing about [healthchecks.io](https://healthchecks.io/) with me! He also has a more scalable monitoring/alerting setup which you can check out [here](https://docs.eridian.xyz/infrastructure-docs/alerting-and-monitoring).

# How it works

- **HTTP & CURL Requests:** The service periodically makes an HTTP GET or CURL request to the specified IP address, port, health, & metrics endpoints. e.g. http://127.0.0.1:8008 (CL health endpoint). This requests the server to respond with their "health" status.

- **Concurrent "check-in" with Healthchecks.io:** Each time the service runs successfully, it sends a message to Healthchecks.io, informing it of the successful run.

- **Service Response:** For the service to consider the consensus or execution client to be "up," the service at the IP address and port must respond to the HTTP request. This typically involves the client's API or a health check endpoint responding with an HTTP status code of 200 OK, indicating that the service is operational and can handle requests.

- **Timeout Handling:** The service includes a timeout (e.g., 5 seconds), ensuring that if the client doesn't respond within a reasonable timeframe, it's considered "down." This helps differentiate between an unresponsive service and one that's simply slow to reply.

- **Send Alert Message:** Finally, the script sends a message to the chat groups designated for each endpoint that was checked if it is “down” or “cannot be reached”.

- **Self-Reporting:** Healthchecks.io notifies the user if the alerting service itself is down.

# How to use

## Preparation
### Telegram bot token & Chat ID
1) Open Telegram and search for @BotFather.
2) Start a chat with BotFather by clicking the Start button.
3) Send the command:
```
/newbot
```
4) Follow the prompts:
- Name your bot (e.g., MyCoolBot).
- Choose a username that ends with bot (e.g., my_cool_bot).
- Once created, BotFather will send you a message with your `bot token`:
```
123456789:ABCDefGhIJKLMnoPQRStUvWxYZ
```
5) Save this token somewhere safe.
6) Go to your newly created bot on Telegram (search for its username, e.g., @my_cool_bot) and start the bot by clicking the `Start` button.
7) Create a new group & add your bot to the group
8) Send a message in the group (e.g., "Hello, bot!").
9) Open up a browser and enter the following (Replace YOUR_BOT_TOKEN with your bot's token)
```
https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
```
10) Look for the chat object in the response. The `id` under chat is your group `Chat ID` (e.g., `-987654321`). For example:
```
{
  "ok": true,
  "result": [
    {
      "update_id": 123456789,
      "message": {
        "chat": {
          "id": -987654321,
          "title": "MyGroup",
          "type": "group"
        },
        "text": "Hello, bot!"
      }
    }
  ]
}
```
You now have your `BOT_TOKEN` and `CHAT_ID`.
### Healthchecks.io URL
1) Go to Healthchecks.io.
2) Sign-up/Log-in with your preferred method (email, GitHub, or Google).
3) Click on "Add Check" on the dashboard. Select 5 minutes for the **Period** and 10 minutes for the **Grace Time** 
4) On the check's configuration page, you’ll find a "Ping URL". It looks like this:
```
https://hc-ping.com/your-unique-id
```
5) Go to your **Integrations** page and select the Telegram integration: **Profile>>Integrations>>Telegram**
6) Enter your Telegram **Bot Token** and **Chat ID**
7) Add the Healthchecks.io bot into your Telegram chat group: `@Healthchecks_io_bot`

You now have your `HEALTHCHECK_URL` and have both your own Telegram bot and the Healthchecks.io bot in your Telegram group. e.g.,

<img width="625" alt="Screenshot 2025-01-28 at 11 27 18 PM" src="https://github.com/user-attachments/assets/61cb2a70-6c37-4dc9-adcc-5cfbfd72fa06" />

### Make sure your monitoring endpoints are accessible
**All Users**
1) **SSV node:** Enable the health endpoint by adding `SSVAPIPort: 16000` into the **config.yaml** file.
2) **SSV DKG & Obol Charon:** No changes needed as we will query the P2P ports for these.

**Systemd & EthPillar Users:**
1) **Execution clients:** Add the `--http` or equivalent flag. This is set to port 8545 on default.
2) **Consensus client:** Add the `--metrics` or equivalent flag and set `--metrics-port=8008`
3) **Validator client:** Add the `--metrics` or equivalent flag and set `--metrics-port=8009`

**Eth Docker Users:**

Map the monitoring ports of your EL, CL, & VC to the host
```
nano ~/eth-docker/cl-shared.yml
```
Replace with the following:
```
services:
  consensus:
    ports:
      - ${SHARE_IP:-}:${CL_REST_PORT:-5052}:${CL_REST_PORT:-5052}/tcp
      - ${SHARE_IP:-}:8008:8008/tcp
  validator:
    ports:
      - ${SHARE_IP:-}:8009:8009/tcp
```
Edit the `.env` file.
```
nano ~/eth-docker/.env
```
Append `:el-shared.yml:cl-shared.yml` into the `COMPOSE_FILE=` line.

***Note:** You will have to make this edit everytime you update your Eth Docker repository.

## Setup
Clone this git repository
```
cd && git clone https://github.com/samuelclk/validator-healthchecks.git
```

Create a `.env` 
```
nano ~/validator-healthchecks/.env
```

Paste the following content in your `.env` file and replace `BOT_TOKEN=TELEGRAM_BOT_TOKEN`, `CHAT_ID=GROUP_CHAT_ID`, & `HEALTHCHECK_URL=https://hc-ping.com/your-unique-id` with your actual credentials.

```
BOT_TOKEN=TELEGRAM_BOT_TOKEN
CHAT_ID=GROUP_CHAT_ID
HEALTHCHECK_URL=https://hc-ping.com/your-unique-id

# HTTP-based endpoints monitored via HTTP GET requests for EL, CL, & SSV nodes
HTTP_EXECUTION_CLIENT=http://127.0.0.1:8545/health
HTTP_CONSENSUS_CLIENT=http://127.0.0.1:8008/health
HTTP_SSV_NODE=http://127.0.0.1:16000/v1/node/health
## Add more EL, CL, or SSV node endpoints here as needed in this format: "HTTP_XX_XX". "HTTP" must be the prefix.

# Command-based monitoring for validator clients
COMMAND_VALIDATOR_CLIENT=curl -s http://127.0.0.1:8009/metrics | grep -E -q '(get_validators_liveness|beacon_attestation_included_total|lighthouse_validator_beacon_node_requests_total|nimbus_validator>

## Add more VC endpoints here as needed in this format: "COMMAND_XX_XX=". "COMMAND" must be the prefix. Change only the "127.0.0.1:8009" part of the variable

# P2P-based nodes for Obol Charon & SSV DKG (host:port format)
P2P_OBOL_CHARON=127.0.0.1:3610
P2P_SSV_DKG=127.0.0.1:3030

## Add more Obol Charon or SSV DKG endpoints here as needed in this format: "P2P_XX_XX=". "P2P" must be the prefix.
```
Save & exit with `CTRL+O`, `ENTER`, `CTRL+X`.

Install docker.
```
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

sudo groupadd docker
sudo usermod -aG docker $USER
```
Log out and then back in again for the new user group settings to take effect.
```
exit
```
Build the docker image.
```
cd ~/validator-healthchecks
docker compose build
```
## Run the tool
Run the health checker service as a docker service.
```
docker compose up -d
```
Check for errors.
```
docker logs validator-healthchecks -f --tail 20
```
You should see the following:
```
Execution Client is healthy
Consensus Client is healthy.
Ssv Node is healthy.
Validator Client is healthy.
Obol Charon is up.
Ssv Dkg is up.
Healthcheck ping successful.
```
This health checker service runs once every 5 minutes and sends a message to Healthchecks.io immediately after.

If any of your monitored services are unhealthy or unreachable, it will send a telegram message to your designated group chat via your Telegram bot. 

If Healthchecks.io does not receive a message from your health checker service, it will send a message to your Telegram chat group to notify that your health checker service itself is offline.

# Context
Most solo stakers rely on [beaconcha.in](https://beaconcha.in) watchlists to notify them when their validators are missing attestations. 

However, in some scenarios, this method no longer works well for solo stakers. e.g.,
- **Running many validator keys via Lido CSM or similar platforms:** It's not useful to receive 10 to 100 notifications every 6.5 minutes from beaconcha.in when the issue could lie with your EL, CL, or VC directly.
- **Running DVTs:** Because your nodes could be offline without causing missed attestations--e.g., a cluster of X nodes is responsible for operating Y validator keyshares. 

This problem is especially pronounced for DVT operators as they may only act when the cluster fails to achieve consensus as a whole, leading to free-rider problems.

Hence, I needed a way of being notified when each of my core services is unhealthy instead of relying solely on onchain alerts. I also want to be alerted when my health checker service itself fails.

I settled on a custom Python script running in a docker container that queries the health, metrics, or p2p endpoints of the consensus, execution, validator, & DVT clients of your setup periodically and sends a Telegram message to yourself or a chat group if it fails. Healthchecks.io alerts you if your health checker service itself fails.

It's a lightweight solution ideal for scenarios where detailed metrics and alerts are not required.

Using [beaconcha.in](https://beaconcha.in)'s watchlist as an alerting mechanism is popular because it is simple to use, free, and requires no maintenance. These are also the design principles for my solution.

_**Disclaimer:** This is meant to be a fun project for solo stakers and is in no way meant to replace professional monitoring tools used by institutions. There might also be other free + plug-and-play solutions out there._

