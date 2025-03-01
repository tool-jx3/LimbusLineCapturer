#!/usr/bin/env bash

help_message() {
echo "Usage: $0 [token1 [token2 [...]]]"
exit 0
}

while getopts "h?:" opt; do
    case "$opt" in
    h|\?)
        help_message
        ;;
    esac
done


if [ "$#" -eq 0 ]; then
  help_message
fi

cd "$(dirname "$0")"

if [ -f ../TOKEN ]; then
  rm ../TOKEN
fi

for ((i=0;i<=$#;i++));
  do
    if [[ "$i" -eq '0' ]]; then
      continue
    fi
    printf "${!i}\n" >> ../TOKEN ;
done

echo "Token writing completed"
