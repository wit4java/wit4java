package org.sosy_lab.sv_benchmarks;

import java.util.LinkedList;
import java.util.Queue;

public final class Verifier {

  static String[] assumptionList = {};
  public static Queue<String> assumptions = new LinkedList<String>();
  static {
    for(String assumption: assumptionList) {
      assumptions.add(assumption);
    }
  }

  public static void assume(boolean condition) {
    if (!condition) {
      Runtime.getRuntime().halt(1);
    }
  }

  public static boolean nondetBoolean() {
    String assumption = assumptions.remove();
    return Boolean.parseBoolean(assumption);
  }

  public static byte nondetByte() {
    String assumption = assumptions.remove();
    return (byte) Integer.parseInt(assumption);
  }

  public static char nondetChar() {
    String assumption = assumptions.remove();
    return (char) Integer.parseInt(assumption);
  }

  public static short nondetShort() {
    String assumption = assumptions.remove();
    return Short.parseShort(assumption);
  }

  public static int nondetInt() {
    String assumption = assumptions.remove();
    return Integer.parseInt(assumption);
  }

  public static long nondetLong() {
    String assumption = assumptions.remove();
    return Long.parseLong(assumption);
  }

  public static float nondetFloat() {
    String assumption = assumptions.remove();
    return Float.parseFloat(assumption);
  }

  public static double nondetDouble() {
    String assumption = assumptions.remove();
    return Double.parseDouble(assumption);
  }

  public static String nondetString() {
    String assumption = assumptions.remove();
    return assumption;
  }
}