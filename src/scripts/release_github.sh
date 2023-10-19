#!/bin/bash  
  
if [[ ! ${TAG_NAME} =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then  
  echo "invalid version tag."   
  exit 1
fi

# upload to pypi
poetry publish --build -u __token__ -p ${TOKEN}