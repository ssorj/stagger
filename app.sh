#!/bin/bash

make install

export PATH=~/.local/bin:$PATH

exec stagger
