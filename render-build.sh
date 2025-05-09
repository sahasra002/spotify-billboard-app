#!/usr/bin/env bash
# Install Rust
curl https://sh.rustup.rs -sSf | sh -s -- -y
source $HOME/.cargo/env
# Proceed with the build
pip install -r requirements.txt