#!/bin/bash
# copies and unzips packaged python layers to your local python path
# Usage: Argument ($1) is optional. It will default to "python" as the pythong command,
#     which is the correct Python 3.x command for most modern systems.
#     If "python" in your setup still means Python 2.7, then you can supply the correct
#     Python 3.x command by passing it as the argument. 
#     For example, if the correct command is "python3", then trigger this script using:
#           ./install-layers-to-local.sh python3

if [[ $1 == '' ]]
then
    pycommand="python"
else
    pycommand=$1
fi

echo "Will install third-party packages..."
pip install boto3 pyyaml crhelper requests

echo "Will now proceed to install lambda layers for local access."
echo "These are the detected python system paths:"
echo -e "import sys\nfor path in sys.path:\n  if 'packages' in path: print(path)" | $pycommand

echo "Where do you want to install your lambda layers for local access? (copy-paste the full path here):"
read -r installpath
cp -rf ../lambda/helpers/* "$installpath"

echo "Installed custom layers in "$installpath"!"
