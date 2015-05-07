#Checksumprovider

_Checksumprovider_ is simple Python script for calculating file hashes. It can work in two modes:

1. Calculating checksums,
2. Verifying checksums.

#Requirements

* Python 3
* After checkout: `pip install -r requirements.txt`

# Usage

Calculate checksum for file `checksum.py` and print it on console:
```
checksum.py --file checksum.py
```

Calculate checksum for file `checksum.py`, print it on console and save to `checksum.py.sha1`:
```
checksum.py --file checksum.py --output checksum.py.sha1
```

Calculate checksums for each file in directory `test` and save to `test.sha1`:

```
checksum.py --directory test --output test.sha1
```


