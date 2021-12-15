#!/bin/bash
# copies and unzips packaged python layers to your local python path


echo "Hello, these are the detected python system paths:"
python -c "import sys; print('\n'.join(sys.path))"


echo "Where do you want to install your lambda layers for local access? (full path):"

read installpath

cp -rf ../lambda/helpers/* $installpath

echo "Installed layers in "$installpath"!"
