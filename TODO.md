- add tests for false positive and false negative (expect high false negative
probability for guided bloom)

- try alternative scheme:
  + if hash1 -> move right
  + elif hash2 -> check self (starting w/ hash4)
  + elif hash3 -> move left
