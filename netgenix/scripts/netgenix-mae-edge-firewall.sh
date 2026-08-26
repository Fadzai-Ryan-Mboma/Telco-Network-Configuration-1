#!/usr/bin/env bash
set -euo pipefail

network="${1:-netgenix_default}"
ports="33127,33143,33243,33217"

gateway="$(docker network inspect "${network}" --format '{{range .IPAM.Config}}{{.Gateway}}{{end}}')"
subnet="$(docker network inspect "${network}" --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}')"

[[ "${gateway}" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] || exit 2
[[ "${subnet}" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}$ ]] || exit 2

if command -v nft >/dev/null && nft list chain ip filter INPUT >/dev/null 2>&1; then
  if ! nft -a list chain ip filter INPUT | grep -q 'comment "netgenix-mae-edge"'; then
    nft insert rule ip filter INPUT \
      ip saddr "${subnet}" \
      ip daddr "${gateway}" \
      tcp dport \{ 33127, 33143, 33243, 33217 \} \
      counter accept \
      comment "netgenix-mae-edge"
  fi
else
  rule=(
    INPUT
    -s "${subnet}"
    -d "${gateway}"
    -p tcp
    -m multiport
    --dports "${ports}"
    -m comment
    --comment netgenix-mae-edge
    -j ACCEPT
  )

  if ! iptables -C "${rule[@]}" 2>/dev/null; then
    iptables -I "${rule[@]}"
  fi
fi
