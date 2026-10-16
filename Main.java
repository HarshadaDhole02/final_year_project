import java.io.*;
import java.util.*;

public class Main {

    public static void main(String[] args) throws Exception {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        StringBuilder output = new StringBuilder();

        int T = Integer.parseInt(br.readLine().trim());

        while (T-- > 0) {
            int n = Integer.parseInt(br.readLine().trim());

            int[] arr = new int[n];
            int[] ans = new int[n];

            StringTokenizer st = new StringTokenizer(br.readLine());

            for (int i = 0; i < n; i++) {
                arr[i] = Integer.parseInt(st.nextToken());
            }

            // Stack stores elements for which we are finding
            // the next smaller element.
            Deque<Integer> stack = new ArrayDeque<>();

            for (int i = n - 1; i >= 0; i--) {

                // Remove elements that are not strictly smaller
                while (!stack.isEmpty() && stack.peek() >= arr[i]) {
                    stack.pop();
                }

                // If stack is empty, no smaller element exists
                if (stack.isEmpty()) {
                    ans[i] = -1;
                } else {
                    ans[i] = stack.peek();
                }

                stack.push(arr[i]);
            }

            for (int i = 0; i < n; i++) {
                if (i > 0) {
                    output.append(" ");
                }
                output.append(ans[i]);
            }

            output.append("\n");
        }

        System.out.print(output);
    }
}