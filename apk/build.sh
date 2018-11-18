#!/bin/sh
p4a apk --private ../ --package org.irc.irc1 --name irc1 --version 0.1 --orientation portrait --icon ../data/icon.png --permission INTERNET --presplash ../data/presplash.png --window --blacklist blacklist.txt --requirements kivy,jnius,android
