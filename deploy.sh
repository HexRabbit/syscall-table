#!/bin/bash
cd "$(dirname "$0")"

if [ ! -f www/index.html ]; then
  echo "Please run python3 gen_syscalls.py [args] first!"
  exit 0
fi

git fetch
kernel_version=$(grep -Eo 'Linux kernel v[0-9]*\.[0-9]*(\.[0-9]*)?(-rc[0-9])?' www/index.html | cut -d ' ' -f3)

if [ $(git tag -l $kernel_version) ]; then
  echo "Version $kernel_version exist, aborting..."
  exit 0
fi

git checkout gh-pages

# files stay since they're not tracked by git
mv www/index.html www/syscall.json .
rm -rf www

git add -A .
git commit -m "sync with Linux $kernel_version"
git tag -a $kernel_version -m "auto tagging $kernel_version"
git push origin gh-pages --tags
git checkout master
