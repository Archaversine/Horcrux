#!/usr/bin/python3

import os
import sys
import secrets
import argparse
import numpy as np

def error(message: str) -> None:
    print(f"<> Error: {message}")
    sys.exit(1)

def log(message: str) -> None:
    print(f"<> {message}")

def parse_byte_count(value: str) -> int:
    units = {'K': 1024, 'M': 1024 * 1024, 'G': 1024 * 1024 * 1024}

    if value[-1] in units:
        return int(value[:-1]) * units.get(value[-1], 1)

    return int(value)

def split_file(input_filename: str, outputs: list, chunk_size: int, noise: int) -> None:
    input_file = open(input_filename, "rb")
    output_files = [open(x, "wb") for x in outputs]

    input_chunk = input_file.read(chunk_size)

    while input_chunk:
        random_chunks = [os.urandom(len(input_chunk)) for _ in range(len(output_files) - 1)]

        for i in range(len(output_files) - 1):
            output_files[i].write(random_chunks[i])

        xor_chunk = np.frombuffer(input_chunk, dtype=np.uint8)

        for chunk in [np.frombuffer(random_chunk, dtype=np.uint8) for random_chunk in random_chunks]:
            xor_chunk = xor_chunk ^ chunk

        output_files[-1].write(xor_chunk.tobytes())

        input_chunk = input_file.read(chunk_size)

    input_file.close()
    rand_index = int.from_bytes(os.urandom(1), byteorder="big") % len(output_files)

    for i, output_file in enumerate(output_files):
        if i != rand_index:
            output_file.write(os.urandom(secrets.randbelow(noise)))

        output_file.close()

def merge_files(inputs: list, output_filename: str, chunk_size: int) -> None:
    output_file = open(output_filename, "wb")
    input_files = [open(x, "rb") for x in inputs]

    chunks = [f.read(chunk_size) for f in input_files]

    while all(chunks):
        min_len = min([len(chunk) for chunk in chunks])
        decrypted_chunk = np.zeros(min_len, dtype=np.uint8)

        for chunk in [np.frombuffer(c, dtype=np.uint8) for c in chunks]:
            decrypted_chunk = decrypted_chunk ^ chunk[:min_len]

        output_file.write(decrypted_chunk.tobytes())
        chunks = [f.read(chunk_size) for f in input_files]

    output_file.close()

    for input_file in input_files:
        input_file.close()

def locket_transform(locket_name: str, inputs: list, outputs: list, chunk_size: int) -> None:
    if len(inputs) != len(outputs):
        error("Number of inputs must equal number of outputs.")

    locket_file = open(locket_name, "ab+")
    locket_file.seek(0)

    input_files = [open(x, "rb") for x in inputs]
    output_files = [open(x, "wb") for x in outputs]

    input_chunks = [input_file.read(chunk_size) for input_file in input_files]

    while any(input_chunks):
        locket_chunk = bytearray(locket_file.read(chunk_size))
        max_chunk_length = max([len(input_chunk) for input_chunk in input_chunks])

        if len(locket_chunk) < max_chunk_length:
            random_chunk = os.urandom(max_chunk_length - len(locket_chunk))
            locket_file.write(random_chunk)
            locket_chunk.extend(random_chunk)

        for i in range(len(input_chunks)):
            if not input_chunks[i]:
                continue

            xor_chunk = np.frombuffer(input_chunks[i], dtype=np.uint8)
            xor_chunk = xor_chunk ^ np.frombuffer(locket_chunk, dtype=np.uint8)

            output_files[i].write(xor_chunk.tobytes())

        input_chunks = [input_file.read(chunk_size) for input_file in input_files]

    locket_file.close()

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
        input_chunk = np.frombuffer(input_file.read(chunk_size), dtype=np.uint8)

        for i in range(len(target_chunks)):
            if not target_chunks[i]:
                continue

            total_byte_count[i] += len(target_chunks[i])

            target_chunk = np.frombuffer(target_chunks[i], dtype=np.uint8)
            min_len = min(len(target_chunk), len(input_chunk))
            same_byte_count[i] += np.count_nonzero(target_chunk[:min_len] == input_chunk[:min_len])

        target_chunks = [target_file.read(chunk_size) for target_file in target_files]

    input_file.close()

    for target_file in target_files:
        target_file.close()

    percentages = [same_byte_count[i] / total_byte_count[i] for i in range(len(target_files))]

    for filename, percentage in zip(target_filenames, percentages):
        print(f"{filename:30}: {percentage:.5%} Similarity")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Protect your files by splitting their souls.')
    parser.add_argument("mode", type=str, help="Action to perform.", choices=("split", "merge", "locket", "compare"))
    parser.add_argument("inputs", type=str, nargs="*")
    parser.add_argument("-L", "--locket", type=str, help="Filename of locket horcrux.")
    parser.add_argument("-o", "--output", type=str, help="Names of output files.", nargs='*', default=[])
    parser.add_argument("-c", "--chunk-size", type=str, help="1M Default. How many bytes to load into RAM per file. Use K, M, G for more units or no unit for bytes.", default='1M')
    parser.add_argument("-p", "--parts", type=int, help="How many parts to split into.")
    parser.add_argument("-n", "--noise", type=str, help="Default: 0. Max amount of extra bytes to generate for horcruxes after splitting. Use K, M, G for more units or no unit for bytes.", default='0')

    args = parser.parse_args()
    chunk_size = parse_byte_count(args.chunk_size)

    if args.mode == "split":
        output_filenames = args.inputs[1:] + args.output
        specified_outputs = len(output_filenames)
        unspecified_outputs = args.parts - specified_outputs if args.parts else 0
        output_filenames.extend([''] * unspecified_outputs)

        for i in range(specified_outputs, specified_outputs + unspecified_outputs):
            output_filenames[i] = f"{args.inputs[0]}.{i + 1}-of-{len(output_filenames)}.hcx"

        split_file(args.inputs[0], output_filenames, chunk_size, parse_byte_count(args.noise))
    elif args.mode == "merge":
        input_filenames = args.inputs[:-1] if not args.output else args.inputs
        output_filenames = args.output or args.inputs[-1:]
        merge_files(input_filenames, output_filenames[0], chunk_size)
    elif args.mode == "locket":
        specified_outputs = len(args.output)
        unspecified_outputs = len(args.inputs) - specified_outputs
        args.output.extend([''] * unspecified_outputs)

        for i in range(specified_outputs, specified_outputs + unspecified_outputs):
            args.output[i] = args.inputs[i] + ".hcx"

        locket_transform(args.locket, args.inputs, args.output, chunk_size)
    elif args.mode == "compare":
        compare_files(args.inputs[0], args.inputs[1:] + args.output, chunk_size)
