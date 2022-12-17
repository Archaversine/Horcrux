#!/usr/bin/python3

import os
import sys
import secrets
import argparse

CHUNK_SIZE = 1024 * 1024  # 1 MB

def error(message: str) -> None:
    print(f"<> Error: {message}")
    sys.exit(1)

def log(message: str) -> None:
    print(f"<> {message}")

def split_file(input_filename: str, outputs: list) -> None:

    input_file = open(input_filename, "rb")
    target_files = [open(x, "wb") for x in outputs]

    byte = input_file.read(1)

    while byte:
        random_bytes = [secrets.randbits(8) for _ in range(len(target_files) - 1)]

        for i in range(len(target_files) - 1):
            target_files[i].write(bytes([random_bytes[i]]))

        result_byte = byte

        for random_byte in random_bytes:
            result_byte = bytes([random_byte ^ ord(result_byte)])

        target_files[-1].write(result_byte)

        byte = input_file.read(1)

    input_file.close()

    for target_file in target_files:
        target_file.close()

def merge_files(inputs: list, output_filename: str) -> None:

    output_file = open(output_filename, "wb")
    input_files = [open(x, "rb") for x in inputs]

    chunks = [f.read(CHUNK_SIZE) for f in input_files]

    while all(chunks):
        decrypted_chunk = bytearray(len(chunks[0]))

        for i in range(len(chunks[0])):
            decrypted_chunk[i] = 0

            for j in range(len(chunks)):
                decrypted_chunk[i] ^= chunks[j][i]

        output_file.write(decrypted_chunk)

        chunks = [f.read(CHUNK_SIZE) for f in input_files]

    output_file.close()

    for input_file in input_files:
        input_file.close()

def keysplit(keyname: str, inputs: list, outputs: list) -> None:

    if len(inputs) != len(outputs):
        error("Number of inputs must equal number of outputs.")

    key_file = open(keyname, "wb")
    input_files = [open(x, "rb") for x in inputs]
    output_files = [open(x, "wb") for x in outputs]

    input_bytes = [input_file.read(1) for input_file in input_files]

    while any(input_bytes):

        key_byte = secrets.randbits(8)
        key_file.write(bytes([key_byte]))

        for i, input_byte in enumerate(input_bytes):
            if not input_byte:
                continue

            output_files[i].write(bytes([key_byte ^ ord(input_byte)]))

        input_bytes = [input_file.read(1) for input_file in input_files]

    key_file.close()

    for input_file in input_files:
        input_file.close()

    for output_file in output_files:
        output_file.close()

def keyadd(keyname: str, inputs: list, outputs: list) -> None:

    if len(inputs) != len(outputs):
        error("Number of inputs must equal number of outputs")

    key_file = open(keyname, "rb+")
    input_files = [open(x, "rb") for x in inputs]
    output_files = [open(x, "wb") for x in outputs]

    input_bytes = [input_file.read(1) for input_file in input_files]

    while any(input_bytes):
        key_byte = key_file.read(1)

        if not key_byte:
            key_byte = bytes([secrets.randbits(8)])
            key_file.write(key_byte)
            # NOTE: May need to add key_file.read(1) to prevent reading (I think it is fine without this)

        for i, input_byte in enumerate(input_bytes):
            if not input_byte:
                continue

            output_files[i].write(bytes([ord(key_byte) ^ ord(input_byte)]))

        input_bytes = [input_file.read(1) for input_file in input_files]

    key_file.close()

    for input_file in input_files:
        input_file.close()

    for output_file in output_files:
        output_file.close()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Protect your files by splitting their souls.')
    parser.add_argument("mode", type=str, help="Action to perform.", choices=("split", "merge", "keysplit", "keyadd"))
    parser.add_argument("-k", "--key", type=str, help="Filename of key for keysplitting.")
    parser.add_argument("-i", "--input", type=str, help="Names of input files.", nargs='*')
    parser.add_argument("-o", "--output", type=str, help="Names of output files.", nargs='*')

    args = parser.parse_args()

    # Ensure both inputs and outputs are specified
    if args.input is None or args.output is None:
        error("Must specify both inputs and outputs.")

    # Ensure all input files are valid paths
    for input_file in args.input:
        if not os.path.isfile(input_file):
            error(f"File {input_file} does not exist.")

    # Ensure only one input file when splitting
    if (args.mode == "split") and len(args.input) != 1:
        error("Specify only 1 input file when splitting.")

    # Ensure only one output file when merging
    if (args.mode == "merge") and len(args.output) != 1:
        error("Specify only 1 output file when merging.")

    # Only split/merge if enough files to do so
    if (args.mode == "split" and len(args.output) < 2) or (args.mode == "merge" and len(args.input) < 2):
        log("Nothing to do.")
        sys.exit(0)

    # Ensure keysplitting has key argument
    if (args.mode == "keysplit" and args.key is None) or (args.mode == "keyadd" and args.key is None):
        error("No keyfile given.")

    if args.mode == "split":
        split_file(args.input[0], args.output)
    elif args.mode == "merge":
        merge_files(args.input, args.output[0])
    elif args.mode == "keysplit":
        keysplit(args.key, args.input, args.output)
    elif args.mode == "keyadd":
        keyadd(args.key, args.input, args.output)
