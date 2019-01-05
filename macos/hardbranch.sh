#!/bin/bash

REPO=$1
BRANCH=$2
ROOT=~/git/

if [[ "${BRANCH}" == "" ]]; then
  echo "Usage: $0 REPO BRANCH"
  exit 1
fi

if [[ ! -d ${ROOT} ]]; then
  echo "Could not find root dir: ${ROOT}. Something looks wrong ..."
  exit 1
fi

if [[ -d "${ROOT}/${BRANCH}" ]]; then
  echo "There is already a branch named: ${BRANCH}"
  exit 1
fi

echo "Under construction ..."
exit 1

echo "Cloning ${REPO} into its own directory and creating branch: ${BRANCH}"

#
# Clone the repo and set upstream.
#
cd ${ROOT}
mkdir ${BRANCH}
cd ${BRANCH}/
git clone https://$( cat ~/Documents/token.git )@github.com/erikbryant/${REPO}.git
cd ${REPO}/
git remote add upstream https://$( cat ~/Documents/token.git )@github.com/XXXX/${REPO}.git

#
# Make sure my fork is up-to-date with the original repo.
#
DEVBRANCH=$( git branch | awk '{ print $2 }' )
git pull --rebase upstream ${DEVBRANCH}
git push --set-upstream origin ${DEVBRANCH}

#
# Create the branch we will be working in.
#
git checkout -b ${BRANCH}
git push --set-upstream origin ${BRANCH}
