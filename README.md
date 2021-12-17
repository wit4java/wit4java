# Project Title 

wit4java

### Description

A violation-witness validator for Java. Version 2.0 is recommended. It searches for assumptions to create a unit test case to reproduce the violation property. 

### Dependencies

- Python 3
- Java
- NetworkX
- Mockito 3.4

### How to run
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
