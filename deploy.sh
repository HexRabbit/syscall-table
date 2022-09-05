#!/bin/bash

git fetch
git checkout gh-pages

rm -rf *
echo 'syscall.hexrabbit.io' > CNAME

git checkout master www
mv www/* .
rm -rf www

git add -A .
git commit -m "static content update at `git rev-parse --short HEAD`"
git push origin gh-pages
git checkout master
