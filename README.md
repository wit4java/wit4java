# Wit4Java: A Violation-Witness Validator for Java Verifiers

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/7aa7c9bff3c5458d9af4b055f97af8ce)](https://www.codacy.com/gh/wit4java/wit4java/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=wit4java/wit4java&amp;utm_campaign=Badge_Grade)

### Description

Modern verification tools report a violation witness amidst verification if a bug is encountered. To check the validity of the counterexample wit4java can be used for Java-based verifiers. 

The tool employs *execution-based validation* to assert the violation of a witness. This process involves extracting information on the assumptions of the verifier from the [standardised exchange format for violation witnesses](https://github.com/sosy-lab/sv-witnesses/blob/main/README-GraphML.md) and building a test harness to provide a concrete execution of the program. The tool then executes the test harness on the code under verification and can either confirm or reject the violation witness if the relevant assertion is reached.

### Literature

- [Wit4Java: A violation-witness validator for Java verifiers (competition contribution)](https://doi.org/10.1007/978-3-030-99527-0_36) by Wu, T., Schrammel, P., & Cordeiro, L. C. International Conference on Tools and Algorithms for the Construction and Analysis of Systems. Springer, Cham, 2022. Springer [doi.org/10.1007/978-3-030-99527-0_36](https://doi.org/10.1007/978-3-030-99527-0_36)
### Usage
```
usage: wit4java [-h] [--packages [PACKAGE_PATHS [PACKAGE_PATHS ...]]]
                --witness WITNESS_FILE [--version]
                benchmark

Validate a given Java program with a witness conforming to the appropriate SV-COMP exchange format.

positional arguments:
  benchmark             Path to the benchmark directory

optional arguments:
  -h, --help            show this help message and exit
  --packages [PACKAGE_PATHS [PACKAGE_PATHS ...]]
                        Path to the packages used by the benchmark
  --witness WITNESS_FILE
                        Path to the witness file. Must conform to the exchange
                        format
  --version             show program's version number and exit
```
### Authors
Tong Wu (University of Manchester, United Kingdom) wutonguom@gmail.com

Lucas Cordeiro (University of Manchester, United Kingdom) lucas.cordeiro@manchester.ac.uk

Peter Schrammel (University of Sussex, United Kingdom) P.Schrammel@sussex.ac.uk

### Maintainers 

Joss Moffatt (University of Manchester, United Kingdom) josshmoffatt@gmail.com

### Links
- [Wit4java Version History](CHANGELOG.md)
- [Benchexec Tool Info Module](https://github.com/sosy-lab/benchexec/blob/main/benchexec/tools/wit4java.py)
