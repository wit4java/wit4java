import org.mockito.*;
import org.mockito.stubbing.OngoingStubbing;
import org.sosy_lab.sv_benchmarks.Verifier;

public class Test {
  public static void main(String[] args) {
    try {
      Main.main(new String[0]);
      System.out.println("OK ");
    } catch (Exception e) {
      System.out.println(e);
    }
  }
}