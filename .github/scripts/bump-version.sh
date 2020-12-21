#!/bin/bash
set -e
set -o pipefail

script_dir=$(dirname "$0")
cd $script_dir

[ ! -z "$1" ] || (echo "Please supply version string as first parameter"; exit 1)
version_str=$1

setup_config_file="../../setup.py"
release_tag="v$version_str"
release_branch="$release_tag-release"

echo "Checking out release branch $release_branch"
git checkout -b $release_branch

echo "Updating the version to $version_str"
# Note this if statement is for cross platform support between Linux/OSX
if [[ "$OSTYPE" == "darwin"* ]]; then
  sed -i '' -e 's/VERSION = ".*"/VERSION = "'"$version_str"'"/' $setup_config_file
else
  sed -i -e 's/VERSION = ".*"/VERSION = "'"$version_str"'"/' $setup_config_file
fi

echo "Creating commit for $release_branch"
git add $setup_config_file
git commit -m "Updated version for release of version $version_str"

echo "Pushing $release_branch"
git push origin $release_branch

echo "Creating and pushing tag for version $version_str"
git tag -a "$release_tag" -m "Tag Dolt version $version_str"
git push origin $release_tag
