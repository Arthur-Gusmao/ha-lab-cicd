# Recorded validation

This is a historical evidence record, not a live status dashboard.
Times below use America/Sao_Paulo (UTC-03:00).

## Automatic application deployment — October 8, 2026

Application commit:
[`25ffe18`](https://github.com/Arthur-Gusmao/ha-lab-cicd/commit/25ffe18d3b84df6488bb2aec92be345543e606ff).

The page heading changed from `HA-LAB` to `HA-LAB - Automated Deployment`.
The user pushed this commit to master. No manual web-server update was needed
for the deployment recorded below.

[Associated CI run](https://github.com/Arthur-Gusmao/ha-lab-cicd/actions/runs/37782514230).

Relevant messages read from the local systemd journal:

```text
Oct 08 10:16:22 Approved CI: https://github.com/Arthur-Gusmao/ha-lab-cicd/actions/runs/37782514230
Oct 08 10:16:34 Deployment verified: 192.168.56.11
Oct 08 10:16:37 Deployment verified: 192.168.56.12
Oct 08 10:16:37 Deployment complete; both hosts and VIP verified: 25ffe18d3b84df6488bb2aec92be345543e606ff
```

The excerpt omits workstation identifiers and process IDs. It preserves the
timestamps, target addresses and controller messages. Under the installed
controller's validation logic, completion means both service/image/content
checks and the ten VIP content checks passed.

## Earlier controller deployment — October 7, 2026

Commit `196bc4d9c4a609cd4eba143138d4a31267451147` completed at 12:02:59.
Both web hosts and VIP were verified. On October 8 at 09:58:22, the resumed
timer reported `Already deployed` for that commit. This confirms that the
controller resumed and retained state; it does not demonstrate VM health
after reboot.

## Automated test coverage

The controller tests cover rejection of ineligible workflow results, reverse
rollback ordering and failed-commit blocking, and preservation of pending
state when rollback fails. They use mocks rather than failing the live lab.

## Not yet demonstrated

- Load-balancer failover after shutting down the active load balancer.
- Backend failure behavior and in-flight connection handling.
- Live forced deployment failure followed by successful rollback.
- Complete VM provisioning from a clean machine using repository contents.
- A production availability or recovery-time guarantee.

Record each future experiment with its trigger, expected behavior, actual
result, timestamps, and restoration procedure before marking it validated.
