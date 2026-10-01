#!/bin/bash
#
# export-pull-images.sh
#
# Run this on the SOURCE host (10.10.10.13).
# It saves one or more local Docker images, copies the archives to every
# destination host, then loads them there.
#
#   Usage: ./export-pull-images.sh <image> [<image> ...]
#
# Example: ./export-pull-images.sh nginx:latest redis:7

set -euo pipefail

# --- Configuration ----------------------------------------------------------
DESTINATIONS=(
    "ubuntu@10.10.10.14"
    "ubuntu@10.10.10.15"
)

# Remote directory used to stage the image archives.
REMOTE_TMP="/tmp"

# --- Arguments ---------------------------------------------------------------
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <image> [<image> ...]" >&2
    exit 1
fi

IMAGES=("$@")

# --- Helpers -----------------------------------------------------------------
# Turn an image reference (e.g. "nginx:latest" or "repo/app:1.0") into a safe
# filename (e.g. "nginx_latest.tar").
image_to_filename() {
    local image="$1"
    echo "${image//[\/:]/_}.tar"
}

# --- Process each image ------------------------------------------------------
for image in "${IMAGES[@]}"; do
    filename="$(image_to_filename "$image")"
    local_path="${REMOTE_TMP}/${filename}"

    echo "==> Saving '${image}' locally to ${local_path}"
    docker save -o "${local_path}" "${image}"

    for dest in "${DESTINATIONS[@]}"; do
        dest_path="${REMOTE_TMP}/${filename}"

        echo "    -> Copying '${filename}' to ${dest}"
        scp "${local_path}" "${dest}:${dest_path}"

        echo "    -> Loading '${image}' on ${dest}"
        ssh "$dest" "docker load -i '${dest_path}' && rm -f '${dest_path}'"
    done

    echo "    -> Cleaning up local ${local_path}"
    rm -f "${local_path}"

    echo "==> Done with '${image}'"
    echo
done

echo "All images processed successfully."
