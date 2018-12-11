#!/bin/bash

make PREFIX=/usr
make install

exec stagger
