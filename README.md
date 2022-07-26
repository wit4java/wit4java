# Wit4Java: A Violation-Witness Validator for Java Verifiers

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/7aa7c9bff3c5458d9af4b055f97af8ce)](https://www.codacy.com/gh/wit4java/wit4java/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=wit4java/wit4java&amp;utm_campaign=Badge_Grade)

### Description

Modern verification tools report a violation witness amidst verification if a bug is encountered. To check the validity of the counterexample wit4java can be used for Java-based verifiers. 

The tool employs *execution-based validation* to assert the violation of a witness. This process involves extracting information on the assumptions of the verifier from the [standardised exchange format for violation witnesses](https://github.com/sosy-lab/sv-witnesses/blob/main/README-GraphML.md) and building a test harness to provide a concrete execution of the program. The tool then executes the test harness on the code under verification and can either confirm or reject the violation witness if the relevant assertion is reached.

### Usage
```
./wit4java.py –witness <path-to-sv-witnesses>/witness.graphml <path-to-sv-benchmarks>/java/jbmc-regression/someprogram
```

### Benchmark Tool-info module

[wit4java.py](https://github.com/sosy-lab/benchexec/blob/main/benchexec/tools/wit4java.py)

### Authors
Tong Wu (University of Manchester, United Kingdom) wutonguom@gmail.com

Lucas Cordeiro (University of Manchester, United Kingdom) lucas.cordeiro@manchester.ac.uk

Peter Schrammel (University of Sussex, United Kingdom) P.Schrammel@sussex.ac.uk

### Version History
- 1.0
Naive
- 2.0
Apply Mockito framework
