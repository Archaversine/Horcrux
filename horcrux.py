#!/usr/bin/python3

import os
import sys
import argparse

def error(message: str) -> None:
    print(f"<> Error: {message}")
    sys.exit(1)

def log(message: str) -> None:
    print(f"<> {message}")

def split_file(input_filename: str, outputs: list, chunk_size: int) -> None:

    input_file = open(input_filename, "rb")
    output_files = [open(x, "wb") for x in outputs]

    input_chunk = input_file.read(chunk_size)

    while input_chunk:
        random_chunks = [os.urandom(len(input_chunk)) for _ in range(len(output_files) - 1)]

        for i in range(len(output_files) - 1):
            output_files[i].write(random_chunks[i])

        xor_chunk = bytearray(input_chunk)

        for i in range(len(xor_chunk)):
            for chunk in random_chunks:
                xor_chunk[i] ^= chunk[i]

        output_files[-1].write(xor_chunk)

        input_chunk = input_file.read(chunk_size)

    input_file.close()

def merge_files(inputs: list, output_filename: str, chunk_size: int) -> None:

    output_file = open(output_filename, "wb")
    input_files = [open(x, "rb") for x in inputs]

    chunks = [f.read(chunk_size) for f in input_files]

    while all(chunks):
        decrypted_chunk = bytearray(min([len(chunk) for chunk in chunks]))

        for i in range(len(decrypted_chunk)):
            for chunk in chunks:
                decrypted_chunk[i] ^= chunk[i]

        output_file.write(decrypted_chunk)

        chunks = [f.read(chunk_size) for f in input_files]

    output_file.close()

    for input_file in input_files:
        input_file.close()

def keysplit(keyname: str, inputs: list, outputs: list, chunk_size: int) -> None:

    if len(inputs) != len(outputs):
        error("Number of inputs must equal number of outupts.")

    key_file = open(keyname, "wb")
    input_files = [open(x, "rb") for x in inputs]
    output_files = [open(x, "wb") for x in outputs]

    input_chunks = [input_file.read(chunk_size) for input_file in input_files]

    while any(input_chunks):

        key_chunk = os.urandom(chunk_size)
        key_file.write(key_chunk)

        for i in range(len(input_chunks)):
            if not input_chunks[i]:
                continue

            xor_chunk = bytearray(input_chunks[i])

            for j in range(len(xor_chunk)):
                xor_chunk[j] ^= key_chunk[j]

            output_files[i].write(xor_chunk)

        input_chunks = [input_file.read(chunk_size) for input_file in input_files]

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
            key_byte = os.urandom(1)
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
    parser.add_argument("-c", "--chunk-size", type=int, help="How many bytes to load into RAM per file (Default: 1MB)", default=1024 * 1024)

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
        split_file(args.input[0], args.output, args.chunk_size)
    elif args.mode == "merge":
        merge_files(args.input, args.output[0], args.chunk_size)
    elif args.mode == "keysplit":
        keysplit(args.key, args.input, args.output, args.chunk_size)
    elif args.mode == "keyadd":
        keyadd(args.key, args.input, args.output)
