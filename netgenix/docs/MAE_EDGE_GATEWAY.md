# MAE Edge Gateway

NetGenix can keep its application stack on a VM that cannot route directly to
Huawei MAE. An MAE-reachable edge host opens a persistent, TLS-transparent
reverse SSH tunnel to listeners bound only to the VM's Docker host-gateway
address.

## Traffic flow

```text
NetGenix backend/collector
        |
        | HTTPS to mae-edge:33xxx
        v
VM Docker host gateway
        |
        | reverse SSH tunnel
        v
MAE-reachable edge host
        |
        +--> Access NBI       41.174.191.214:31127
        +--> Access GUI       41.174.191.214:31943
        +--> Evaluation GUI   41.174.191.211:31943
        +--> Evaluation NBI   41.174.191.211:27417
```

The tunnel does not terminate TLS, inspect credentials, or expose a public
proxy. Huawei authentication and certificate handling remain inside NetGenix.

## VM endpoint configuration

Use these values in the VM's ignored `.env` file:

```dotenv
NETGENIX_HUAWEI_ACCESS_NBI_URL=https://mae-edge:33127
NETGENIX_HUAWEI_ACCESS_GUI_URL=https://mae-edge:33143/ossfacewebsite/index.html#Access/AccessHome?switch
NETGENIX_HUAWEI_EVALUATION_GUI_URL=https://mae-edge:33243/ossfacewebsite/index.html#Evaluation/prs_reportmanagement_reportList
NETGENIX_HUAWEI_EVALUATION_NBI_URL=https://mae-edge:33217
MAE_GUI_LOGIN_URL=https://mae-edge:33243/unisso/login.action?service=%2Funisess%2Fv1%2Fauth%3Fservice%3D%252Fossfacewebsite%252Findex.html&decision=1
```

The backend and collector receive `mae-edge` through Docker's `host-gateway`
mapping in `docker-compose.yml`.

The VM helper `/usr/local/sbin/netgenix-mae-edge-firewall` allows only the
NetGenix Docker subnet to reach the four listener ports on Docker's bridge
gateway address (the same address supplied by `host-gateway`).
It does not open those ports on the VM's public or LAN interfaces.

## Edge process

Run `scripts/mae-edge-tunnel.sh` on the MAE-reachable host. On macOS it should
be supervised by a LaunchAgent with `RunAtLoad` and `KeepAlive` enabled. The
script discovers the VM's current Docker host-gateway before opening the four
forwards and reconnects automatically after SSH or network interruption.

The VM requires two one-time installation steps:

```bash
sudo install -o root -g root -m 0644 \
  deploy/sshd/99-netgenix-mae-edge.conf \
  /etc/ssh/sshd_config.d/99-netgenix-mae-edge.conf
sudo sshd -t
sudo systemctl reload ssh

sudo install -o root -g root -m 0755 \
  scripts/netgenix-mae-edge-firewall.sh \
  /usr/local/sbin/netgenix-mae-edge-firewall
```

Always run `sshd -t` before reloading SSH. The firewall helper is called by
the edge process before each tunnel connection, so it restores the private
listener rule after a VM reboot or Docker network recreation.

## Verification

```bash
./scripts/check-mae-edge.sh
curl -s http://VM_ADDRESS:8510/api/diagnostics/nbi
```

The health script performs a TLS handshake from the backend container through
each relay listener. A successful handshake proves the complete container →
VM bridge → SSH → edge host → MAE path.

## Operational dependency

The edge host must remain powered on, awake, connected to the MAE-reachable
network, and able to SSH to the VM. If it disconnects, NetGenix continues to
serve historical KPI data and reports, but live Huawei queries and Evaluation
refreshes remain unavailable until the tunnel reconnects.
