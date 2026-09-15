FROM ubuntu:24.04

ARG RUNNER_VERSION=2.337.0
ARG RUNNER_SHA256=70920811a4f8ad4328818682bca5c6469c1c942fab52448868071d0063816613

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl git jq unzip zip tar gzip python3 python3-venv \
    libicu74 libssl3t64 libkrb5-3 zlib1g liblttng-ust1t64 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1001 runner

WORKDIR /home/runner/actions-runner
RUN curl --fail --silent --show-error --location \
    "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" \
    --output /runner.tar.gz \
    && echo "${RUNNER_SHA256}  /runner.tar.gz" | sha256sum --check - \
    && tar xzf /runner.tar.gz \
    && rm /runner.tar.gz \
    && chown -R runner:runner /home/runner/actions-runner

# Supply fresh single-job JIT configuration, never an App key or installation token.
USER runner
ENTRYPOINT ["/bin/bash", "-euc", "config=${RUNNER_JIT_CONFIG:?RUNNER_JIT_CONFIG is required}; unset RUNNER_JIT_CONFIG; exec ./run.sh --jitconfig \"$config\""]
