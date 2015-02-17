#!/bin/bash

rm -rf cpp
rm -rf java
rm -rf python

mkdir cpp
mkdir java
mkdir python

protoc --proto_path=protobuf --cpp_out=cpp --java_out=java --python_out=python protobuf/*.proto

