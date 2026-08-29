#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 user@host:/absolute/project/path" >&2
    exit 2
fi

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
destination=${1%/}

rsync -av --progress \
    "$project_root/backend/assets/" \
    "$destination/backend/assets/"
