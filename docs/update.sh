#!/bin/bash
make clean
cd ../../uraniadocs
git clone -b gh-pages --single-branch git@github.com:nachoplus/urania.git html
cd ../urania/docs
make html
make latexpdf
cd ../../uraniadocs/html
cp ../latex/urania.pdf .
pwd
git add .
git commit -a -m "Updated documentation"
git push origin gh-pages
cd ../../urania/docs
