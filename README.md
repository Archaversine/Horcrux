# Horcrux Encryption

Protect your files by splitting their souls.

## Horcruxes

A horcrux is a file that contains a fraction of the information of another file,
similar to how horcruxes in Harry Potter contain split pieces of a soul to
protect it. It is not possible to tell if a file is a horcrux of another file or
not, and the horcrux itself does not contain any information about other
horcruxes to the same file or any information about even if either of those
things exist. The information that each horcrux holds is essentially random
bytes, so none of the data from the original file can be recovered. Even 99 out
of 100 horcruxes combined will not yield any information about the original
file; all horcruxes must be present to merge to the original file. The data a
horcrux holds is only meaningful if all the other pieces are present.

## Splitting Algorithm (Encryption)

At it's core, encryption and decryption calculations revolve around the use of
XOR. When a file is split, securely random bytes are generated in a way such
that when they are combined together via the use of XOR it will yield the
decrypted file. 

For example, assume the file `passwords.txt` is going to be split into `1.hcx`,
`2.hcx`, and `3.hcx`. For each byte in `passwords.txt`, two random bytes are
generated and placed into `1.hcx` and `2.hcx` respectively. The byte for `3.hcx`
is calculated by XORing all random bytes with the original byte

In pseudocode:

```
third_byte = original_byte XOR first_rand_byte XOR second_rand_byte
```

## Merging Algorithm (Decryption)

To merge files together, the process is even easier. To recover the original
file from it's 'horcruxes', the program goes through every byte in each horcrux
and XORs them all together. For example, to recover the file `passwords.txt`
from its horcruxes `1.hcx`, `2.hcx`, and `3.hcx`, the first byte of
`passwords.txt` would be equal to the first byte of `1.hcx` XOR `2.hcx` XOR
`3.hcx`.

In pseudocode:

```
original_byte = byte_from_1hcx XOR byte_from_2hcx XOR byte_from_3hcx
```

## Comparison Algorithm

Since horcruxes are generated with purely random numbers, there is an
astronomically low chance that a significantly large portion of the original
data will be in one of the split components. To put into perspective how low of
a chance this is of occuring, a file with three bytes has a 1 in 16,777,216
chance of all three bytes not being encrypted and a 1 in 65,281 chance of two of
the bytes not being encrypted. As more bytes are added to the file the chances
of data being leaked from the original exponentially decreases. In order to
verify that there isn't a significant amount of information leaked from the
original, a comparison algorithm was added. This checks multiple files, and
returns a percentage of the similarity between the files.

In pseudocode, the percentage of the similarity is calculated with the following:

```
percentage = number_of_identical_bytes / total_number_of_bytes
```


## Splitting with Key Horcruxes (Advanced Encryption)

To create a horcrux that is compatible with multiple files, A 'key' with the
same size as the largest input file is generated. After this key is generated,
each input file is individually merged with the key. If a file is shorter than
the key, then the extra bytes of the key are not used for merging (This is the
default behavior for merging in general). The output files will each be
horcruxes that can be merged with the key to recover it's original file. Of
course, both the key and the horcruxes and be split or merged even more.

## Command Line Usage

```
usage: horcrux [-h] [-k KEY] [-o [OUTPUT ...]] [-c CHUNK_SIZE]
               {split,merge,key,compare} [inputs ...]

Protect your files by splitting their souls.

positional arguments:
  {split,merge,key}     Action to perform.
  inputs

options:
  -h, --help            show this help message and exit
  -k KEY, --key KEY     Filename of key horcrux.
  -o [OUTPUT ...], --output [OUTPUT ...]
                        Names of output files.
  -c CHUNK_SIZE, --chunk-size CHUNK_SIZE
                        How many bytes to load into RAM per file (Default:
                        1MB)
```


Note that on the above usage section, `[inputs ...]` is listed after all the
command flags. This is due to how the `argparse` library prints usage. When
using the horcrux command, inputs must be specified *before* flags.

On windows, the program can be run with the `python` or `python3` command. This
can also be done on linux, or `horcrux.py` can be placed in a folder in the PATH
variable with execution permissions and used directly as a command.

## Splitting Files (Encryption)

To split a file into any number of parts, use the following syntax:

```
horcrux split <fileToSplit> <part1> <part2> [<part3> ...]
```

The file will be split into however many output files are specified. So if five
filenames are specified, then it will be split into five parts. (NOTE: At least
two output files are needed to split).

Note that for merging, *ALL* parts of a file are required for merging. If a file
is split into 100 horcruxes and one horcrux is missing, the original data
*CANNOT* be recovered.

The name or file extension of the horcruxes (output files) does not matter, they
will appear as corrupted files either way.

## Merging Horcruxes (Decryption)

To merge horcruxes into their original file, use the following syntax:

```
horcrux merge <part1> <part2> [<part3> ...] <outputFile>
```

The horcruxes will be merged into a single file whether or not they will created
a decrypted file. If the horcruxes vary in size, the merging algorithm will use
the size of the smallest horcrux. Since there's no way to confirm if a file is a
horcrux, the merge algorithm can be applied to any list of files.

## Key Horcruxes

Different Files can share horcruxes that hold the information to both of them.
For example, the horcrux `a.hcx` merged with the horcrux `k.hcx` may yield an
decrypted file, and the completely different horcrux `b.hcx` merged with the
same horcrux `k.hcx` may yield a completely different decrypted file.

This can be done by generated a special horcrux that is used in the calculations
for splitting multiple differnet files to get their other halves. While this
horcrux is able to decrypt multiple things, it still is fundamentally the same
and indistinguishable from a regular horcrux.

To split multiple files at once with a shared horcrux, use the following syntax:

```
horcrux key <file1> [<file2> ...] --key <keyFileName>
```

If you want to specify specific output names, use the following:

```
horcrux key <file1> [<file2> ...] --output [output1 output2 ...] --key <keyFileName>
```

### Example

To Encrypt the files `a.txt`, `b.txt`, and `c.txt` with a key horcrux `key.hcx`:

```
horcrux key a.txt b.txt c.txt --key key.hcx
```

This will generate the horcruxes: `a.txt.hcx`, `b.txt.hcx`, and `c.txt.hcx`.

The file extension of the horcruxes does not matter. To use specific outupts
instead of auto generated ones the above example would be changed into:

```
horcrux key a.txt b.txt c.txt --key key.hcx --output Ahorcrux.bin Bhorcrux.bin
```

Note that in the above example an output name for `c.txt` is not specified, so
the name `c.txt.hcx` will be used.

## Comparing Files

To view the similarity between two files, use the following syntax:

```
horcrux compare <fileToCompare> <file1> [<file2> ...]
```

The above command will show the percent similarity between `fileToCompare` and
all the other files. Note that all other files won't be compared with each
other, only `fileToCompare` and the other files.
