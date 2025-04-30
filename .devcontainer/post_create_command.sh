USERHOME=/home/vscode
USERBIN=${USERHOME}/bin
bash get-pants.sh -d ${USERBIN}
chown -R vscode ${USERBIN}

git config --global --add safe.directory $1
