#!/bin/bash
# copies and unzips packaged python layers to your local python path

echo "Hello, these are the detected python system paths:"
echo -e "import sys\nfor path in sys.path:\n  if 'site-packages' in path: print(path)" | python

echo "Where do you want to install your lambda layers for local access? (copy-paste the full path here):"
read installpath
cp -rf ../lambda/helpers/* $installpath

echo "Installed custom layers in "$installpath"!"
echo "Will now install third-party packages..."
pip install boto3 pyyaml crhelper bcrypt
