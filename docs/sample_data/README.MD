This folder has sample data from https://download.bls.gov/pub/time.series/ to inform planning.

`*.head` files are the first lines of a full data partition. `pc.data.20.ComputerProduct.sample` is the header and first 14 rows followed by the last 20 rows of the partition (so it shows both early one-decimal values and recent preliminary `P` rows); the join between the two parts is not contiguous.
