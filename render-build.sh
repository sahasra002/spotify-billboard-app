#!/usr/bin/env bash
# Install Rust in a writable directory
curl https://sh.rustup.rs -sSf | sh -s -- -y --default-toolchain stable --profile minimal --no-modify-path
export PATH="$HOME/.cargo/bin:$PATH"
# Proceed with the build
pip install -r requirements.txt