#!/usr/bin/env bash
set -euo pipefail

source_network="${1:-netgenix_default}"
listener_network="${2:-bridge}"
ports="33127,33143,33243,33217"

listener_gateway="$(docker network inspect "${listener_network}" --format '{{range .IPAM.Config}}{{.Gateway}}{{end}}')"
source_gateway="$(docker network inspect "${source_network}" --format '{{range .IPAM.Config}}{{.Gateway}}{{end}}')"
source_subnet="$(docker network inspect "${source_network}" --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}')"

[[ "${listener_gateway}" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] || exit 2
[[ "${source_gateway}" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] || exit 2
[[ "${source_subnet}" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}$ ]] || exit 2

if command -v nft >/dev/null && nft list chain ip filter INPUT >/dev/null 2>&1; then
  # Replace any previous rule so Docker network recreation or a gateway
  # correction cannot leave a valid-looking but stale firewall entry behind.
  while read -r handle; do
    [[ -n "${handle}" ]] && nft delete rule ip filter INPUT handle "${handle}"
  done < <(
    nft -a list chain ip filter INPUT \
      | awk '/comment "netgenix-mae-edge"/ {for (i=1; i<=NF; i++) if ($i == "handle") print $(i+1)}'
  )

  nft insert rule ip filter INPUT \
    ip saddr "${source_subnet}" \
    ip daddr "${listener_gateway}" \
    tcp dport \{ 33127, 33143, 33243, 33217 \} \
    counter accept \
    comment "netgenix-mae-edge"
else
  old_rule=(
    INPUT
    -s "${source_subnet}"
    -d "${source_gateway}"
    -p tcp
    -m multiport
    --dports "${ports}"
    -m comment
    --comment netgenix-mae-edge
    -j ACCEPT
  )
  rule=(
    INPUT
    -s "${source_subnet}"
    -d "${listener_gateway}"
    -p tcp
    -m multiport
    --dports "${ports}"
    -m comment
    --comment netgenix-mae-edge
    -j ACCEPT
  )

  while iptables -C "${old_rule[@]}" 2>/dev/null; do
    iptables -D "${old_rule[@]}"
  done
  if ! iptables -C "${rule[@]}" 2>/dev/null; then
    iptables -I "${rule[@]}"
  fi
fi
