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

def horcrux_key(keyname: str, inputs: list, outputs: list, chunk_size: int) -> None:

    if len(inputs) != len(outputs):
        error("Number of inputs must equal number of outputs.")

    key_file = open(keyname, "ab+")
    key_file.seek(0)

    input_files = [open(x, "rb") for x in inputs]
    output_files = [open(x, "wb") for x in outputs]

    input_chunks = [input_file.read(chunk_size) for input_file in input_files]

    while any(input_chunks):

        key_chunk = bytearray(key_file.read(chunk_size))
        max_chunk_length = max([len(input_chunk) for input_chunk in input_chunks])

        if len(key_chunk) < max_chunk_length:
            random_chunk = os.urandom(max_chunk_length - len(key_chunk))
            key_file.write(random_chunk)
            key_chunk.extend(random_chunk)

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

def compare_files(input_filename: str, target_filenames: list, chunk_size: int) -> None:

    input_file = open(input_filename, "rb")
    target_files = [open(x, "rb") for x in target_filenames]

    # Store the number of identical bytes for each target_file
    same_byte_count = [0] * len(target_files)
    total_byte_count = [0] * len(target_files)
    target_chunks = [target_file.read(chunk_size) for target_file in target_files]

    while any(target_chunks):

        input_chunk = input_file.read(chunk_size)

        for i in range(len(target_chunks)):
            if not target_chunks[i]:
                continue

            total_byte_count[i] += len(target_chunks[i])

            for j in range(min(len(input_chunk), len(target_chunks[i]))):
                same_byte_count[i] += 1 if target_chunks[i][j] == input_chunk[j] else 0

        target_chunks = [target_file.read(chunk_size) for target_file in target_files]

    input_file.close()

    for target_file in target_files:
        target_file.close()

    percentages = [same_byte_count[i] / total_byte_count[i] for i in range(len(target_files))]

    for filename, percentage in zip(target_filenames, percentages):
        print(f"{filename:30}: {percentage:.2%} Similarity")

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Protect your files by splitting their souls.')
    parser.add_argument("mode", type=str, help="Action to perform.", choices=("split", "merge", "key", "compare"))
    parser.add_argument("inputs", type=str, nargs="*")
    parser.add_argument("-k", "--key", type=str, help="Filename of key horcrux.")
    parser.add_argument("-o", "--output", type=str, help="Names of output files.", nargs='*', default=[])
    parser.add_argument("-c", "--chunk-size", type=int, help="How many bytes to load into RAM per file (Default: 1MB)", default=1024 * 1024)

    args = parser.parse_args()

    if args.mode == "split":
        split_file(args.inputs[0], args.inputs[1:] + args.output, args.chunk_size)

    elif args.mode == "merge":
        input_filenames = args.inputs[:-1] if not args.output else args.inputs
        output_filenames = args.output or args.inputs[-1:]
        merge_files(input_filenames, output_filenames[0], args.chunk_size)
    elif args.mode == "key":

        # Auto generate output filenames if not specified
        specified_outputs = len(args.output)
        unspecified_outputs = len(args.inputs) - specified_outputs
        args.output.extend([''] * unspecified_outputs)

        for i in range(specified_outputs, specified_outputs + unspecified_outputs):
            args.output[i] = args.inputs[i] + ".hcx"

        horcrux_key(args.key, args.inputs, args.output, args.chunk_size)
    elif args.mode == "compare":
        compare_files(args.inputs[0], args.inputs[1:] + args.output, args.chunk_size)

    #if args.mode == "split":
    #    split_file(args.inputs[0], args.output, args.chunk_size)
    #elif args.mode == "merge":
    #    merge_files(args.input, args.output[0], args.chunk_size)
    #elif args.mode == "key":
    #    horcrux_key(args.key, args.input, args.output, args.chunk_size)
