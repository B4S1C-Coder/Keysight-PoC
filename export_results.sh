#!/usr/bin/env bash

shopt -s nullglob
files=(data/*.xlsx)

if ((${#files[@]})); then
	cp -f -- "${files[@]}" "/mnt/c/Users/SAKSHAM MITTAL/Desktop/"
fi
